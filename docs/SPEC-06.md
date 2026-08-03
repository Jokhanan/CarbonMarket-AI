# SPEC-06 — Moteur d'instanciation : template × méthodologie × exigences transverses → champs réels

Statut : à implémenter
Créée le 03.08.2026
Prérequis : SPEC-01 (RECH v5.0 ingéré, mécanisme d'ingestion réutilisé pour
les exigences transverses) ; SPEC-05 T1-T3 (`template_fields`, dont le
`field_type = 'parameter_block'` que cette spec instancie)
Bloque : rien de formellement mandaté, mais sans elle SPEC-05 reste
incomplète pour tout usage réel — `template_fields` sait qu'un VPA-DD a un
patron de bloc paramètre à 18 champs, jamais combien de fois le répéter ni
lesquels des 92 sous-sections viennent de RECH plutôt que d'un document
Gold Standard séparé

---

## Objectif

Corrigé après un retour de l'utilisateur sur le rapport SPEC-05 : compter
« 3 `parameter_block` » dans le VPA-DD v3.0 est trompeur. Ce ne sont pas
trois paramètres, ce sont trois **patrons** de bloc (ex ante 10 champs,
monitoring 18 champs, SDG 13 champs). Un VPA-DD réel en contient autant
d'**exemplaires** qu'il a de paramètres de calcul — celui du Kenya (GS
11319, cité dans SPEC-04) en a 16. **Le template ne dit pas combien il en
faut ni lequel des trois patrons utiliser pour tel paramètre — c'est la
méthodologie qui le dit.**

Deuxième angle mort identique dans son principe : un VPA-DD ne se remplit
pas avec la seule méthodologie. Les sections Safeguarding, Genre,
Consultation des parties prenantes et Développement durable du VPA-DD ne
viennent pas de RECH v5.0 — elles viennent de documents Gold Standard
transversaux séparés, applicables à *tout* projet quel que soit le
secteur.

L'équation réelle, telle que formulée par l'utilisateur :

**template × méthodologie × exigences transverses → champs réels d'un
projet donné.**

Aucune des trois sources ne suffit seule. `docs/SPEC-05.md` ne couvre que
le premier facteur (les patrons). Cette spec couvre les deux facteurs
manquants et leur croisement avec le premier.

---

## Constat de départ (03.08.2026)

### RECH v5.0 : structure réelle d'un paramètre, lue directement dans le PDF déjà ingéré (SPEC-01)

Chaque paramètre de calcul porte un identifiant (« Parameter ID ICS 24 »,
« ICS 25 », « ICS 26»... — au moins quatre confirmés au fil de cette
session : ICS 20 pour le fNRB cité en SPEC-02, ICS 24/25/26 lus
directement aux pages 73-74 du PDF v5.0) suivi d'un bloc structuré aux
champs fixes :

`Data/parameter` · `Description` · `Data unit` · `Purpose of data` ·
`Measurement and updating frequency` · `Measurement methods and
procedures` · `Entity/person responsible for the measurement` ·
`Measuring instrument(s)` (sous-champs Type/Accuracy class/Calibration
requirements/Location) · `QA/QC procedures` · `Treatment of uncertainty`
· `Comments`.

C'est, champ pour champ, quasiment le patron **monitoring** du VPA-DD
v3.0 identifié en SPEC-05 (table 40, 18 champs). Ce n'est pas une
coïncidence — les deux documents parlent le même vocabulaire CDM/GS4GG
hérité. **Le discriminant ex ante / monitoring n'est pas un champ séparé,
il se lit dans le contenu de `Measurement and updating frequency`** :
« Determined ex-ante and fixed for the crediting period » (fNRB, ICS 20)
→ patron ex ante (10 champs) ; « Annual » (DAF, Tool 05) ou « Biennial »
(fNRB si option de mise à jour choisie) → patron monitoring (18 champs).
Certains paramètres (fNRB) déclarent explicitement les deux options
possibles, confirmées à la certification du design — un même paramètre
peut donc devoir être instancié dans les deux patrons selon le choix fait
par le projet, pas dans un seul par nature fixe.

### Exigences transverses Gold Standard : liste réelle vérifiée en ligne (même démarche que RECH en SPEC-01)

Consulté `globalgoals.goldstandard.org/documents/core-documents/` et
`/200-activity-requirements/` le 03.08.2026 :

| Code | Titre | Version | Date | Gouverne (section VPA-DD v3.0, SPEC-05 T7) |
|---|---|---|---|---|
| 101 | Principles & Requirements | v2.1 | 31.01.2025 | Éligibilité générale, structure globale du document |
| 102 | Stakeholder Consultation and Engagement Requirements | — | 14.06.2022 | Stakeholder Consultation assessment |
| 103 | Safeguarding Principles & Requirements | v2.1 | 29.06.2023 | Safeguarding principles and Gender Sensitivity Assessment |
| 104 | Gender Equality Requirements & Guidelines | v2.0 | 16.05.2023 | Gender equality assessment (13 sous-sections — la section qui a le plus grossi entre v2.3 et v3.0, voir rapport SPEC-05) |
| 118 | Requirements for selection of Monitoring Indicators in the SDG Impact Tool | — | 18.10.2025 | Sustainable development contribution |
| 119 | Requirements for Paris Agreement Alignment | — | 02.02.2026 | Les nouvelles questions A6.4/PACM en tête du document (cohérent avec le préfixe de nom de fichier « PAA » du template v3.0 — 119 est publié trois mois avant le rafraîchissement du template du 15.05.2026, causalité plausible) |
| 201 | Community Services Activity Requirements | v1.2 | 23.10.2019 | Éligibilité propre à l'activité — les cookstoves/RECH relèvent de ce périmètre (« end-use energy efficiency, waste management and handling and WASH ») |

Deux constats additionnels, ni l'un ni l'autre traité dans cette spec :

- **201 est daté 2019** — nettement plus ancien que le reste du corpus
  transversal (2022-2026), potentiellement dans le même état de dérive
  que les templates avant SPEC-05. Signalé, hors périmètre (SPEC-05 T0
  n'a vérifié que le VPA-DD).
- 6 autres documents Activity Requirements existent (202 Renewable
  Energy, 203 Land-use & Forests, 204 Blue Carbon, 205 Engineered
  Removals, 206 Agriculture) — non pertinents pour RECH/cookstoves, non
  traités.

**Piège structurel trouvé en vérifiant, avant d'écrire le moindre code** :
les pages de ces documents transversaux (103, 104, etc.) partagent le
même défaut de balisage que les pages de template — chaque `<tr>` de leur
table REVISION HISTORY n'est pas fermé, ce qui corrompt le comptage de
cellules avec le parseur `html.parser` (`gs_ingest.py`) exactement comme
constaté sur le VPA-DD (SPEC-05 T0). Confirmé par un comptage direct sur
`103-par-safeguarding-principles-requirements/` : une ligne censée avoir
3 cellules en a 24 avec `html.parser`, 3 avec `lxml`. **Le mécanisme
d'ingestion de SPEC-01 est réutilisable dans son principe** (page → table
REVISION HISTORY → versions → téléchargement idempotent, dédup sha256)
**mais l'implémentation doit reprendre le parseur `lxml` de
`gs_template_ingest.py` (SPEC-05 T2), pas celui de `gs_ingest.py` tel
quel.**

---

## Périmètre

### Dans le périmètre

1. Modèle de données pour les paramètres extraits d'une méthodologie,
   classés ex ante / monitoring / les deux, avec unité, source de
   données, méthode de mesure
2. Ingestion des 7 documents transversaux identifiés ci-dessus
3. Modèle de liaison entre un champ de template et sa ou ses sources
   d'exigence, traçable et vérifiable
4. Moteur d'instanciation : patron de bloc × liste de paramètres → N
   blocs concrets pour un projet donné
5. Modélisation de ce qui reste non déductible et doit être demandé à
   l'utilisateur

### Hors périmètre

- Extraction automatique et exhaustive de **tous** les paramètres de RECH
  v5.0 — cette spec établit la méthode et l'amorce sur les paramètres déjà
  cités dans cette conversation (ICS 20, 24, 25, 26 + le bloc charbon
  EF_CO2/EF_nonCO2 déjà en base). L'extraction systématique complète est
  un travail de mise en œuvre séparé, sur le modèle de SPEC-01 T5 (extraire
  puis soumettre un rapport d'écarts à l'utilisateur, ne rien corriger
  seul)
- L'adaptateur `load_guide()`/`doc_exporter.py` (T6 de SPEC-05) — cette
  spec produit les données qu'il consommera, ne le construit pas
- Les 6 autres documents Activity Requirements (202-206), non pertinents
  pour RECH
- La correction de la datation de 201 (2019) — signalée, pas traitée
- Application à un autre couple (méthodologie, template) que RECH v5.0 /
  VPA-DD v3.0 — cette spec est démontrée sur ce seul couple, comme SPEC-05
  T7 l'a fait pour le seul VPA-DD

---

## Travaux

### T1 — Modèle de données : paramètres de méthodologie

Migration additive.

**`methodology_parameters`** — un paramètre de calcul extrait d'une
version de méthodologie
`id`, `methodology_version_id` (FK `methodology_version_history`),
`parameter_id` (identifiant propre à la méthodologie, ex. « ICS 24 »),
`key` (nom symbolique si dérivable, ex. `LE_Market_y`), `description`,
`unit`, `purpose`, `timing_classification` (`ex_ante` | `monitoring` |
`both` — `both` pour les cas où la méthodologie laisse explicitement le
choix à la certification, comme le fNRB), `measurement_frequency_note`
(texte brut du champ source — c'est lui qui sert à déduire
`timing_classification`, jamais l'inverse), `measurement_method`,
`responsible_entity`, `qa_qc_procedures`, `section_ref`, `page_ref`,
`extraction_method` / `verified_by` / `verified_at` (même discipline que
`regulatory_values`, SPEC-01), `created_at`.

### T2 — Ingestion des exigences transverses

Réutilise le patron d'ingestion de SPEC-01 (page → REVISION HISTORY →
versions → téléchargement idempotent) mais avec le parseur `lxml` de
SPEC-05 T2 (voir Constat de départ). Nouveau module —
`gs_crosscutting_ingest.py`, ou extension de `gs_template_ingest.py` (à
trancher à l'implémentation selon le degré de code effectivement
partageable une fois écrit) — écrivant dans une table
`crosscutting_requirements` calquée sur `methodology_version_history`
(`code`, `version`, `released_date`, `effective_from`/`effective_until`,
`is_current`, `local_path`, `sha256`).

Cible les 7 pages listées dans le Constat de départ (101, 102, 103, 104,
118, 119, 201).

### T3 — Amorçage : extraction des paramètres RECH v5.0

Applique T1 à RECH v5.0. Méthode d'extraction, dans l'ordre de
préférence : les blocs « Parameter ID ... » suivent un motif structurel
régulier et répétitif (repérable par le label « Parameter ID » en tête de
bloc) — extractible par un parseur de texte dédié sur le PDF déjà ingéré
(`pdfplumber`, déjà une dépendance du dépôt), pas par un LLM en première
intention. Un LLM n'intervient qu'en repli si le motif structurel échoue
sur un bloc donné, avec `extraction_method = 'llm_unverified'` dans ce
cas — jamais consommé silencieusement en aval (même garde-fou que SPEC-01
T5 et SPEC-03).

Amorçage limité aux paramètres déjà rencontrés dans cette conversation
(ICS 20, 24, 25, 26, et le rattachement croisé aux trois lignes
`regulatory_values` charbon EF_CO2/EF_nonCO2 déjà en base depuis SPEC-01/
SPEC-03) — sert de preuve de concept et de vérification croisée, pas
l'extraction complète de RECH (renvoyée en un travail séparé, cf.
Périmètre).

### T4 — Liaison champ de template ↔ source d'exigence

**`template_field_requirements`** — une ligne par (champ, source qui le
gouverne)
`id`, `template_field_id` (FK `template_fields`, SPEC-05), `requirement_type`
(`methodology` | `crosscutting`), `methodology_version_id` (FK nullable),
`crosscutting_requirement_id` (FK nullable) — contrainte : exactement un
des deux non NULL selon `requirement_type`, jamais les deux, jamais
aucun ; `notes`.

Un même champ peut être gouverné par plusieurs sources à la fois (ex. la
section Safeguarding est gouvernée par 103 *et*, si RECH y ajoute une
exigence propre à la carbonisation du bois, par RECH lui-même — pas
supposé ici, à vérifier au cas par cas).

Amorçage : table de correspondance saisie manuellement à partir du
Constat de départ ci-dessus (7 lignes methodology/crosscutting → 9
sections de niveau 1 du VPA-DD v3.0) — une donnée vérifiée une fois, pas
une extraction automatique par similarité de texte (qui serait le genre
d'heuristique fragile que cette spec cherche justement à éviter).

### T5 — Moteur d'instanciation

`instantiate_parameter_blocks(template_version_id, methodology_version_id)
-> list[dict]`

Pour chaque patron de bloc (`template_fields` où `field_type =
'parameter_block'`) : sélectionne les lignes `methodology_parameters`
dont `timing_classification` correspond au patron (`ex_ante` → patron
ex ante, `monitoring` → patron monitoring ; un paramètre `both` produit
une instance dans chacun des deux patrons compatibles), produit une
instance par paramètre correspondant, chaque champ du patron rempli
depuis la colonne `methodology_parameters` équivalente — une
correspondance colonne-à-colonne explicite et documentée dans le code
(`unit` → `unit`, `measurement_method` → `Measurement methods and
procedures`, etc.), jamais une extraction devinée à l'exécution.

Retourne séparément la liste des paramètres dont l'extraction n'est pas
vérifiée (`extraction_method = 'llm_unverified'` ou colonne requise
NULL) — ceux-là ne sont **pas** instanciés silencieusement dans le
résultat principal, ils remontent comme « à vérifier avant usage » (R2).

### T6 — Ce qui reste non déductible

Aucune nouvelle table — réutilise `project_open_questions` (SPEC-03),
déjà le mécanisme du système pour tout fait qu'aucune source documentaire
ne peut fournir. Cette spec **liste** les catégories de faits non
déductibles identifiées pour RECH/VPA-DD/cookstoves, sans toutes les
implémenter (l'amorçage reste limité à EF_CO2/EF_nonCO2, cohérent avec le
périmètre déjà validé en SPEC-03) :

- **Choix de piste optionnelle** : 104 impose une piste « gender-sensitive »
  obligatoire mais laisse la piste « gender-responsive » (quantification
  de l'impact SDG 5) optionnelle — un choix de projet, jamais déductible
  d'un document.
- **Échelle/catégorie du VPA** : micro/small/large scale (Table 0 du
  template, SPEC-05) — dépend du projet, pas de la méthodologie.
- **Données de terrain propres au site** : coordonnées GPS, quantités de
  foyers distribués, dates d'installation — aucune source documentaire ne
  les contient par construction, ce sont des faits du monde, pas des
  règles.
- **Statut CORSIA / A6.4 / PACM** : les nouvelles questions de 119
  (v3.0) sont des faits déclaratifs sur le projet (enregistrement CDM
  antérieur, autorisation A6.4...), pas des valeurs à calculer.

---

## Tests exigés

- Extraction d'un bloc « Parameter ID » sur un extrait de texte RECH
  fixture (ICS 24, page 73 confirmée dans cette session) → tous les
  champs du patron monitoring correctement remplis
- `timing_classification` déduite correctement : « Determined ex-ante and
  fixed for the crediting period » → `ex_ante` ; « Annual » → `monitoring`
  ; le cas fNRB (les deux options mentionnées) → `both`
- Ingestion d'une page transverse (103) sur fixture HTML → versions
  correctement extraites avec le parseur `lxml`, comptage de cellules non
  corrompu (test de non-régression direct sur le piège trouvé en T0)
- `instantiate_parameter_blocks` : pour un jeu de 3 paramètres fixture (2
  ex ante, 1 monitoring), produit exactement 2 instances du patron ex
  ante et 1 du patron monitoring, aucune instance pour un paramètre
  `llm_unverified`
- `template_field_requirements` : contrainte CHECK rejette une ligne avec
  `methodology_version_id` et `crosscutting_requirement_id` tous deux
  NULL, ou tous deux renseignés

---

## Livrables

1. Migration de schéma additive (`methodology_parameters`,
   `crosscutting_requirements`, `template_field_requirements`)
2. Module d'ingestion des exigences transverses + tests + fixtures
3. Extracteur de paramètres RECH (amorcé sur ICS 20/24/25/26) + tests
4. Table de correspondance champ ↔ exigence (amorçage manuel documenté)
5. `instantiate_parameter_blocks()` + tests
6. `docs/STATUS.md` mis à jour

---

## Critère d'acceptation

Pour le VPA-DD v3.0 / RECH v5.0 / le projet réel `user_projects.id=12`
(Ghana, déjà utilisé tout au long de cette session), le système peut
répondre : « le patron monitoring (table 40, SPEC-05) doit être instancié
au moins pour ICS 24, ICS 25, ICS 26, chacun avec son unité, sa source et
sa méthode tirées de RECH ; sa section transverse gouvernante est 103 pour
Safeguarding, 104 pour Genre ; et voici la liste de ce qui manque encore
pour remplir le VPA-DD — posé comme question ouverte à l'utilisateur, pas
deviné. » Aucun champ n'est rempli par une source qui ne le gouverne pas
réellement, et aucun paramètre non vérifié n'entre silencieusement dans
le résultat.
