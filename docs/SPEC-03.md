# SPEC-03 — Moteur de résolution de paramètres (Couche 3)

Statut : à implémenter
Créée le 01.08.2026
Prérequis : SPEC-01 (`regulatory_values`, `methodology_version_history`),
SPEC-02 (`external_reference_values`, indexées par pays)
Bloque : rien explicitement, mais c'est la pièce manquante pour reconnecter
`gs_rech_v5.py` à des valeurs défendables sans que le système choisisse à la
place de l'utilisateur (SPEC-01 T5.4, volontairement laissé en attente)

---

## Objectif

À partir du contexte d'un projet (pays, combustible, technologie, date),
proposer automatiquement, pour chaque paramètre réglementaire :

- une **valeur proposée**
- les **alternatives écartées**, avec leur motif
- la **source** et sa référence de section exacte
- un **argument de défendabilité** face à un VVB
- la possibilité de **modifier**, chaque modification étant tracée

Et, quand une valeur ne peut pas être déduite du contexte du projet (type de
meule utilisée, durée de vie technique de l'appareil, option de leakage
retenue...) : **poser la question à l'utilisateur plutôt que supposer.**

C'est la Couche 3 de `docs/ARCHITECTURE.md` (« Résolution de paramètres »).
Sans elle, reconnecter `gs_rech_v5.py` à `regulatory_values` reviendrait à
remplacer une constante figée par une autre — ce que l'utilisateur a
explicitement écarté le 01.08.2026 : la cible n'est pas une valeur unique
par paramètre, c'est une proposition contextuelle, justifiée, modifiable.

---

## Constat de départ

La table `project_parameters` (schéma existant, non créée par SPEC-01)
stocke déjà, par projet et par année, une valeur retenue avec `source_type`
(`default`, `measured`, `calculated`, `user_override`, `national_inventory`,
`ipcc`, `methodology`, `document_extracted`), `source_reference`,
`validation_status`, `methodology_code`. **C'est la bonne table pour la
valeur retenue** — elle n'a pas besoin d'être remplacée.

Ce qui lui manque, et que rien d'autre ne couvre :

1. Les **alternatives écartées** — `project_parameters` ne garde qu'un
   gagnant, pas les concurrents ni pourquoi ils ont perdu.
2. Un **argument de défendabilité** rédigé (pas juste une référence de
   section brute).
3. Un mécanisme pour **poser une question** quand aucune donnée existante ne
   permet de choisir — aujourd'hui, en l'absence de valeur, le paramètre
   reste simplement vide, sans distinction entre « pas encore renseigné » et
   « le système ne peut pas le déduire, il faut te le demander ».

**Décision** (à valider) : étendre `project_parameters` (colonnes additives)
et créer deux tables neuves, plutôt que dupliquer ce qui existe déjà — même
principe que SPEC-01.

---

## Périmètre

### Dans le périmètre

1. Moteur générique `resolve_parameter()` qui lit `regulatory_values`
   (SPEC-01) et `external_reference_values` (SPEC-02) selon le contexte
   projet, et écrit dans `project_parameters` + les deux nouvelles tables
2. Modélisation des alternatives écartées, avec motif
3. Génération de l'argument de défendabilité (gabarit textuel, pas de
   rédaction libre par IA à ce stade — voir T4)
4. Détection et gestion des faits non déductibles (questions à
   l'utilisateur)
5. Modification tracée d'une valeur proposée (jamais silencieuse)

### Hors périmètre

- Interface utilisateur (formulaires, affichage des questions) — cette spec
  couvre le moteur et son modèle de données, pas le frontend
- Réécriture de `gs_rech_v5.py` pour consommer `resolve_parameter()` — étape
  séparée, une fois ce moteur validé sur des cas réels
- Extraction de nouvelles `regulatory_values`/`external_reference_values` —
  c'est SPEC-01/SPEC-02, ce moteur consomme, il n'extrait pas

---

## Travaux

### T1 — Extension de `project_parameters`

Migration additive :
`defendability_argument TEXT`, `original_proposed_value TEXT` (la
proposition initiale du moteur, conservée même après une modification
manuelle), `resolution_engine_version VARCHAR(20)` (pour savoir quelle
version de la logique de résolution a produit la proposition — utile si la
logique change plus tard et qu'il faut ré-évaluer d'anciens projets),
`resolved_at TIMESTAMP`.

### T2 — `project_parameter_alternatives`

Une ligne par alternative écartée pour un paramètre d'un projet donné.

`id`, `project_parameter_id` (FK `project_parameters(id)`), `value`, `unit`,
`regulatory_value_id` (FK `regulatory_values(id)`, nullable),
`external_reference_value_id` (FK `external_reference_values(id)`,
nullable — exactement une des deux FK doit être renseignée), `section_ref`,
`applicability` (JSONB, copié de la source au moment de la résolution, pour
ne pas dépendre d'un changement ultérieur de la source), `rank` (1 =
proposition retenue, 2+ = écartées, dans l'ordre de la hiérarchie de
préférence), `rejection_reason` (TEXT, **obligatoire si `rank` > 1**),
`created_at`.

### T3 — `project_open_questions`

Un fait que le moteur ne peut pas déduire du contexte du projet, posé à
l'utilisateur plutôt que supposé.

`id`, `project_id` (FK `user_projects(id)`), `question_key` (ex.
`kiln_type_wccf_ratio`, `device_technical_lifetime`,
`market_leakage_option`, `primary_fuel_user_category`), `question_text`
(rédigé, prêt à afficher, en français), `blocks_param_keys` (`text[]` — quels
paramètres de `project_parameters` restent non résolus tant que la question
est ouverte), `status` (`open`, `answered`, `not_applicable`),
`answer_value`, `answered_by`, `answered_at`, `created_at`.

### T4 — Le moteur : `resolve_parameter(project_id, param_key, methodology_version_id)`

1. Rassembler le contexte du projet : pays, combustible(s) baseline/activité,
   technologie, date/millésime — depuis `user_projects` et les paramètres
   déjà connus dans `project_parameters`.
2. Chercher dans `regulatory_values` les lignes dont la `applicability`
   correspond au contexte. Si le paramètre dépend d'une source externe
   indexée par pays (SPEC-02, ex. DAF, fNRB), interroger
   `resolve_external_value()` en complément.
3. **Si un élément de contexte nécessaire n'est pas dans
   `project_parameters` et ne peut pas être déduit** (ex. type de meule
   utilisée pour le charbon, durée de vie technique de l'appareil, option de
   leakage marché retenue parmi les trois de RECH §9.3.2) : créer ou mettre
   à jour une `project_open_questions`, **ne rien écrire dans
   `project_parameters` pour ce paramètre**, et arrêter là pour ce
   paramètre. Ne jamais deviner à la place de l'utilisateur.
4. Sinon, classer les candidats restants selon la **hiérarchie de
   préférence que la méthodologie elle-même énonce** — RECH v5.0 la donne
   explicitement pour chaque paramètre (ex. « Choice of data or measurement
   methods and procedures: i. IPCC defaults ii. Activity-specific field
   tests... »), ce n'est pas à inventer, c'est à lire dans
   `regulatory_values`/le texte source.
5. Retenir le premier candidat de la hiérarchie comme **valeur proposée**,
   écrire les autres dans `project_parameter_alternatives` avec un motif
   dérivé du contexte (ex. « Écartée : valeur nationale non disponible pour
   ce pays, défaut IPCC retenu » ou « Écartée : suppose des émissions de
   carbonisation incluses (WCCF 6:1), non confirmé pour ce projet »).
6. Générer l'**argument de défendabilité** : gabarit textuel combinant
   source, référence de section, position dans la hiérarchie de préférence,
   et toute mention de conservativité que le texte source signale
   explicitement (RECH le fait souvent — « conservative default »,
   « conservativeness discount »).
7. Écrire la valeur retenue dans `project_parameters`
   (`resolution_engine_version` renseigné) et les alternatives dans
   `project_parameter_alternatives`.

### T5 — Modification tracée

`override_parameter(project_id, param_key, new_value, reason, user)` :
seul chemin pour modifier une valeur résolue automatiquement.
- Exige une `reason` non vide — jamais de modification silencieuse.
- Bascule `source_type` à `user_override`, sans toucher à
  `original_proposed_value` (la proposition initiale du moteur reste
  visible).
- L'ancienne valeur (proposée ou précédemment overridée) est conservée —
  soit via un rang spécial dans `project_parameter_alternatives`, soit via
  une table d'historique séparée append-only ; le choix précis se fait à
  l'implémentation, mais **la perte silencieuse d'une valeur précédente
  n'est pas une option.**
- `resolve_parameter()` ne réécrit **jamais** une ligne déjà en
  `source_type='user_override'` sans confirmation explicite de
  l'utilisateur — une résolution automatique ultérieure (ex. après
  ingestion d'une nouvelle version de Tool 05) propose la mise à jour, elle
  ne l'impose pas.

### T6 — Faits non déductibles, par paramètre

Une liste ouverte, à enrichir au fil des méthodologies, des faits qu'aucun
contexte projet ne permet de déduire automatiquement. Pour RECH v5.0,
identifiés dans cette passe :

| Fait | Paramètres bloqués | Pourquoi non déductible |
|---|---|---|
| Type de meule / ratio WCCF applicable | `EF_CO2`, `EF_nonCO2` (charbon) | Le pays seul ne dit pas si le développeur choisit le défaut régional (6:1/4:1) ou le combustion-seule ; c'est une décision de projet |
| Durée de vie technique de l'appareil (< ou ≥ 5 ans) | `embodied_emission_factor` (branche d'amortissement, Eq.18 vs Eq.19) | Dépend de la technologie précise déployée, pas du pays ni du combustible |
| Option de leakage marché retenue (1, 2 ou 3, §9.3.2) | `market_leakage_default` | Choix du développeur d'activité, conditionné par la conception du suivi (P-KPT) |
| Catégorie d'utilisateur primaire (bois/charbon/mixte) | `PCAP` (quelle table de seuils/plafonds s'applique) | Dépend de l'enquête de référence du projet, pas déductible a priori |

Le moteur consulte cette liste avant de tenter une résolution automatique ;
si la réponse n'existe pas déjà dans `project_parameters`, il pose la
question (T3) au lieu de proposer une valeur.

---

## Tests exigés

- Pays des Pays les Moins Avancés + combustible charbon, sans réponse à la
  question du type de meule : le moteur crée une `project_open_questions`,
  n'écrit rien dans `project_parameters` pour `EF_CO2`/`EF_nonCO2`
- Même cas, une fois la question répondue (WCCF 6:1) : le moteur propose
  355.36/89.68, écarte 112/5.87 et 236.91/61.74 avec motif
- Argument de défendabilité généré contient la référence de section exacte
  de la source
- `override_parameter()` : l'ancienne valeur reste retrouvable après
  modification
- `resolve_parameter()` n'écrase jamais une ligne `user_override` sans
  confirmation explicite
- Un paramètre sans aucune ligne `regulatory_values`/`external_reference_values`
  correspondante lève une erreur explicite (pas de valeur par défaut
  inventée par le moteur lui-même)

---

## Livrables

1. Migration de schéma (additive) : `project_parameters` étendue,
   `project_parameter_alternatives` et `project_open_questions` créées
2. `resolve_parameter()`, `override_parameter()` + tests
3. Liste des faits non déductibles pour RECH v5.0 (T6), extensible aux
   méthodologies suivantes
4. `docs/STATUS.md` mis à jour

---

## Critère d'acceptation

Pour un projet réel du portefeuille (pays, méthodologie et combustible
connus), le moteur retourne pour chaque paramètre RECH soit une proposition
défendable — valeur, alternatives écartées motivées, source précise,
argument citable face à un VVB — soit une question claire adressée à
l'utilisateur. Jamais un silence, jamais une valeur inventée sans expliquer
pourquoi elle a été retenue plutôt qu'une autre.
