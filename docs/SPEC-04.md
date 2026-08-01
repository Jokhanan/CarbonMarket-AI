# SPEC-04 — Génération de l'argument de défendabilité par IA

Statut : à implémenter
Créée le 01.08.2026
Prérequis : SPEC-03 (tranche fine — `project_parameters.defendability_argument`,
`project_parameter_alternatives`, `regulatory_value_preferences`)
Bloque : rien explicitement

---

## Objectif

Remplacer le gabarit textuel de `defendability_argument` (SPEC-03 T5, étape
6) par une vraie prose rédigée par IA, qui explique **pourquoi cette valeur
pour ce projet précis** — pays, combustible, réponse à la question posée —
plutôt que de simplement concaténer des champs.

**C'est le seul endroit du système où un modèle de langage apporte une
vraie valeur.** Tout le reste (SPEC-01 à SPEC-03) est délibérément fait de
données et de règles, pas de génération libre — voir CLAUDE.md R1-R3. Cette
spec ne change pas cette philosophie : le modèle ne choisit rien, ne source
rien, n'extrait rien ; il met en prose des faits déjà tranchés et déjà en
base, sous contrainte stricte de ne jamais en sortir.

---

## Constat de départ

Le gabarit actuel (implémenté dans `parameter_resolver.py`,
`resolve_parameter()` étape 6) :

```
{param_key} = {value} {unit}. Source : {section_ref}, page {page_ref}.
Statut : {obligation}. {rationale}
```

Techniquement correct — chaque mot vient d'une donnée sourcée — mais c'est
une concaténation de champs, pas un argument. Un VVB qui lit ça n'a pas
d'explication de pourquoi ce choix est défendable *pour ce projet* : le
gabarit ne mentionne ni le pays, ni le combustible, ni la réponse du
développeur à la question qui a déterminé le choix.

---

## Périmètre

### Dans le périmètre

1. Génération de prose depuis un ensemble fermé de faits structurés déjà
   en base (pas de nouvelle extraction, pas de recherche libre)
2. Garde-fou anti-hallucination : vérification automatique post-génération
3. Stockage versionné (quel modèle a produit quel texte, et quand)
4. Repli sur le gabarit structuré si la génération échoue ou est rejetée —
   jamais de blocage de `resolve_parameter()` à cause de ça

### Hors périmètre

- Le moteur de résolution lui-même (SPEC-03) — cette spec consomme sa
  sortie, ne la remplace pas
- Extraction de nouvelles `regulatory_values`/`regulatory_value_preferences`
  (SPEC-01/SPEC-02) — le modèle ne voit que ce qui existe déjà
- Génération pour d'autres champs que `defendability_argument` (pas de
  rédaction de sections de PDD ici, c'est `ai_writer.py`, déjà existant et
  hors périmètre)

---

## Travaux

### T1 — Le « fact set » : tout ce que le modèle a le droit de voir

Avant l'appel au modèle, construire un objet JSON fermé et exhaustif,
strictement composé de faits déjà en base — rien d'autre :

```json
{
  "param_key": "EF_CO2",
  "chosen": {"value": "355.36", "unit": "tCO2/TJ", "section_ref": "§2 Definitions (WCCF entry)",
             "page_ref": "7", "obligation": "default_permitted",
             "applicability": {"fuel": "charcoal", "wccf_ratio": "6:1", ...}},
  "project_context": {"country": "Ghana", "country_iso": "GHA",
                       "region_classification": "sub_saharan_africa_or_ldc",
                       "question_answered": "wccf_6_1",
                       "question_text": "..."},
  "rejected_alternatives": [
    {"value": "236.91", "section_ref": "...", "reason": "..."},
    {"value": "112", "section_ref": "...", "reason": "..."}
  ]
}
```

**Rien d'autre n'est transmis au modèle** : pas le PDF brut de la
méthodologie, pas une recherche web, pas d'autres lignes de
`regulatory_values` que celles déjà retenues/écartées par le moteur. Le
fact set est la seule réalité que le modèle connaît pour cet appel.

### T2 — Le prompt

Contraintes non négociables dans le prompt système :

- « Tu ne dois utiliser aucun chiffre, aucune référence de section, aucune
  unité qui n'apparaisse pas mot pour mot dans les faits fournis
  ci-dessous. »
- « Si tu ne peux pas construire un argument solide sans introduire une
  information absente des faits fournis, dis-le explicitement plutôt que
  d'improviser. »
- Rédiger 3 à 5 phrases, adressées à un vérificateur (VVB), qui expliquent
  pourquoi la valeur retenue s'applique à ce projet précis — en mobilisant
  le contexte (pays, réponse à la question) et, si utile, en écartant
  explicitement une alternative avec son motif.
- Appel via `carbongpt/core/openai_client.py:call_openai()` (Anthropic,
  voir CLAUDE.md §5) — pas d'appel direct à une API dans ce module.

### T3 — Vérification post-génération (le garde-fou)

`validate_generated_argument(text: str, fact_set: dict) -> bool` :

1. Extraire tous les nombres du texte généré (regex sur motifs numériques,
   décimales incluses).
2. Vérifier que chaque nombre trouvé apparaît quelque part dans le
   fact_set (comme valeur, unité numérique, référence de page...).
3. Extraire toute référence de section (motifs du type `§X`, `§X.Y`,
   `page N`) et vérifier sa présence dans le fact_set.
4. Si un nombre ou une référence n'est pas retrouvé dans le fact_set : rejet.
   L'argument généré **n'est pas stocké**, un événement est loggé
   explicitement (pas de dégradation silencieuse), et `resolve_parameter()`
   retombe sur le gabarit structuré (T4) pour ce paramètre.

**Limite honnête de ce garde-fou, à ne pas survendre** : il prouve
seulement que le texte ne contient aucun chiffre ou référence *absent* du
fact set — pas qu'il interprète correctement les faits qu'il cite. Un texte
qui utilise le bon chiffre au mauvais endroit passerait la vérification.
C'est un filet de sécurité contre l'invention, pas une garantie de
justesse totale.

### T4 — Stockage versionné, avec repli

Extension additive de `project_parameters` (déjà dotée de
`defendability_argument` depuis SPEC-03) :

`defendability_argument_source` (`ai_generated` | `template`),
`defendability_argument_model` (ex. `claude-sonnet-5`, `NULL` si
`template`), `defendability_argument_generated_at` (TIMESTAMP).

Le gabarit structuré (SPEC-03) n'est pas supprimé : c'est le repli
systématique quand la génération IA échoue (erreur API, garde-fou T3
déclenché). `resolve_parameter()` continue à fonctionner sans IA — la
prose est une amélioration, jamais une dépendance dure.

### T5 — Régénération quand les faits changent

Si `project_parameters.value` change (nouvelle résolution, override) ou si
`resolution_engine_version` change, l'argument existant est invalidé et
regénéré au prochain appel plutôt que laissé périmé — un argument qui
décrit une valeur différente de celle actuellement retenue serait pire que
le gabarit.

---

## Tests exigés

- Un fait numérique absent du fact set fait rejeter le texte (garde-fou T3)
- Une référence de section absente du fact set fait rejeter le texte
- Un texte qui ne cite que des faits du fact set est accepté
- Un échec de génération (erreur API) ou un rejet par le garde-fou
  n'empêche pas `resolve_parameter()` de retourner un résultat — repli sur
  le gabarit, `defendability_argument_source = 'template'`
- Deux générations avec le même fact set peuvent produire un texte
  différent (non-déterminisme du modèle), mais toutes deux doivent passer
  la vérification indépendamment
- Un changement de `value` sur un `project_parameters` existant invalide
  l'argument précédemment stocké

---

## Livrables

1. `generate_defendability_argument(fact_set) -> str`, avec appel au
   garde-fou intégré
2. `validate_generated_argument(text, fact_set) -> bool`
3. Migration de schéma additive (colonnes de versioning T4)
4. Tests
5. `docs/STATUS.md` mis à jour

---

## Critère d'acceptation

Pour le cas déjà démontré (EF_CO2 charbon, projet réel Ghana/Burkina Faso,
SPEC-03) : l'argument généré est une prose lisible par un VVB, qui mentionne
le contexte du projet (pays, réponse à la question WCCF) et la source
exacte, **sans introduire un seul chiffre ou référence absent des faits
fournis** — vérifié automatiquement à chaque génération, pas seulement
relu à l'œil une fois.
