# SPEC-05 — Ingestion et analyse automatique des templates officiels

Statut : à implémenter
Créée le 03.08.2026
Prérequis : SPEC-01 (même patron d'ingestion — page de standard → historique de
versions → téléchargement → détection de changement — appliqué ici aux
templates de documents plutôt qu'aux méthodologies)
Bloque : la fiabilité des cinq parcours documentaires identifiés lors de la
reconnaissance du 03.08.2026 (rien → PDD/VPA-DD ; PoA-DD → VPA-DD ;
VPA-DD → premier MR ; MR an N → MR an N+1 ; commentaires VVB → réponses
CAR/CL) — tant que les templates sont recopiés à la main, tout ce qui est
construit dessus dérive avec eux

---

## Objectif

`carbongpt/guides/*.py` encode aujourd'hui à la main, en Python, la structure
de chaque template officiel (Gold Standard VPA-DD, PDD, PoA-DD, MR ; Verra VCS
PD, MR, ValVer). C'est l'anti-pattern exact que R1 de CLAUDE.md interdit :
« quand Gold Standard republie, il faut réécrire du Python — donc personne ne
le fait, et le système dérive. » La reconnaissance du 03.08.2026 en a
mesuré l'ampleur : les quatre templates Gold Standard ont été republiés le
même jour (15.05.2026) et le code n'en a aucun ; côté Verra, ce n'est même
plus une question de version, c'est un changement de standard entier (VCS
V4 → V5).

Le système doit savoir, pour tout couple (standard, type de document) :

- quelles versions du template existent, laquelle est en vigueur, à quelle
  date, et dans quelles conditions (un template peut être applicable
  simultanément à plusieurs versions selon un attribut du projet — voir
  Verra 5.0A/5.0B ci-dessous, différent du cas RECH où une seule version est
  en vigueur à une date donnée)
- la structure réelle de ce template : sections, sous-sections, et pour
  chaque champ son type (texte libre, tableau, valeur unique, case à cocher,
  bloc de paramètre répété, pièce jointe) et sa position exacte dans le
  document
- tout cela **sans réécrire `generate_full_document()` ni `doc_exporter.py`**,
  qui fonctionnent déjà et n'ont pas besoin d'être reconstruits — seulement
  d'être nourris par la bonne donnée au lieu d'un module Python figé

---

## Constat de départ (reconnaissance du 03.08.2026, sans code)

### Ce qui existe et fonctionne déjà

- `carbongpt/core/ai_writer.py::generate_full_document()` boucle sur
  `guide.SUBSECTIONS` (importé via `carbongpt.guides.load_guide(standard,
  doc_type)`) et génère un brouillon par sous-section.
- `carbongpt/core/doc_exporter.py` réinjecte ce brouillon dans le vrai
  `.docx` officiel — gestion des cases à cocher (`_check_checkbox_in_cell`),
  du tableau Key Project Information (`_fill_gs_kpi_table`), correspondance
  titre → identifiant de section (`_match_gs_title_to_sid`).

Les deux mécanismes sont solides. Le problème n'est pas la mécanique, c'est
ce qu'elle lit :

### Ce qui est figé à la main et daté

`carbongpt/guides/__init__.py::GUIDE_REGISTRY` fait correspondre
`(standard, doc_type)` à un **module Python** (`gs_vpa_dd_v2_3.py`,
`vcs_pd_v4_4.py`, etc.) contenant un dictionnaire `SUBSECTIONS` écrit à la
main. `carbongpt/core/doc_exporter.py::TEMPLATE_FILES` fait la même chose
pour le **fichier `.docx` physique** — un dictionnaire de noms de fichiers
littéraux pointant dans `document_repository/`. Les deux sont des
constantes en dur au sens de R1, pas des données.

Écarts mesurés le 03.08.2026 (détail complet dans le rapport de
reconnaissance de cette conversation) :

| Standard | Document | Code actuel | Officiel actuel | Écart |
|---|---|---|---|---|
| Gold Standard | VPA-DD | v2.3 (29.06.2023) | **v3.0 (15.05.2026)** | 2 versions |
| Gold Standard | PDD | v1.5 | **v2.0 (15.05.2026)** | — |
| Gold Standard | PoA-DD | v2.2 | **v3.0 (15.05.2026)** | — |
| Gold Standard | MR (PerfCert) | v1.2 dans le code, v1.1 le fichier réel | **v2.0 (15.05.2026)** | code et fichier local déjà en désaccord entre eux |
| Verra | Project Description | v4.4 | **VCS v5.0A/5.0B** (opérationnalisé 09.06.2026) | changement de standard |
| Verra | Monitoring Report | v4.4 | **VCS v5.0A/5.0B** | changement de standard |
| Verra | Validation/Vérification | v4.4, modèle **joint** | **deux documents séparés**, v5.0A/5.0B | changement de structure, pas juste de version |
| Verra | VM0050 (cookstoves) | v1.0 | v1.0 toujours en vigueur | à jour |

**Échéance dure côté Verra** : tout dossier soumis après le **1er janvier
2027** doit utiliser les templates v5.0B, y compris les projets en cours.
Nous sommes le 03.08.2026 — moins de cinq mois.

### Anatomie déjà vérifiée pour le VPA-DD (sert de cas de référence pour T3/T4)

Extraction directe du blanc officiel v2.3 (`python-docx`, sans lib
supplémentaire — déjà présent dans le venv) : 18 tableaux, 499 lignes,
~1468 cellules, 6 sections (A–F) + 4 annexes. Deux formes de champ
récurrentes qui ne sont **pas** de simples sous-sections :

- **Bloc de paramètre répété** (sections B.6.2 et B.7) : un petit tableau à
  répéter par paramètre de calcul — 8 champs ex ante (Data/parameter, Unit,
  Description, Source of data, Value(s) applied, Choice of data or
  Measurement methods, Purpose of data, Additional comment), 10 en
  monitoring (+ Monitoring frequency, QA/QC procedures). Un VPA-DD réel
  (GS 11319, Kenya) en contient 16 répétitions.
- **Checklist massive** (Appendice 1, Safeguarding Principles) : 339
  lignes, **116 questions individuelles** codées `P.1`, `P.1.1.1`... avec
  colonnes Reference requirement | Question | Response. `gs_vpa_dd_v2_3.py`
  ne l'encode pas — `D.1` n'y est qu'un résumé à 4 points.

Le guide Python actuel couvre correctement les 27 sous-sections narratives
A–F (vérifié champ par champ), mais ignore structurellement tout ce qui est
répété ou en annexe. C'est exactement ce que l'analyse automatique doit
produire et que l'écriture manuelle n'a jamais suivi.

### Ce qui n'a pas encore été vérifié (à faire en T0 avant d'écrire du code)

- La page Verra listant les templates V5 (`verra.org/programs/verified-carbon-standard/vcs-program-details/`)
  a été lue via un outil de résumé IA dans la reconnaissance, pas
  inspectée en HTML brut. Sa structure réelle (page statique avec tableau
  de révisions comme Gold Standard, ou liste de liens moins régulière) n'est
  pas confirmée — à vérifier avant d'écrire l'ingesteur Verra, comme SPEC-01
  T0 et SPEC-02 T0 l'ont fait avant chaque ingesteur.
- Les pages de templates Gold Standard (`globalgoals.goldstandard.org/t-prereview-*`,
  `/t-perfcert-*`) ont, elles, été confirmées structurées en tableau
  « Revision History » avec version, date, lien direct — même format que
  les pages de méthodologies de SPEC-01. Réutilisable tel quel.

---

## Périmètre

### Dans le périmètre

1. Modèle de données pour les templates de documents, leurs versions, et
   leur structure de champs analysée
2. Ingestion automatique des pages de templates (Gold Standard confirmé
   exploitable ; Verra à vérifier en T0)
3. Analyse structurelle d'un `.docx` officiel en champs typés et positionnés
4. Couverture des blocs répétés et des annexes (Safeguarding compris)
5. Résolution de la version de template applicable — y compris le cas où
   deux versions sont valides simultanément selon un attribut du projet
   (Verra 5.0A/5.0B)
6. Adaptateur de compatibilité pour que `generate_full_document()` et
   `doc_exporter.py` continuent de fonctionner sans modification pendant la
   migration progressive des guides Python vers cette structure
7. Fusion de la méthodologie dupliquée en base (`GS-TPDDTEC` / `407`)
8. Détection automatique de nouvelles versions de templates

### Hors périmètre

- Réécriture de `generate_full_document()` ou `doc_exporter.py` — ils
  fonctionnent, on change ce qu'ils lisent, pas comment ils lisent
- Le moteur de sélection standard → méthodologie → template (chaîne décrite
  au point 3 de la reconnaissance, dépend d'abord de SPEC-02) — cette spec
  fournit le maillon « template → champs requis », pas les maillons en amont
- Templates CAR/CL — aucun template officiel identifié à ce jour ni chez
  Gold Standard ni chez Verra ; à reprendre séparément une fois confirmé
  qu'un tel document structuré existe réellement (portail de soumission des
  VVB plutôt qu'un fichier téléchargeable, peut-être)
- Templates CDM (119 méthodologies en base sous ce standard, mais aucun
  document du portefeuille actuel n'en a besoin)
- Migration effective de tous les guides existants — seul le VPA-DD Gold
  Standard est amené jusqu'au bout dans cette spec (voir Priorité
  ci-dessous) ; les autres restent sur les modules Python jusqu'à leur tour

---

## Priorité d'implémentation

**Le VPA-DD Gold Standard v3.0 en premier** — c'est le besoin immédiat.
L'amorçage (T7) cible uniquement ce couple (standard, doc_type) jusqu'au
bout de la chaîne : ingestion, analyse, adaptateur, vérification que
`generate_full_document`/`doc_exporter` produisent bien un document basé sur
le vrai v3.0. Les autres guides Gold Standard (PDD, PoA-DD, MR) restent sur
leurs modules Python existants après cette spec — à migrer un par un dans
des tours ultérieurs, une fois le patron validé sur le VPA-DD.

**Mais la conception (T1, T5) doit prévoir Verra v5.0B dès le départ**,
même si son ingestion n'est pas faite ici. Deux raisons concrètes :

1. **Pas de template joint dans le modèle de données.** `vcs_valver_v4_4.py`
   et `TEMPLATE_FILES[("Verra", "valver")]` supposent aujourd'hui un document
   unique Validation+Vérification. La V5 le remplace par deux documents
   distincts (Validation Report, Verification Report). Le modèle de données
   ne doit à aucun endroit supposer qu'un `doc_type` Verra de type
   « validation » est unique — `document_templates.doc_type` doit pouvoir
   porter `VCS-ValidationReport` et `VCS-VerificationReport` comme deux
   entrées indépendantes dès la conception du schéma, même si seule
   l'ancienne entrée jointe (`VCS-ValVer`, v4.4) est réellement peuplée par
   cette spec. Ne pas coder en dur ailleurs (adaptateur T6 compris) une
   hypothèse de correspondance 1:1 entre « validation » et « vérification ».
2. **Deux versions simultanément valides, pas une succession chronologique
   simple.** Le modèle `resolve_applicable_version` de SPEC-01 suppose
   qu'une seule version est en vigueur à une date donnée. Verra 5.0A/5.0B
   casse cette hypothèse : les deux coexistent, le choix dépend de la date
   de démarrage du **projet**, pas de la date de la requête. `document_template_versions`
   doit porter ce distinguo nativement (voir T1) pour que le jour où
   l'ingestion Verra est faite, aucune migration de schéma supplémentaire
   ne soit nécessaire.

---

## Travaux

### T0 — Vérifier la disponibilité et la structure réelle de chaque source

Confirmé pour Gold Standard (tableau Revision History structuré, même
format que les pages de méthodologies de SPEC-01, pas de blocage
Cloudflare — cohérent avec le constat SPEC-01 T0). **À faire avant
d'écrire l'ingesteur Verra** : inspecter le HTML brut de la page VCS
Program Details (pas un résumé IA), confirmer la présence d'un tableau de
versions exploitable par un parseur, et vérifier l'absence de protection
anti-bot (comme SPEC-02 T0 l'a fait pour Tool 05, MoFuSS et l'outil A6.4 —
trois résultats différents pour trois sources qui semblaient similaires).

### T1 — Modèle de données

Migration additive (ne casse aucune des tables existantes).

**`document_templates`** — identité stable d'un couple (standard, type de
document)
`id`, `standard` (GoldStandard, Verra), `doc_type` (`VPA-DD`, `PDD`,
`PoA-DD`, `MR`, `VCS-PD`, `VCS-MR`, `VCS-ValidationReport`,
`VCS-VerificationReport`, `VCS-ValVer` conservé comme entrée historique
pour la V4 jointe — pas de contrainte figée en enum, une nouvelle valeur de
`doc_type` doit pouvoir s'ajouter sans migration de schéma, cf. R1),
`name`, `source_url` (page listant les versions), `last_checked_at`

**`document_template_versions`** — une ligne par version publiée
`id`, `template_id` (FK), `version` (« 3.0 », « 5.0B »), `released_date`,
`effective_from`, `effective_until` (nullable), `is_current` (bool),
`project_start_before` (date, nullable), `project_start_on_or_after` (date,
nullable) — ces deux derniers champs portent le cas Verra 5.0A/5.0B : une
version peut être sélectionnée non pas par la date du jour mais par un
attribut du projet évalué contre un seuil ; NULL pour le cas RECH-like où
une seule version est en vigueur à la fois ; `document_name`,
`download_url`, `local_path`, `sha256`, `ingested_at`, `parsed_at`
(nullable — renseigné une fois l'analyse structurelle T3 exécutée sur ce
fichier)

**`template_fields`** — un champ structurel, résultat de l'analyse T3
`id`, `template_version_id` (FK), `field_key` (identifiant stable — « B.6.2 »,
ou pour un item Safeguarding « P.4.3.2 »), `parent_section` (« SECTION B »,
« Appendix 1 »), `title`, `field_type` (enum : `prose`, `table`,
`single_value`, `checkbox`, `parameter_block`, `checklist_item`,
`attachment`), `position` (JSONB — ancrage réel dans le `.docx`, ex.
`{"table_index": 7, "row_index": 2}` ou `{"paragraph_index": 42}` —
condition posée explicitement : la position doit être exploitable pour
replacer le contenu au bon endroit, pas seulement documentée), `repeat_of`
(FK nullable vers un autre `template_fields.id` — le modèle d'un bloc
répété, ex. la définition du bloc paramètre de B.6.2, dont chaque paramètre
concret d'un projet réel est une instance), `must_include`,
`format_instructions` (texte — portés depuis les guides Python existants
au moment de la migration T6, pas recréés depuis zéro), `created_at`

### T2 — Ingestion des pages de templates

Un module par standard, même contrat que `gs_ingest.py` (SPEC-01 T2) :
parsing isolé et testable sur fixture HTML sauvegardée, idempotent, erreur
explicite si le parsing échoue.

- `gs_template_ingest.py` — réutilise le même patron de parsing de tableau
  Revision History que `gs_ingest.py`, appliqué aux quatre pages
  `/t-prereview-vpa-design-document/`, `/t-prereview-design-document/`,
  `/t-prereview-poa-design-document/`, `/t-perfcert-monitoring-report/`
- `verra_template_ingest.py` — structure à déterminer en T0 ; ne pas
  supposer qu'elle ressemble à celle de Gold Standard avant vérification

### T3 — Analyse structurelle du `.docx`

Le cœur technique nouveau de cette spec. Module `template_docx_parser.py`.

- `parse_template_structure(local_path) -> list[dict]` — parcourt le
  document avec `python-docx` (déjà utilisé dans la reconnaissance,
  disponible dans le venv), produit une liste de `template_fields` :
  - paragraphes de style Heading → sections/sous-sections, `field_type`
    déduit du contenu qui suit (texte libre par défaut)
  - tableaux dont la première cellule ressemble à un en-tête de bloc
    paramètre (« Data/parameter », « Data / Parameter ») → `field_type =
    parameter_block`, `repeat_of` pointant vers un seul modèle par section
  - cellules organisées en options délimitées (ex. « Real case VPA \|
    Regular VPA ») → `field_type = checkbox`
  - tableaux simples à une valeur par ligne → `field_type = single_value`
    ou `table` selon le nombre de colonnes
- Position toujours enregistrée en indices structurels du document
  (`table_index`, `row_index`, `paragraph_index`), pas en heuristique de
  texte — condition pour que `doc_exporter.py` puisse un jour s'appuyer
  dessus plutôt que sur la correspondance de titre actuelle
  (`_match_gs_title_to_sid`)
- Si la structure ne correspond à aucun motif connu, la traiter comme
  `prose` par défaut avec un avertissement loggé — jamais d'échec silencieux
  ni de perte de champ

### T4 — Couverture des blocs répétés et des annexes

Traitement explicite du cas Safeguarding, généralisé pour toute annexe de
forme similaire (motif observé : une colonne de code hiérarchique du type
`P.<n>(\.<n>)*` répété sur des dizaines/centaines de lignes) :

- Détecter le motif de code répétitif dans la première colonne d'un grand
  tableau
- Créer un `template_fields` par ligne détectée, `field_type =
  checklist_item`, `field_key` = le code exact tel qu'écrit dans le
  document (« P.4.3.2 »), `parent_section` = le nom de l'annexe
- Vérifier sur le VPA-DD v2.3 (puis v3.0 une fois ingéré) que les 116
  codes de l'Appendice 1 sont extraits sans perte ni doublon

### T5 — Résolution de version applicable

`resolve_applicable_template(standard, doc_type, *, at_date=None,
project_start_date=None) -> document_template_versions row`

Deux modes, explicitement distingués plutôt que masqués dans une seule
heuristique :

- **Mode succession** (Gold Standard aujourd'hui, RECH-like) : une seule
  version a `effective_from <= at_date <= effective_until` (ou
  `effective_until IS NULL` et `is_current`). Retourne cette version.
- **Mode double piste** (Verra V5) : si `project_start_before` /
  `project_start_on_or_after` sont renseignés sur plusieurs versions
  candidates, la sélection se fait sur `project_start_date` (obligatoire
  dans ce mode — lever une erreur explicite s'il manque, jamais deviner).

Erreur explicite si aucune version ne correspond — jamais de valeur par
défaut inventée, même logique que `resolve_applicable_version` (SPEC-01) et
`resolve_external_value` (SPEC-02).

### T6 — Adaptateur de compatibilité (migration progressive, rien ne casse)

Deux points d'entrée aujourd'hui figés à modifier, chacun avec un repli
vers le comportement actuel :

- **`carbongpt/guides/__init__.py::load_guide(standard, doc_type)`** —
  avant de résoudre via `GUIDE_REGISTRY` (module Python), vérifier si une
  `document_template_versions` correspondante existe, est `is_current`, et
  a `parsed_at` renseigné. Si oui, construire à la volée un objet exposant
  un attribut `.SUBSECTIONS` de même forme que les modules Python actuels
  (dict `field_key -> {title, parent_section, content_format, ...}`,
  reconstitué depuis `template_fields`) — `generate_full_document()` ne
  voit aucune différence, il lit `.SUBSECTIONS` comme avant. Si aucune
  version analysée n'existe pour ce couple, retomber sur `GUIDE_REGISTRY`
  exactement comme aujourd'hui. C'est ce qui permet de migrer un
  `(standard, doc_type)` à la fois sans jamais casser les autres.
- **`carbongpt/core/doc_exporter.py::_resolve_template_path(standard,
  doc_type)`** — même principe : vérifier d'abord
  `document_template_versions.local_path` pour la version applicable
  (T5), replier sur `TEMPLATE_FILES` si absent.

Ne pas toucher à `_match_gs_title_to_sid` ni aux autres fonctions de
`doc_exporter.py` dans cette spec — elles continuent de fonctionner par
correspondance de titre. Les remplacer par la position exacte capturée en
T3 est une amélioration de fidélité pour une spec ultérieure, pas une
condition pour que celle-ci fonctionne.

### T7 — Amorçage : VPA-DD Gold Standard v3.0

1. Ingérer la page de template VPA-DD (T2), confirmer que v3.0 est bien
   détectée avec sa date (15.05.2026)
2. Télécharger le `.docx` v3.0, l'analyser (T3+T4), vérifier que les 27
   sous-sections A–F sont retrouvées avec le même découpage que
   `gs_vpa_dd_v2_3.py` (sert de vérification croisée) et que les 116 items
   Safeguarding sont désormais couverts
3. Basculer `GUIDE_REGISTRY[("GoldStandard", "VPA-DD")]` via l'adaptateur
   T6 ; laisser les sept autres entrées de `GUIDE_REGISTRY` inchangées
4. Vérifier par un essai réel que `generate_full_document` et
   `doc_exporter` produisent un document basé sur v3.0 sans qu'une ligne de
   ces deux modules n'ait changé

### T8 — Fusion de la méthodologie dupliquée (`GS-TPDDTEC` / `407`)

Trouvé en reconnaissance (03.08.2026) : deux lignes dans `methodologies`
pour la même méthodologie réelle — `GS-TPDDTEC` (`applicability` renseigné,
jamais référencée par le reste du système) et `407` (`applicability` et
`sector` NULL, celle que `methodology_version_history`,
`regulatory_value_preferences` et tout le moteur SPEC-03 utilisent
réellement). Nécessaire pour cette spec car un futur moteur de sélection
(point 3 de la reconnaissance, hors périmètre ici mais qui lira
`methodologies.applicability`) trouverait sinon la mauvaise ligne.

Procédure, à exécuter uniquement au moment de l'implémentation (pas dans
cette spec) :

1. Auditer toute table référençant `methodologies.id` — vérifier
   qu'aucune ligne ne pointe vers l'id de `GS-TPDDTEC` (attendu : aucune,
   à confirmer, jamais supprimer sans avoir vérifié — R5)
2. Copier les champs non NULL de `GS-TPDDTEC` (`applicability`, et tout
   autre champ renseigné que `407` n'a pas) dans la ligne `407`
3. Une fois copié et vérifié sans référence orpheline, marquer
   `GS-TPDDTEC` comme fusionnée (`status = 'merged'`, `superseded_by =
   '407'`) plutôt que la supprimer immédiatement — cohérent avec la
   discipline R4 (tout est versionné et daté, pas de suppression sèche)
4. Documenter dans `docs/DECISIONS.md` au moment de l'exécution

### T9 — Détection de nouvelles versions de templates

`check_for_template_updates(standard=None, doc_type=None)` — même esprit
que le T6 de SPEC-01 et le T6 de SPEC-02 : re-parse les pages ingérées,
compare à `document_template_versions`, retourne la liste des nouveautés.
Ne télécharge ni n'analyse rien automatiquement.

---

## Tests exigés

- Parsing de la structure sur le VPA-DD v2.3 (fixture déjà disponible dans
  `document_repository/`) → 18 tableaux détectés, `field_type` correct par
  tableau (`parameter_block` pour les tableaux 7 et 9, `checklist_item` ×
  116 pour le tableau 14, `checkbox` pour les tableaux 0 et 1)
- Idempotence : deux analyses successives du même fichier ne créent pas de
  doublon de `template_fields`
- `resolve_applicable_template('GoldStandard', 'VPA-DD', at_date=...)` →
  version correcte en mode succession
- `resolve_applicable_template('Verra', 'VCS-PD', project_start_date=
  '2027-02-01')` → v5.0B ; `project_start_date='2026-06-01'` → v5.0A ;
  absence de `project_start_date` en mode double piste → erreur explicite
- `load_guide()` : pour un couple migré, l'objet retourné expose
  `.SUBSECTIONS` de même forme que les modules Python actuels — test que
  `generate_full_document()` s'exécute sans modification contre les deux
  sources (Python et DB-backed)
- Fusion T8 : audit préalable confirme zéro référence orpheline avant toute
  modification
- `check_for_template_updates()` détecte une version présente dans une
  fixture mais absente de la base, sans rien télécharger

---

## Livrables

1. Migration de schéma additive (`document_templates`,
   `document_template_versions`, `template_fields`)
2. `gs_template_ingest.py`, `template_docx_parser.py` + tests + fixtures
   (`verra_template_ingest.py` si T0 confirme une structure exploitable)
3. Adaptateur `load_guide()` et `_resolve_template_path()` rétrocompatibles
4. VPA-DD Gold Standard v3.0 ingéré, analysé, et branché en production —
   preuve de concept du patron complet
5. Fusion `GS-TPDDTEC` / `407` exécutée et documentée dans
   `docs/DECISIONS.md`
6. `docs/STATUS.md` mis à jour

---

## Critère d'acceptation

Depuis la base actuelle, une seule commande ingère et analyse le VPA-DD
Gold Standard v3.0. `generate_full_document('GoldStandard', 'VPA-DD', ...)`
et `doc_exporter` produisent un document basé sur ce v3.0 — annexe
Safeguarding (116 questions) comprise pour la première fois — sans qu'une
seule ligne de ces deux modules n'ait été modifiée. Les sept autres
couples (standard, doc_type) continuent de fonctionner exactement comme
avant, sur leurs modules Python inchangés. Le système sait dire qu'un
template Verra v5.0B existe et n'est pas encore ingéré, sans planter et
sans supposer un template Validation+Vérification joint. La méthodologie
407 n'a plus de doublon en base.
