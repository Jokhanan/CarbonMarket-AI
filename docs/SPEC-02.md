# SPEC-02 — Sources de données externes indexées par pays

Statut : à implémenter
Créée le 01.08.2026
Prérequis : SPEC-01 (schéma `methodology_version_history`, discipline
`extraction_method`/`verified_by` de `regulatory_values`)
Bloque : SPEC-03 (le moteur de résolution de paramètres a besoin de pouvoir
interroger ces sources par pays et par millésime pour proposer un défaut)

---

## Objectif

RECH v5.0 ne définit pas tous ses paramètres en interne. Plusieurs renvoient
explicitement à des documents ou outils externes, tenus à jour séparément et
indexés par pays (parfois par millésime). Le système doit pouvoir les
interroger automatiquement — pas une seule fois pour combler `gs_rech_v5.py`,
mais en continu, puisque ces sources changent (nouvelle édition de MoFuSS,
nouveau tableau Tool 05 par millésime, mise à jour de la liste des pays les
moins avancés).

**Enjeu clé, redit ici parce qu'il structure tout le reste** : ce n'est pas
un travail de remplissage ponctuel. La valeur de ces données, c'est d'être
**interrogeables par pays et par année** — c'est ce qui permet à SPEC-03 de
proposer un défaut contextualisé au lieu d'une constante figée.

---

## Constat de départ (relecture complète de RECH v5.0, 01.08.2026)

Liste exhaustive des dépendances externes trouvées dans le texte de RECH v5.0,
avec la section qui les invoque. Classées par nature, parce qu'elles
n'appellent pas le même traitement.

### Catégorie A — valeurs numériques indexées par pays (cœur de cette spec)

**1. GS4GG Tool 05 — Downward Adjustment Factor Determination**
- Normative reference : §4.1.2.2(c), page 13
- Définition et formule : §7.4.6.1, Eq.9, pages 32-33 — « This factor
  remains fixed and shall be sourced from the GS4GG Tool 05 corresponding to
  the host country and the calendar year of the monitoring period. »
- Paramètre suivi : §14.3, Parameter ID **ICS 25**, pages 73-74 — « Sourced
  from the latest version of the GS4GG Methodology Tool 05, corresponding to
  the host country and the monitoring year. » Fréquence de mise à jour :
  annuelle.
- **Indexation : pays hôte × année civile de la période de monitoring.**

**2. fNRB — A6.4 MEP012-A04 (ex-CDM TOOL33) et MoFuSS**
- Normative reference : §4.1.2.3(b) « A6.4 MEP012-A04: Methodological tool:
  Fraction of non-renewable biomass », page 13 ; §4.1.2.4(a) « MoFuSS »,
  page 13
- Paramètre suivi : §14.3, Parameter ID **ICS 20**, pages 67-68 — «
  Determined using the latest version of approved standardized methods and
  tools i.e., MoFuSS, or approved A6.4 fNRB tool. » Mise à jour biennale
  obligatoire au renouvellement de période de comptabilisation.
- **Indexation : pays (et, selon l'outil, source de biomasse / région
  infranationale) × date de détermination.** MoFuSS et l'outil A6.4 fNRB ne
  publient pas nécessairement les mêmes valeurs pour le même pays — ce sont
  deux sources concurrentes, pas une seule.

### Catégorie B — classification de pays (légère, mais conditionne des valeurs déjà en base)

**3. Liste des Pays les Moins Avancés (PMA/LDC) et Afrique subsaharienne**
- §2 Définitions (entrée « Wood-to-charcoal conversion factor »), page 7 —
  « Sub-Saharan Africa (SSA) and Least Developed Countries (LDCs): A default
  WCCF ratio of 6:1... Industrialized or High-Efficiency Regions: ...WCCF
  ratio of 4:1... »
- **Conditionne directement l'applicabilité des lignes `EF_CO2`/`EF_nonCO2`
  charbon déjà présentes dans `regulatory_values`** (voir
  `docs/RECH-V5-VALUE-AUDIT.md`, point 3 et 5). Sans cette classification,
  le moteur de résolution (SPEC-03) ne peut pas choisir entre WCCF 6:1 et
  4:1 pour un pays donné.
- Source externe naturelle : liste officielle des PMA (UN-OHRLLS), ~46 pays,
  révisée occasionnellement (retraits/ajouts rares). Petite, stable, facile
  à ingérer intégralement plutôt qu'à la demande.

### Catégorie C — faits d'éligibilité par pays (pas des valeurs numériques : des documents à vérifier au cas par cas)

**4. Liste négative Article 6 / autorité nationale désignée (DNA)**
- §6.3.5-6.3.6, pages 19-20 — l'activité doit être vérifiée contre la liste
  négative ou le cadre Article 6 publié par le pays hôte, ou une lettre
  d'autorisation de la DNA.
- Nature différente des catégories A/B : ce n'est pas une valeur numérique à
  stocker, c'est une vérification documentaire propre à chaque pays, pas
  toujours publiée sous forme structurée. Modélisation proposée en T5,
  ingestion effective volontairement hors périmètre de cette spec.

**5. NDC / stratégie long terme bas-carbone (LT-LEDS) du pays hôte**
- §6.4 (Lock-In Risk Analysis), page ~20, et §7.4.6 (le DAF « lie
  structurellement la trajectoire de référence de l'activité à la
  trajectoire Net Zero du pays hôte »).
- Même nature que le point 4 : document officiel par pays, à citer plutôt
  qu'une base de valeurs à interroger. Mentionné pour complétude, non traité
  ici.

### Catégorie D — dépendances externes, mais pas indexées par pays (hors périmètre de cette spec)

- **Tool - Technical lifetime (A6.4-AMT-006)** : détermine la durée de vie
  technique d'un appareil, qui décide quelle branche d'amortissement des
  embodied emissions s'applique (Eq.18 vs Eq.19 — voir
  `RECH-V5-VALUE-AUDIT.md`, point 9). Indexé par **technologie**, pas par
  pays. À couvrir séparément si SPEC-03 doit un jour recommander la branche
  d'amortissement.
- **Tool 06 — Common Practice Analysis**, §4.1.2.2(d) : méthode
  d'évaluation, pas un tableau de valeurs.
- **A6.4-AMT-002 — Investment analysis**, §4.1.2.3(a) : méthode financière ;
  peut impliquer des taux d'actualisation par pays mais non creusé ici.
- Protocoles de mesure (ISO 19867-1, KPT, WBT) : procédures de test, pas des
  données à interroger.

---

## Périmètre

### Dans le périmètre

1. Modèle de données pour les sources externes et leurs valeurs, indexées
   par pays et par période de validité (catégories A et B)
2. Ingestion de GS4GG Tool 05 (DAF par pays × millésime)
3. Ingestion de la fraction non-renouvelable de biomasse — MoFuSS et outil
   A6.4 fNRB, comme deux sources distinctes pour la même clé
4. Ingestion de la classification PMA/Afrique subsaharienne (conditionne le
   WCCF déjà en base)
5. Résolution : `resolve_external_value(source, key, country_iso, at_date)`
   — même esprit que `resolve_applicable_version` de SPEC-01
6. Rattachement des lignes `regulatory_values` déjà en base dont
   l'applicabilité dépend du pays (WCCF charbon) à cette classification,
   une fois ingérée

### Hors périmètre

- Catégorie C (listes négatives Article 6, NDC/LT-LEDS) : modèle de données
  esquissé (T5) mais ingestion non faite ici — nature documentaire, pas une
  base de valeurs structurée comme A/B
- Catégorie D (durée de vie technique, common practice, analyse
  d'investissement) : non traitée
- Le moteur de résolution de paramètres lui-même (couche 3) → SPEC-03
- Modification de `gs_rech_v5.py`

---

## Travaux

### T1 — Modèle de données

Suivre la même discipline que `regulatory_values` (SPEC-01) : source
déclarée, `extraction_method`, `verified_by`/`verified_at` nullable, jamais
de valeur choisie silencieusement.

**`external_data_sources`** — identité d'une source externe
`id`, `name` (ex. « GS4GG Tool 05 », « MoFuSS », « A6.4 fNRB Tool »),
`maintainer` (« Gold Standard », « UNFCCC / Article 6.4 Mechanism », «
MoFuSS project »), `home_url`, `update_frequency_note` (texte libre, ex. «
annuel », « au renouvellement de la période de comptabilisation »),
`last_checked_at`

**`external_reference_values`** — une valeur, pour un pays et une période
`id`, `source_id` (FK `external_data_sources`), `country_iso` (FK
`countries`, **nullable = valeur par défaut mondiale si la source en prévoit
une**), `key` (ex. `DAF_NetZero`, `fNRB`), `applicable_from` (année ou date
— DAF est annuel, fNRB peut être fixé pour toute une période de
comptabilisation), `applicable_until` (nullable), `value`, `unit`,
`applicability` (JSONB — ex. `{"biomass_source": "fuelwood"}` pour
différencier plusieurs fNRB d'un même pays selon la source de biomasse, même
logique que les trois `EF_CO2` charbon de SPEC-01), `section_ref` (référence
dans le document SOURCE, ex. le tableau de Tool 05, pas dans RECH), `sha256`
du document source, `extraction_method` (`manual`, `llm_extracted`,
`llm_unverified` — même enum que `regulatory_values`), `verified_by`,
`verified_at`, `notes`, `created_at`

Contrainte : comme pour `regulatory_values`, plusieurs lignes peuvent
coexister pour la même clé et le même pays si leur `applicability` diffère
(ex. fNRB MoFuSS vs fNRB A6.4 pour le même pays — deux sources, potentiellement
deux valeurs, aucun choix automatique tant que ce n'est pas arbitré).

**Extension de `countries`** (table existante, 158 lignes) : ajouter
`is_least_developed_country BOOLEAN`, `is_sub_saharan_africa BOOLEAN`,
`ldc_list_source_url TEXT`, `ldc_list_checked_at TIMESTAMP` — additive,
suit le même principe que SPEC-01 T1 (étendre plutôt que dupliquer).

### T2 — Ingestion par source

Un module d'ingestion par source externe (les formats et la disponibilité en
ligne diffèrent probablement d'un outil à l'autre — Tool 05 est un document
Gold Standard téléchargeable, MoFuSS est un outil de modélisation avec ses
propres publications de résultats par pays, l'outil A6.4 fNRB est publié par
le secrétariat de l'Article 6.4). Chaque module suit le même contrat que
`gs_ingest.py` (SPEC-01 T2) : parsing isolé et testable sur fixture, erreur
explicite si la structure change, idempotent.

- `tool05_ingest.py` — DAF par pays × millésime
- `fnrb_ingest.py` — fNRB par pays, une fonction par source (MoFuSS, A6.4),
  résultats stockés séparément (`source_id` différent), jamais fusionnés
  automatiquement
- `ldc_classification_ingest.py` — liste PMA/Afrique subsaharienne

### T3 — Amorçage

Ingérer au minimum les pays où le portefeuille de projets a une présence
réelle (déductible de `carbon_projects.country_iso` / `user_projects`),
plutôt que les 195+ pays du monde d'un coup — un amorçage ciblé, extensible.

### T4 — Résolution

`resolve_external_value(source_name, key, country_iso, at_date, **applicability_filters)`
→ valeur applicable, sur le modèle de
`resolve_applicable_version`/`get_regulatory_value` de SPEC-01. Lève une
erreur explicite si rien n'est ingéré pour ce pays (pas de valeur par
défaut inventée), et si plusieurs lignes correspondent après filtrage par
`applicability` (le système ne choisit jamais seul entre deux sources
concurrentes, ex. MoFuSS vs A6.4).

### T5 — Modèle pour la catégorie C (esquisse, pas d'ingestion)

Table `country_eligibility_facts` esquissée seulement (`country_iso`,
`fact_type` — ex. `article6_negative_list_status` — `status`,
`source_document_url`, `checked_at`, `notes`) pour que SPEC-03 sache qu'un
fait de ce type existe et doit être posé en question à l'utilisateur s'il
n'est pas renseigné, plutôt que supposé. Ingestion réelle hors périmètre.

### T6 — Détection de changement

`check_external_updates(source_name)` — même esprit que le T6 de SPEC-01 :
ne télécharge rien automatiquement, signale ce qui a changé depuis la
dernière ingestion (ex. Tool 05 publie un nouveau millésime).

---

## Tests exigés

- Ingestion Tool 05 sur fixture → DAF correct pour un pays et un millésime
  donnés, erreur explicite si le pays n'est pas couvert par la fixture
- fNRB : deux sources (MoFuSS, A6.4) pour le même pays restent deux lignes
  distinctes, jamais fusionnées ni choisies automatiquement
- Classification PMA : un pays PMA résout `is_least_developed_country=True`
  et devient éligible au WCCF 6:1 ; un pays non-PMA ne l'est pas
- `resolve_external_value` lève une erreur explicite (pas de valeur
  inventée) pour un pays non ingéré
- Idempotence de chaque module d'ingestion (comme SPEC-01 T2)

---

## Livrables

1. Migration de schéma (additive)
2. Un module d'ingestion par source (Tool 05, fNRB × 2 sources,
   classification PMA)
3. `resolve_external_value()` + tests
4. `docs/STATUS.md` mis à jour

---

## Critère d'acceptation

Pour un pays et un millésime donnés dans le portefeuille de projets actuel,
le système peut répondre « DAF = X, source Tool 05 édition Y » et « fNRB =
Z (MoFuSS) ou Z' (A6.4), aucune fusion automatique » sans qu'aucune de ces
valeurs n'ait été codée en dur. C'est le prérequis direct du moteur de
résolution de paramètres (`docs/SPEC-03.md`).
