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

---

## 2026-08-01 — fNRB retiré de `regulatory_values` ; résultats RECH v5.0 antérieurs non fiables

**Constat** : `docs/RECH-V5-VALUE-AUDIT.md` a d'abord enregistré une ligne
`fNRB_default` avec `extraction_method='llm_unverified'` (aucune valeur
trouvée dans le PDF v5.0). Après relecture, cette ligne elle-même n'a pas de
sens dans `regulatory_values` : la table est faite pour des **valeurs**
(même non vérifiées) rattachées à une `section_ref` précise ; or fNRB n'a
tout simplement **pas de valeur fixe à chercher** dans RECH v5.0. Le texte
renvoie explicitement à un paramètre suivi/dérivé (« ICS 20 »), obtenu via
MoFuSS ou l'outil fNRB A6.4 (MEP012-A04), spécifique au pays et à la source
de biomasse — voir §4.1.2.3(b), page 13, et §14.2 (ICS 20). Une ligne
`llm_unverified` laissait croire qu'il existait quelque chose à vérifier un
jour ; ce n'est pas le cas, c'est une dépendance externe (voir
`docs/SPEC-02.md`), pas une valeur en attente.

**Décision** : la ligne `fNRB_default` a été supprimée de `regulatory_values`
(`DELETE FROM regulatory_values WHERE key='fNRB_default'`). L'absence de
fNRB dans RECH v5.0 reste documentée dans `docs/RECH-V5-VALUE-AUDIT.md` et
ci-dessous — ce n'est pas une donnée manquante à sourcer plus tard dans
`regulatory_values`, c'est une dépendance à une autre source de données par
pays, hors du périmètre de SPEC-01.

**Tout résultat RECH v5.0 produit par `gs_rech_v5.py` avant cet audit
(30.07.2026–01.08.2026) doit être considéré comme non fiable.** Quatre des
constantes qu'il utilise n'ont aucune source retrouvée dans le texte de la
méthodologie :

1. **EF CO2 charbon = 165.22 tCO2/TJ** — absent du texte ; le PDF donne trois
   valeurs légitimes selon l'applicabilité (112 / 355.36 / 236.91 tCO2/TJ),
   aucune n'est 165.22.
2. **EF non-CO2 charbon = 44.83 tCO2/TJ** — absent du texte ; valeurs
   légitimes : 5.87 / 89.68 / 61.74 tCO2/TJ.
3. **fNRB par défaut = 0.75** — n'est structurellement pas une constante de
   cette méthodologie (voir ci-dessus).
4. **Leakage marché = 5% (0.05)**, appliqué sans condition — la seule valeur
   par défaut du texte est 2% (0.02), et elle est conditionnelle (une option
   sur trois, §9.3.2.2).

`gs_rech_v5.py` n'a pas été modifié à ce stade (décision de l'utilisateur du
01.08.2026 : ne pas reconnecter le moteur de calcul tant que les écarts ne
sont pas tranchés). Tant que ce n'est pas fait, tout chiffre RECH v5.0 déjà
produit — dans un PDD, un classeur Excel, ou ailleurs — s'appuie sur ces
quatre valeurs non sourcées et doit être retraité une fois les vraies
valeurs tranchées.
