# DECISIONS.md — Journal des décisions d'architecture

Ce fichier trace les décisions prises en cours de route, avec leur justification.
Voir CLAUDE.md §3.

---

## 2026-08-01 — RECH n'existe dans aucune table : c'est la justification de SPEC-01

**Constat** : avant l'implémentation de SPEC-01, la méthodologie RECH (Gold
Standard, code 407, `PAA-M400-08 Reduced Emission from Cooking and Heating`)
n'existait **nulle part** dans la base de données restaurée (8913 projets,
195 méthodologies, 1224 findings) :

- absente de `methodologies` (aucune ligne dont le code ou le nom correspond)
- absente de `ref_methodologies`
- absente de `methodology_version_history` (table vide, 0 ligne, jamais utilisée)
- absente de `methodology_knowledge`, `methodology_parsed`, `methodology_structure`

Pourtant, `carbongpt/core/gs_rech_v5.py` calcule déjà des réductions d'émissions
RECH v5.0 en production, avec des constantes réglementaires écrites en dur dans
le code Python (facteurs d'émission, NCV, plafonds per-capita, fNRB, DAF...),
sans document source déclaré pour la plupart d'entre elles.

**Conséquence** : le système produit aujourd'hui des chiffres réglementaires
pour RECH sans que personne — ni la base, ni le code — ne puisse dire d'où ils
viennent. C'est exactement le problème que SPEC-01 (corpus réglementaire
versionné) et son sous-livrable `RECH-V5-VALUE-AUDIT.md` sont censés résoudre :
sourcer chaque valeur, ou la marquer explicitement comme non sourcée.

**Décision** : implémenter SPEC-01 en priorité sur RECH, conformément au choix
déjà acté dans `docs/ARCHITECTURE.md` ("Stratégie de mise en œuvre").

---

## 2026-08-01 — Étendre les tables existantes plutôt qu'en créer de nouvelles

**Constat** : une partie du schéma que SPEC-01 (T1) proposait de créer existait
déjà, à moitié construite et inutilisée :

| Table proposée par SPEC-01 | Existant réutilisé |
|---|---|
| `methodologies` | `methodologies` (195 lignes) — déjà quasi identique |
| `methodology_versions` | `methodology_version_history` (0 ligne, jamais peuplée) |
| `methodology_related_documents` | `documents` — catégorie `rule_update` déjà présente |

Seule `regulatory_values` n'avait aucun équivalent : `methodology_knowledge`
existe, mais stocke des blocs de texte libres pour la recherche RAG (IA), pas
des constantes typées avec source, section et statut de vérification.

**Décision** (validée par l'utilisateur le 2026-08-01) : migration additive
qui étend les 3 tables existantes (nouvelles colonnes nullable uniquement,
aucune colonne supprimée, aucune donnée modifiée) et crée uniquement
`regulatory_values`. Conforme à la règle R1 de CLAUDE.md (les règles métier
sont des données) et évite de dupliquer une infrastructure déjà à moitié
construite. Sauvegarde complète de la base effectuée avant la migration
(`~/db_backups/carbongpt_pre_spec01_*.dump`).
