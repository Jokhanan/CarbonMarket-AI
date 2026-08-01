# SPEC-01 — Couche 0 : corpus réglementaire versionné

Statut : à implémenter
Créée le 30.07.2026
Prérequis : aucun
Bloque : toutes les autres specs

---

## Objectif

Le système doit savoir, pour toute méthodologie Gold Standard :

- quelles versions existent
- laquelle est en vigueur aujourd'hui
- à quelle date chacune est entrée en vigueur
- quels documents associés s'y rattachent (Rule Updates, Rule Clarifications,
  Deviations, documents liés)
- où se trouve le PDF de chacune, et l'avoir en local

Et il doit obtenir tout cela **automatiquement**, sans téléchargement manuel.

---

## Constat de départ (vérifié le 30.07.2026)

`globalgoals.goldstandard.org` n'est **pas** protégé par Cloudflare. Le blocage
documenté dans `carbongpt/repository/pack_builder.py` concerne l'Assurance
Platform (documents des projets), pas le site des standards.

La page d'une méthodologie contient un tableau `REVISION HISTORY` structuré,
avec une ligne par version : numéro, date de publication, nom du document, URL
PDF directe. Elle contient également une section `RELATED DOCUMENTS`.

Exemple de référence — RECH (méthodologie 407) :

`https://globalgoals.goldstandard.org/407_paa-m400-08_reduced-emission-from-cooking-and-heating/`

| Version | Date publiée | Note |
|---|---|---|
| v5.0 | 05.05.2026 | Document courant, aligné Paris |
| v4.0 | 07.10.2021 | TPDDTEC |
| v3.1 | 25.08.2017 | |
| v3.0 | 10.07.2017 | |
| v2.0 | 24.04.2015 | |
| v1.0 | 11.04.2011 | |

Plus : Rule Update 27.10.2020, Rule Update 03.05.2021, Rule Clarification
06.07.2020, et un document lié (Cookstove Usage Rate Guidelines v2.0).

PDF de la version courante :
`https://globalgoals.goldstandard.org/standards/407_v5.0_PAA-M400-08_Reduced-Emission-from-Cooking-and-Heating.pdf`

Pages d'index de même structure à exploiter :
`/all-documents/`, `/rule-updates/`, `/rule-clarifications/`, `/deviations/`,
`/clarification-requests/`, `/paris-agreement-alignment-documents/`

---

## Périmètre

### Dans le périmètre

1. Modèle de données pour méthodologies, versions, documents associés
2. Ingestion automatique depuis `globalgoals.goldstandard.org`
3. Téléchargement et stockage des PDF, dédupliqués
4. Résolution de la version applicable à une date donnée
5. Migration des constantes de `gs_rech_v5.py` vers des données sourcées
6. Détection des changements lors d'une ré-exécution (nouvelle version publiée)

### Hors périmètre

- Extraction des règles depuis le texte des PDF → SPEC-02
- Documents des projets tiers (PDD, MR) → spec ultérieure, problème Cloudflare
  distinct
- Verra, CDM, autres standards → après validation sur Gold Standard
- Toute modification du frontend

---

## Travaux

### T1 — Modèle de données

Créer les tables (migration additive, ne pas casser les 41 existantes) :

**`methodologies`** — identité stable
`id`, `standard` (GoldStandard), `code` (407), `name`, `short_name` (RECH),
`former_name` (TPDDTEC), `source_url`, `last_checked_at`

**`methodology_versions`** — une ligne par version
`id`, `methodology_id`, `version` (5.0), `released_date`, `effective_from`,
`effective_until` (nullable), `is_current` (bool), `paris_aligned` (bool),
`document_name`, `pdf_url`, `local_path`, `sha256`, `ingested_at`

**`methodology_related_documents`** — Rule Updates, RC, Deviations, docs liés
`id`, `methodology_id`, `version_id` (nullable), `doc_type` (enum :
rule_update, rule_clarification, deviation, clarification_request,
related_document), `title`, `released_date`, `pdf_url`, `local_path`, `sha256`

**`regulatory_values`** — toute constante réglementaire, avec sa source
`id`, `version_id`, `key` (ex. `EF_CO2.charcoal`), `value`, `unit`,
`applicability` (JSON : combustible, technologie, pays…), `section_ref`,
`page_ref` (nullable), `extraction_method` (enum : manual, llm_extracted,
llm_unverified), `verified_by` (nullable), `verified_at` (nullable), `notes`

Contrainte : aucune ligne de `regulatory_values` sans `version_id` et
`section_ref`. Les valeurs non vérifiées portent `extraction_method =
llm_unverified` et ne doivent jamais être consommées silencieusement par un
calcul (voir T5).

### T2 — Ingestion

Module `carbongpt/repository/gs_ingest.py`.

- `fetch_methodology_page(url)` → HTML
- `parse_revision_history(html)` → liste de versions structurées
- `parse_related_documents(html)` → liste de documents associés
- `download_document(pdf_url)` → fichier local + sha256, idempotent (ne
  retélécharge pas si le sha correspond)
- `ingest_methodology(url)` → orchestration, écrit en base

Exigences :

- User-Agent réaliste, timeout, retry avec backoff exponentiel
- Idempotent : relancer ne duplique rien
- Si le parsing échoue, lever une erreur explicite — **jamais de dégradation
  silencieuse**
- Le HTML de Gold Standard peut changer : isoler le parsing dans des fonctions
  testables sur des fixtures HTML sauvegardées

### T3 — Amorçage sur RECH

Ingérer la méthodologie 407 complète : les 6 versions, les 2 Rule Updates, la
Rule Clarification, le document lié. Vérifier que le PDF de la v5.0 est bien
présent en local et lisible.

### T4 — Résolution de version

`resolve_applicable_version(methodology_code, at_date)` → version applicable.

Doit gérer explicitement le cas RECH : un projet validé sous v4.0 dont les
émissions de millésime 2026 exigent une version alignée Paris. La fonction
retourne la version applicable **et** un indicateur de transition requise, avec
sa justification.

### T5 — Reprise des constantes de `gs_rech_v5.py`

`carbongpt/core/gs_rech_v5.py` contient des constantes réglementaires en dur,
écrites sans le document source (le PDF n'était pas dans le projet) :

| Constante | Valeur en dur | Source déclarée |
|---|---|---|
| `_NCV` bois / charbon | 0.0156 / 0.0295 TJ/t | aucune |
| `_EF_CO2` bois / charbon | 112.0 / 165.22 tCO2/TJ | « Annexe 2 » |
| `_EF_NONCO2` bois / charbon | 9.46 / 44.83 tCO2e/TJ | « Annexe 2 » |
| `_PCAP` bois / charbon | 1.25 / 0.40 t/cap/an | « §8.2 » |
| `fNRB` défaut | 0.75 | aucune |
| `DAF` défaut | 0.025 | « GS Tool 05 » |
| `embodied` | 0.017 tCO2e/unité | « défaut GS » |
| leakage marché | 5 % | aucune |

Incohérence connue : `er_simulator.py` plafonne l'EF CO2 charbon TPDDTEC à
197.15, tandis que `gs_rech_v5.py` utilise 165.22. Impossible de trancher sans
le document.

Travail attendu :

1. Une fois le PDF v5.0 ingéré, extraire chaque valeur avec sa référence de
   section exacte, et écrire dans `regulatory_values`
2. Comparer aux constantes en dur ; **produire un rapport d'écarts** dans
   `docs/RECH-V5-VALUE-AUDIT.md`
3. Ne rien corriger automatiquement. Le rapport est soumis à l'utilisateur, qui
   est l'expert métier et tranche.
4. Modifier `gs_rech_v5.py` pour lire depuis `regulatory_values` au lieu des
   constantes. Si une valeur est absente ou `llm_unverified`, lever une erreur
   explicite plutôt que d'utiliser un défaut.

**Point d'attention signalé par l'utilisateur** : il n'existe pas *un* facteur
d'émission du charbon. Il en existe plusieurs selon que les émissions de
carbonisation sont incluses, selon le rendement de meule, le ratio de conversion
bois→charbon, et selon que la source est un défaut IPCC, une valeur nationale ou
une mesure de terrain. Le modèle `regulatory_values` doit donc pouvoir stocker
**plusieurs lignes pour la même clé**, différenciées par leur champ
`applicability`. Ne pas écraser, ne pas choisir arbitrairement.

### T6 — Détection de changement

`check_for_updates()` : re-parse les pages ingérées, compare aux versions en
base, retourne la liste des nouveautés. Ne télécharge pas automatiquement.

### T7 — Endpoints

- `GET /api/methodologies` — liste avec version courante
- `GET /api/methodologies/{code}/versions` — historique
- `POST /api/methodologies/ingest` — déclenche une ingestion
- `GET /api/methodologies/{code}/resolve?date=YYYY-MM-DD` — version applicable
- `GET /api/methodologies/check-updates` — nouveautés détectées

---

## Tests exigés

- Parsing de la revision history sur une fixture HTML RECH sauvegardée →
  6 versions, dates exactes
- Parsing des documents associés → 2 Rule Updates, 1 Rule Clarification
- Idempotence : deux ingestions successives ne créent pas de doublon
- `resolve_applicable_version('407', '2021-06-01')` → v3.1
- `resolve_applicable_version('407', '2026-07-01')` → v5.0
- `regulatory_values` accepte plusieurs lignes pour la même clé avec des
  `applicability` différentes
- Un calcul qui consomme une valeur `llm_unverified` lève une erreur

Rappel : les 3 tests actuellement en échec (`test_ai_review.py`,
`test_registry.py`) doivent être corrigés avant de commencer.

---

## Livrables

1. Migration de schéma
2. `carbongpt/repository/gs_ingest.py` + tests + fixtures HTML
3. Corpus RECH complet ingéré et vérifiable en base
4. `docs/RECH-V5-VALUE-AUDIT.md` — le rapport d'écarts, à soumettre à
   l'utilisateur
5. `gs_rech_v5.py` migré vers des valeurs sourcées
6. `docs/STATUS.md` mis à jour

---

## Critère d'acceptation

Depuis une base vide, une seule commande ingère l'intégralité du corpus RECH.
Le système sait dire quelle version s'applique à une date donnée. Et le rapport
d'écarts permet à l'utilisateur de statuer, valeur par valeur, sur ce que le
code calculait jusqu'ici sans source.
