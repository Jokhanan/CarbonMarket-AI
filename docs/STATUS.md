# STATUS.md — État du projet

Dernière mise à jour : 01.08.2026

---

## SPEC-01 — Corpus réglementaire versionné

**Statut : implémentée, sauf T5.4.**

- **T1 (schéma)** : fait. Migration additive — `methodologies` et
  `methodology_version_history` étendues (nouvelles colonnes nullable
  uniquement), `documents` étendue (3 nouvelles catégories, lien vers une
  version de méthodologie, hash), `regulatory_values` créée. Aucune donnée
  existante supprimée ni modifiée ; sauvegarde complète prise avant migration
  (`~/db_backups/carbongpt_pre_spec01_*.dump`, WSL). Voir
  [docs/DECISIONS.md](DECISIONS.md) pour la justification d'étendre plutôt
  que dupliquer.
- **T2 (ingestion)** : fait. `carbongpt/repository/gs_ingest.py` —
  `fetch_methodology_page`, `parse_revision_history`,
  `parse_related_documents`, `download_document`, `ingest_methodology`,
  `resolve_applicable_version`, `check_for_updates`, `get_regulatory_value`.
  Idempotent (vérifié par test et manuellement). User-Agent réaliste, retry
  avec backoff exponentiel.
- **T3 (amorçage RECH)** : fait. Méthodologie 407 (RECH) entièrement
  ingérée : 6 versions, 2 Rule Updates, 1 Rule Clarification, 1 document lié
  (Cookstove Usage Rate Guidelines). PDF v5.0 vérifié présent et lisible
  (97 pages, `pdfplumber`).
- **T4 (résolution de version)** : fait. `resolve_applicable_version()`,
  testée. **Écart avec l'exemple de la spec** : `resolve_applicable_version
  ('407', '2026-07-01')` retourne **v4.0**, pas v5.0 comme l'exemple original
  de SPEC-01 le supposait — le PDF précise que l'entrée en vigueur a lieu 90
  jours après la publication (05.05.2026 + 90j = 03.08.2026). J'ai fait
  confiance au texte primaire plutôt qu'à l'hypothèse de la spec ; à
  confirmer avec l'utilisateur.
- **T5 (audit des valeurs)** : fait pour les parties 1-3 (extraction,
  écriture en base, rapport). Voir
  [docs/RECH-V5-VALUE-AUDIT.md](RECH-V5-VALUE-AUDIT.md) — **livrable
  principal de cette passe**. 18 lignes dans `regulatory_values` (16
  `llm_extracted`, 2 `llm_unverified`), aucune `verified_by`/`verified_at`.
  **T5.4 (migrer `gs_rech_v5.py` pour lire depuis `regulatory_values`) n'est
  volontairement pas fait** — en attente de l'arbitrage de l'utilisateur sur
  les écarts constatés (EF CO2/non-CO2 charbon, fNRB, leakage marché), pour
  ne pas reconnecter le moteur de calcul à des valeurs non validées.
- **T6 (détection de changement)** : fait. `check_for_updates()`, testable,
  ne télécharge rien automatiquement.
- **T7 (endpoints)** : fait. `carbongpt/app/methodology_routes.py`, monté
  sur `/methodologies` (accessible via `/api/methodologies/...` à travers le
  proxy Express) : liste, historique de versions, déclenchement d'ingestion,
  résolution de version, détection de nouveautés.
- **Tests** : `carbongpt/tests/test_gs_ingest.py`, 16 tests. Les tests de
  parsing tournent sur une fixture HTML sauvegardée
  (`carbongpt/tests/fixtures/rech_407_page.html`), sans réseau. Les tests
  dépendant de la base s'ignorent proprement (`SKIPPED`) si `DATABASE_URL`
  n'est pas défini ou si RECH n'a pas encore été ingéré — la suite reste
  exécutable sans base de données.

**Mise à jour du 01.08.2026** : fNRB retiré de `regulatory_values` (n'est
structurellement pas une valeur fixe dans RECH v5.0, voir
[docs/DECISIONS.md](DECISIONS.md)) — 17 lignes restantes, 15
`llm_extracted`, 1 `llm_unverified` (DAF). Citation exacte de l'entrée en
vigueur vérifiée : §3.3.1, page 12.

**Suite complète (SPEC-01 seule)** : 149 tests passent.

**Travail de suite identifié, non fait** :
1. Trancher les écarts du rapport d'audit, valeur par valeur.
2. Une fois les valeurs tranchées : migrer `gs_rech_v5.py` vers
   `regulatory_values` (T5.4).
3. Décider si la branche d'amortissement sur 5 ans des embodied emissions
   (Eq.19 du PDF, absente du code actuel) doit être implémentée.

---

## SPEC-02 — Sources de données externes indexées par pays

**Statut : spec écrite et vérifiée (T0), rien implémenté — décision
volontaire de l'utilisateur (01.08.2026) : d'abord valider le design de
SPEC-03 sur un seul paramètre déjà en base avant d'investir dans
l'ingestion.**

T0 (vérification de disponibilité, préalable à tout code) fait : Tool 05
exploitable (PDF structuré, 188 pays, Ghana et Burkina Faso confirmés
présents) ; outil A6.4 fNRB bloqué par une protection anti-bot sur
unfccc.int (à traiter par téléchargement manuel, pas d'automatisation dans
l'immédiat) ; MoFuSS exploitable mais seulement en PDF (pas de CSV/API),
tableaux par pays confirmés (Ghana, Burkina Faso) ; liste des Pays les Moins
Avancés très simple (44 pays, texte plat, UN DESA). Détail dans
[docs/SPEC-02.md](SPEC-02.md).

---

## SPEC-03 — Moteur de résolution de paramètres (Couche 3)

**Statut : tranche fine implémentée et démontrée sur un projet réel, limitée
à `EF_CO2`/`EF_nonCO2` (charbon).**

- Faille corrigée avant implémentation : `regulatory_values` (SPEC-01)
  n'avait aucun champ pour stocker une hiérarchie de préférence entre
  valeurs candidates. Ajout de `regulatory_value_preferences` (T2), avec la
  même discipline de traçabilité que `regulatory_values`
  (`extraction_method`/`verified_by`/`verified_at`).
- Schéma complet appliqué (migration additive) : `project_parameters`
  étendue, `regulatory_value_preferences`, `project_parameter_alternatives`
  (contrainte au niveau base : un candidat non retenu doit avoir un motif —
  `CHECK (is_selected OR rejection_reason IS NOT NULL)`), `project_open_questions`.
- `carbongpt/repository/parameter_resolver.py` : `resolve_parameter()`,
  `answer_question()`, `override_parameter()`. **Limité par construction à
  `EF_CO2`/`EF_nonCO2`** — toute autre clé lève une erreur explicite plutôt
  que de deviner.
- **STUB explicitement signalé dans le code** : la classification région
  (Afrique subsaharienne/PMA vs industrialisé) n'est pas SPEC-02 — un
  dictionnaire minimal couvre seulement Ghana et Burkina Faso, pour les
  tests et la démonstration. Pas un vrai jeu de données ingéré.
- 12 règles de préférence insérées pour `EF_CO2`/`EF_nonCO2`, sourcées de
  RECH v5.0 §2 (définition WCCF, page 7), deux contextes (Afrique
  subsaharienne/PMA, industrialisé), 3 candidats chacun.
- **Démontré sur le projet réel `user_projects.id=12` (« Gh »,
  méthodologie TPDDTEC/RECH)** — voir la conversation du 01.08.2026 pour la
  trace complète : question posée → réponse → valeur proposée (355.36
  tCO2/TJ) → 2 alternatives écartées avec motif → argument de défendabilité
  citant §2, page 7 → `override_parameter()` avec conservation de la
  proposition initiale → `resolve_parameter()` confirmé sans écraser
  l'override.
  **Anomalie de données trouvée en cours de route, non corrigée** : la
  fiche du projet a `country = 'Afghanistan'` alors que son nom (« Gh ») et
  sa méthodologie suggèrent fortement le Ghana. Signalée, pas corrigée sans
  confirmation.
- Tests : `carbongpt/tests/test_parameter_resolver.py`, 9 tests, contre un
  projet jetable créé et détruit par test (jamais le portefeuille réel).

**Suite complète (SPEC-01 + SPEC-03)** : 158 tests passent.

**Travail de suite identifié, non fait** :
1. Valider le design sur ce seul paramètre avant d'étendre.
2. Implémenter SPEC-02 (au moins Tool 05 et la classification PMA/SSA, les
   deux sources faciles) pour remplacer le stub de classification région.
3. Étendre `resolve_parameter()` aux autres paramètres de RECH (NCV, PCAP,
   embodied, leakage marché — chacun a besoin de sa propre hiérarchie dans
   `regulatory_value_preferences`).
4. Corriger (ou faire corriger) le champ pays du projet `id=12`.

---

## Environnement local

Développement dans WSL (Ubuntu 26.04) — voir CLAUDE.md §5. PostgreSQL 18 +
pgvector installés via apt. `./start_local.sh` lance backend + frontend.
