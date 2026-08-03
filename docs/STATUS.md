# STATUS.md — État du projet

Dernière mise à jour : 03.08.2026

---

## État du projet — synthèse pour reprise

Cette section résume l'état réel du dépôt pour quelqu'un qui reprendrait le
projet sans avoir suivi les sessions précédentes. Le détail complet,
spec par spec et tour par tour, est plus bas dans ce document ; c'est la
trace de référence en cas de doute sur un choix ou un chiffre.

### Ce qui fonctionne, de bout en bout, aujourd'hui

- **Corpus réglementaire versionné (SPEC-01)** : méthodologie RECH v5.0
  (Gold Standard 407) entièrement ingérée — 6 versions, historique complet,
  17 valeurs réglementaires sourcées en base (`regulatory_values`),
  résolution de version applicable testée. Le moteur de calcul lui-même
  (`gs_rech_v5.py`) n'est PAS encore branché sur ces valeurs (voir plus
  bas).
- **Templates officiels ingérés et analysés (SPEC-05 T0-T3, T6, T7)** :
  VPA-DD Gold Standard v3.0 ingéré (7 versions historiques), décomposé en
  161 champs typés et positionnés en base (`template_fields`). 7 documents
  transversaux Gold Standard ingérés et versionnés (101, 102, 103, 104,
  118, 119, 201) (SPEC-06 T2). `load_guide()` sert désormais la structure
  v3.0 issue de la base pour `("GoldStandard", "VPA-DD")`, avec repli
  automatique et vérifié sur le guide Python pour les 7 autres couples
  standard/document si la base est indisponible — rien n'est cassé.
- **Export Word** : les cases à cocher modernes du v3.0 (contrôles de
  contenu `w:sdt`/`w14:checkbox`, 479 dans ce fichier) se cochent
  correctement à l'export, en plus du mécanisme hérité — les deux
  fichiers réels (v2.3 et v3.0) vérifiés directement, aucun des deux
  n'utilisait le mécanisme hérité seul.
- **Paramètres RECH extraits et instanciés (SPEC-06 T1/T3/T5)** : les 26
  paramètres réels de RECH v5.0 extraits du PDF source, tracés section +
  page, classés ex ante/monitoring (18 instances patron ex ante, 9 patron
  monitoring, fNRB dans les deux — jamais tranché automatiquement). Patron
  SDG (T55) correctement remonté comme non couvert par RECH, pas deviné.
- **Traçabilité champ ↔ source (SPEC-06 T4)** : chacune des 9 sections de
  niveau 1 du VPA-DD v3.0 est reliée à sa source réelle (méthodologie ou
  document transversal précis) ; les deux sections sans aucune source
  (« Contact information of CME », « LUF additional information ») sont
  identifiées mécaniquement, pas devinées.
- **Faits non déductibles catalogués (SPEC-06 T6)** : 5 catégories
  documentées, démontrées sur le projet réel `id=12` (5 questions ouvertes
  créées).
- **Rédaction sourcée et validée, démontrée sur données réelles** : deux
  pipelines de génération IA partagent la même discipline anti-
  hallucination (jeu de faits fermé + validateur mécanique qui rejette
  tout nombre, référence de section, ou nom de méthodologie/outil/norme
  absent des faits fournis) :
  - `defendability.py` (SPEC-04) — argument de défendabilité, démontré
    avec un vrai appel API sur `EF_CO2`/`EF_nonCO2` (charbon), projet 12.
  - `parameter_block_drafting.py` (SPEC-06, intégré à
    `generate_section_draft()`) — bloc de paramètre de template, démontré
    sur le projet 12 avec deux paramètres réels (ICS 17 ex ante, ICS 22
    monitoring). Résultat honnête : ICS 22 directement utilisable ; ICS 17
    fidèle mais maladroit à cause d'une bizarrerie de rédaction du PDF
    source lui-même, pas d'une hallucination — le garde-fou a fonctionné
    comme prévu (préférer un texte fidèle mais imparfait à un texte propre
    mais faux).
- **Moteur de résolution de paramètre (SPEC-03)** : `resolve_parameter()`,
  `answer_question()`, `override_parameter()` démontrés sur le projet réel
  12 pour `EF_CO2`/`EF_nonCO2` — volontairement limité à ces deux clés.
- **265/265 tests passent** (suite complète, dernière exécution
  03.08.2026). Diff Git vide vérifié à chaque tour sur les fichiers
  protégés (`carbongpt/guides/*.py`, `ai_writer.py`, `doc_exporter.py`)
  quand la spec ne les touchait pas explicitement.

### Ce qui reste ouvert (par domaine)

- **SPEC-01 T5.4** : `gs_rech_v5.py` (moteur de calcul) n'est toujours pas
  migré pour lire `regulatory_values` — en attente d'arbitrage utilisateur
  sur les écarts constatés dans l'audit (EF CO2/non-CO2 charbon, fNRB,
  leakage marché).
- **SPEC-02** (sources de données externes par pays) : design vérifié
  seulement (T0) ; rien implémenté, décision volontaire d'attendre.
- **SPEC-03** : `resolve_parameter()` ne couvre que `EF_CO2`/`EF_nonCO2` ;
  la classification région (PMA/Afrique subsaharienne) reste un
  dictionnaire minimal (Ghana + Burkina Faso), pas SPEC-02.
- **SPEC-05 T4** (annexe Safeguarding v3.0), **T5** (résolution de version
  double piste Verra 5.0A/5.0B — schéma prêt, aucune logique), **T8**
  (fusion du doublon méthodologie GS-TPDDTEC/407 — audité, pas exécuté),
  **T9** (détection de nouvelles versions au-delà du déclenchement manuel).
- **Aucun résolveur générique projet → méthodologie** : le champ
  méthodologie d'un projet est du texte libre non fiable (le projet 12
  porte « TPDDTEC », pas « 407 ») ; `_draft_parameter_block()` a RECH v5.0
  codé en dur. Généraliser à d'autres méthodologies suppose de résoudre ce
  point d'abord.
- **Bruit d'extraction ICS 17** (« Choice of data or » dans
  `rech_parameter_extractor.py`) : compromis assumé, documenté, jamais
  nettoyé — repéré deux fois maintenant sans être traité.
- **Verra** : jamais réellement ingéré — seule la structure de page a été
  vérifiée pour les 7 documents transversaux Gold Standard ; aucun travail
  Verra n'a démarré dans tout cet arc SPEC-05/06.
- **SPEC-06 T4** : la traçabilité s'arrête aux 9 sections de niveau 1 et
  aux 3 patrons de bloc — pas encore aux 161 champs individuels du
  VPA-DD v3.0. « Appendices » (H303) mélange plusieurs sujets sous une
  seule référence à 101, imprécis.
- **Land-use & Forests (Activity Requirement 203)** non ingéré — hors
  périmètre RECH/cookstoves, mais bloquerait toute extension future vers
  des méthodologies forestières.

### Prochaines étapes, par ordre de priorité

1. **Étendre la rédaction sourcée aux sections prose du VPA-DD v3.0.**
   C'était l'objectif annoncé après SPEC-05 T6 : faire rédiger 2-3
   sections complètes, pas seulement des blocs de paramètres. Aujourd'hui
   seul `content_format == "parameter_blocks"` est routé vers un pipeline
   sourcé (`parameter_block_drafting.py`) ; les 101 champs `prose` du
   v3.0 passent encore par le prompt générique de `ai_writer.py`, qui n'a
   pas accès aux faits de `methodology_parameters`/
   `field_requirement_linking`/`non_deducible_facts` construits ce
   trimestre. C'est le point qui rapprocherait le plus vite le système
   d'un VPA-DD réellement rédigeable.
2. **Construire le résolveur projet → méthodologie**, aujourd'hui absent.
   Bloque à la fois l'extension au-delà de RECH v5.0 et la généralisation
   de `resolve_parameter()` à d'autres paramètres RECH (NCV, PCAP,
   embodied, leakage marché) — chacun a besoin de sa propre hiérarchie
   dans `regulatory_value_preferences`, comme fait pour le charbon en
   SPEC-03.
3. **Nettoyer l'artefact d'extraction ICS 17** (« Choice of data or ») —
   correctif ciblé et de faible risque dans
   `rech_parameter_extractor.py`, déjà documenté deux fois sans être
   traité.
4. **Reprendre SPEC-05 T4** (annexe Safeguarding) avec la structure réelle
   du v3.0 (27 lignes Principe/Sous-principe/Risques/Indicateurs), à
   concevoir de zéro plutôt qu'en reprenant le plan pensé pour les 339
   lignes du v2.3.

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
  **Anomalie de données trouvée en cours de route, corrigée le 01.08.2026
  sur confirmation explicite de l'utilisateur** : la fiche avait
  `country = 'Afghanistan'` ; c'est en réalité un projet au Ghana
  (`country = 'Ghana'`, `country_iso = 'GHA'`). Seule cette ligne a été
  corrigée — aucune autre donnée du projet n'a été touchée, et l'audit de
  cohérence pays sur l'ensemble du portefeuille (22 lignes sans
  `country_iso`, 2 sans `country`) n'a pas été corrigé sans accord.
- Tests : `carbongpt/tests/test_parameter_resolver.py`, 11 tests (9 SPEC-03
  + 2 SPEC-04 : repli gabarit, argument généré par IA), contre un projet
  jetable créé et détruit par test (jamais le portefeuille réel).

**Travail de suite identifié, non fait** :
1. Valider le design sur ce seul paramètre avant d'étendre.
2. Implémenter SPEC-02 (au moins Tool 05 et la classification PMA/SSA, les
   deux sources faciles) pour remplacer le stub de classification région.
3. Étendre `resolve_parameter()` aux autres paramètres de RECH (NCV, PCAP,
   embodied, leakage marché — chacun a besoin de sa propre hiérarchie dans
   `regulatory_value_preferences`).

---

## SPEC-04 — Argument de défendabilité généré par IA (Couche 4)

**Statut : implémentée sur le même périmètre que SPEC-03 (`EF_CO2`/`EF_nonCO2`,
charbon). Démontrée avec un vrai appel au modèle (clés en place le
01.08.2026) sur le projet réel `id=12` — voir plus bas.**

- Schéma (migration additive) : `project_parameters` gagne
  `defendability_argument_source` (`'ai_generated'` | `'template'`, défaut
  `'template'`), `defendability_argument_model`,
  `defendability_argument_generated_at`.
- `carbongpt/repository/defendability.py` (nouveau) : `build_fact_set()`
  assemble un jeu de faits fermé — uniquement la valeur retenue, sa source,
  le contexte projet, la réponse à la question ouverte, et les alternatives
  écartées avec leur motif — rien d'autre n'est visible du modèle (pas le
  PDF brut, pas de recherche web). `generate_defendability_argument()`
  appelle `openai_client.call_openai()` puis `validate_generated_argument()`,
  qui rejette mécaniquement tout nombre ou référence de section absent du
  jeu de faits.
  **Bug trouvé et corrigé avant la démo** : le contrôle de la page source
  ne pouvait jamais réussir — `page_ref` est stocké comme nombre nu dans le
  JSON (`"page_ref": "12"`), jamais sous la forme littérale « page 12 »,
  donc toute mention naturelle d'un numéro de page par le modèle aurait
  toujours été signalée à tort comme une hallucination. Corrigé en
  enregistrant explicitement cette forme attendue avant comparaison.
- `carbongpt/repository/parameter_resolver.py::resolve_parameter()` :
  tente la génération IA en premier ; en cas d'échec (clé absente, erreur
  réseau, argument rejeté par le validateur), repli automatique et
  silencieux-pour-l'utilisateur-final-mais-loggé sur le gabarit SPEC-03,
  `defendability_argument_source` posé à `'template'`. Jamais de crash côté
  appelant.
- **Bug bloquant trouvé en vérifiant les clés (call minimal réel)** :
  `claude-sonnet-5`/`claude-opus-5` rejettent le paramètre `temperature`
  purement et simplement (`400 — "temperature is deprecated for this
  model"`), envoyé sur tous les appels. Sans ce correctif, toute
  génération de texte du produit échouait dès qu'une vraie clé API était
  utilisée. Corrigé dans `openai_client.py` (`temperature` accepté dans
  les signatures pour compat, jamais envoyé au payload).
- **Faille du garde-fou trouvée et corrigée après une première démo** : le
  texte généré affirmait que le Ghana est une juridiction « Sub-Saharan
  Africa/LDC » — faux, le Ghana n'est pas un Pays Moins Avancé (le Burkina
  Faso l'est). Origine structurelle : le champ `applicability.region`
  d'une valeur candidate décrit la portée de la RÈGLE, sourcée de la
  méthodologie (« Sub-Saharan Africa or Least Developed Countries ») — ce
  n'est pas un fait sourcé sur le pays du projet. Le validateur ne
  vérifiait que les nombres et références de section, pas ce type
  d'affirmation relationnelle ; une simple présence de la phrase dans le
  JSON (vraie, mais pour la règle, pas pour le pays) l'aurait laissée
  passer. Corrigé par : (1) interdiction explicite dans la consigne
  système de toute classification de pays (LDC, PMA, Afrique
  subsaharienne, industrialisé, en développement) sous quelque forme que
  ce soit ; (2) `validate_generated_argument()` étendu pour rejeter
  mécaniquement toute occurrence de ces termes, sauf si un futur champ
  `project_context.country_classification` (alimenté par SPEC-02, non
  implémenté) l'autorise explicitement. En attendant SPEC-02, l'argument
  généré doit se limiter au nom du pays, sans qualificatif.
- **Deux défauts de registre corrigés** dans la consigne système : les
  codes internes (`default_permitted`) doivent être traduits en langage
  réglementaire, jamais imprimés tels quels ; l'argument expose un
  raisonnement, il ne dicte pas la conclusion du VVB (interdiction de
  formulations du type « the VVB should validate »).
- **Langue du livrable distincte de la langue de l'interface** : nouvelle
  colonne `user_projects.document_language` (migration additive, défaut
  `'en'` — Gold Standard et Verra exigent des soumissions en anglais).
  `generate_defendability_argument()` lit
  `project_context.document_language` et instruit le modèle en
  conséquence ; la langue de l'interface (français, pour cet utilisateur)
  n'a aucune influence sur celle du livrable.
- Démonstration charbon rejouée sur le projet réel `user_projects.id=12`
  (Ghana) avec de vraies clés API : argument généré par `claude-sonnet-5`,
  persisté (`defendability_argument_source='ai_generated'`), sans
  affirmation de classification, en anglais (défaut Gold Standard),
  jugé par l'utilisateur nettement supérieur au gabarit.
- Tests : 11 dans `carbongpt/tests/test_defendability.py` (jeu de faits,
  validateur nombre/section/classification, langue du livrable, délégation
  à `call_openai()`, clé manquante) + 2 dans `test_parameter_resolver.py`
  (repli gabarit, argument IA effectivement utilisé et persisté — avec
  `call_openai()` simulé, sans réseau).

**Suite complète (SPEC-01 + SPEC-03 + SPEC-04)** : 183 tests passent.

---

## SPEC-05 — Ingestion et analyse automatique des templates officiels

**Statut : T0-T3, T6 et T7 implémentés (03.08.2026) — VPA-DD Gold Standard
v3.0 ingéré, analysé, consultable en base, et maintenant réellement
branché à `generate_full_document()`/`doc_exporter.py` via l'adaptateur
T6. T4 (annexes/Safeguarding), T5 (résolution de version), T8 (fusion
méthodologie) et T9 (détection de nouvelles versions au-delà du strict
nécessaire) restent à faire — voir `docs/SPEC-05.md`. T4 mis de côté ce
tour-ci sur autorisation explicite de l'utilisateur, et parce que la
table Safeguarding du v3.0 (27 lignes, format Principe/Sous-principe/
Risques/Indicateurs) diffère structurellement de celle du v2.3 (339
lignes, 116 questions Oui/Non) que SPEC-05.md T4 avait initialement en
tête — à reconcevoir, pas juste reprendre le plan existant.**

Changement de cap après une reconnaissance sans code sur les cinq parcours
documentaires. Constat central : `carbongpt/guides/*.py` et
`doc_exporter.py::TEMPLATE_FILES` encodent à la main des templates vieux de
plusieurs années (anti-pattern R1) — Gold Standard a republié ses quatre
templates le même jour (15.05.2026), Verra est passé à VCS Version 5
(obligatoire après le 01.01.2027, remplace le template Validation+
Vérification joint par deux documents séparés).

**Ne casse rien — vérifié explicitement** : `carbongpt/guides/`,
`carbongpt/core/ai_writer.py` et `carbongpt/core/doc_exporter.py` ont un
diff Git vide après cette session. `load_guide('GoldStandard', 'VPA-DD')`
résout toujours vers `gs_vpa_dd_v2_3.py` (27 sous-sections), et
`doc_exporter._resolve_template_path` fonctionne toujours sur
`TEMPLATE_FILES`. Les nouvelles tables (`document_templates`,
`document_template_versions`, `template_fields`) existent à côté, lues par
personne d'autre que les nouveaux modules eux-mêmes.

**T0** : page GS confirmée exploitable (comme prévu), mais avec un piège
non anticipé — chaque `<tr>` de la table REVISION HISTORY d'une page de
*template* (contrairement aux pages de *méthodologie* que `gs_ingest.py`
sait déjà lire) n'est pas fermé (`</tr>` manquant). Le parser HTML standard
de Python interprète ça comme un imbrication littérale : un `find_all('td')`
naïf sur une ligne récupère aussi les cellules de toutes les lignes
suivantes. Corrigé en utilisant le parser `lxml` (déjà disponible), qui
ferme chaque `<tr>` au suivant comme le ferait un navigateur — confirmé
correct (17 lignes propres) contre la vraie page. `gs_ingest.py` n'est pas
touché, ses propres pages n'ont pas ce défaut.

**T1** : migration additive — `document_templates`,
`document_template_versions` (avec `project_start_before`/
`project_start_on_or_after`, pensés dès la conception pour le cas Verra
5.0A/5.0B), `template_fields` (`field_type` parmi prose/table/single_value/
checkbox/parameter_block/checklist_item/attachment, `position` JSONB avec
ancrage réel dans le document, `repeat_of` prévu pour T4). Sauvegarde
complète de la base prise avant migration (`db_backups/`, hors dépôt Git).

**T2** : `carbongpt/repository/gs_template_ingest.py` — même contrat que
`gs_ingest.py` (parsing isolé et testable, idempotent, erreur explicite).
Les 7 versions du VPA-DD (v1.0 à v3.0) ingérées et téléchargées, dédupliquées
par sha256.

**T3** : `carbongpt/repository/template_docx_parser.py` — analyse un
`.docx` en champs typés et positionnés (position = indices structurels
réels du document, jamais une heuristique de titre). Bug trouvé et corrigé
en écrivant les tests : la détection de case à cocher héritée de
`doc_exporter.py::_check_checkbox_in_cell` (champs de formulaire hérités
`w:ffData/w:checkBox`) ne détecte **aucune** des 479 cases à cocher réelles
du VPA-DD v3.0 — le nouveau template utilise des contrôles de contenu
modernes (`w:sdt`/`w14:checkbox`), un mécanisme entièrement différent.
Corrigé dans le nouveau parseur ; **`doc_exporter.py` lui-même n'a pas été
touché** (hors périmètre — mais signalé ici : le jour où l'export vers
v3.0 sera branché, `_check_checkbox_in_cell` ne saura pas cocher ces
cases-là sans son propre correctif).

**T7 — VPA-DD v3.0, résultat concret** : 161 champs extraits (101 prose,
38 checkbox, 18 table, 3 parameter_block, 1 single_value), contre 29 pour
v2.3 (11/8/5/3/2). Changements structurels majeurs entre v2.3 et v3.0 :
abandon complet du codage de section par lettre (A.1, B.6.2...) au profit
de vrais styles Word Heading 1/2/3 avec titres descriptifs (92
sous-sections niveau 2/3, contre 27 sous-sections A–F dans le guide
actuel) ; l'annexe Safeguarding passe de 339 lignes/116 questions
pré-écrites à 27 lignes dans un format d'évaluation de risque ouvert
(Principe/Sous-principe/Risques identifiés/Indicateurs de suivi, à
remplir par le porteur de projet plutôt que 116 réponses Oui/Non) ; les
blocs de paramètres de calcul passent de 2 formes (8 et 10 champs) à 3
formes plus riches (10, 18 et 13 champs, dont un nouveau bloc dédié aux
paramètres SDG/développement durable) ; nouvelles questions de diligence
Article 6.4/PACM en tête de document (cohérent avec le préfixe de nom de
fichier « PAA » — Paris Agreement Alignment) ; la section Genre est
passée d'un sous-point (D.2, ~1 sous-section) à une section majeure
complète (13 sous-sections).

Tests : `carbongpt/tests/test_gs_template_ingest.py` (9, fixture HTML
sauvegardée) et `carbongpt/tests/test_template_docx_parser.py` (9, contre
les vrais fichiers v2.3/v3.0 déjà dans `document_repository/`).

**T6 (03.08.2026)** : `carbongpt/guides/__init__.py::load_guide()` vérifie
maintenant d'abord si une version de template analysée existe en base
(`document_template_versions.parsed_at IS NOT NULL`) pour le couple
demandé ; si oui, un objet `_DbBackedGuide` construit à la volée depuis
`template_fields` est retourné, exposant exactement la même interface que
les modules Python (`.SUBSECTIONS`, `.get_subsections()`,
`.get_subsection()`, `.get_parent_sections()`,
`.get_subsections_for_parent()`) — vérifié champ par champ contre ce que
`ai_writer.py` et `ai_review.py` lisent réellement (certains accès sont
`dict[...]` directs, pas `.get(...)`, donc `title`/`parent_section`
doivent toujours être présents). Sinon, repli sur `GUIDE_REGISTRY` exactement
comme avant — vérifié en simulant une panne de base (```get_cursor```
monkeypatché pour lever une exception) : les 8 couples chargent toujours,
aucune erreur ne remonte à l'appelant.

Seul `("GoldStandard", "VPA-DD")` bascule aujourd'hui (161 sous-sections,
VPA-DD v3.0) ; les 7 autres couples restent sur leur module Python
inchangé (diff Git vide sur les 8 fichiers `carbongpt/guides/gs_*.py` /
`vcs_*.py` et sur `ai_writer.py`). Pour les blocs de paramètres (SPEC-05,
`field_type='parameter_block'`), l'adaptateur reconstruit un
`template_scaffold` en relisant les vrais libellés de colonnes du
`.docx` — un ajout concret au-delà de la simple compatibilité, utile pour
la session suivante.

**Case à cocher moderne — corrigé aussi ce tour-ci** :
`doc_exporter.py::_check_checkbox_in_cell` ne reconnaissait que le
mécanisme de formulaire hérité (`w:ffData/w:checkBox`, glyphes Wingdings).
**Constat plus large que prévu** : vérifié directement dans les deux
fichiers réels, ni le v2.3 (guide en production jusqu'ici) ni le v3.0
n'utilisent ce mécanisme — 0 `w:ffData` dans les deux, 495 et 479
cases à cocher modernes (`w:sdt`/`w14:checkbox`) respectivement. **La
case à cocher ne fonctionnait donc déjà pas avant cette session**, pas
seulement pour v3.0. Corrigé : `_check_checkbox_in_cell` reconnaît
maintenant les deux mécanismes — pour le moderne, bascule
`w14:checked/@w14:val` à `1` ET remplace le glyphe visible (`☐` U+2610 →
`☒` U+2612, lu dynamiquement depuis `w14:checkedState`, jamais supposé).
Vérifié par un test réel qui coche une case du v3.0 et du v2.3 et
confirme les deux changements. Note découverte au passage : v2.3 place
« Real case VPA » et « Regular VPA » dans deux paragraphes séparés (une
seule case cochée par appel) alors que v3.0 les met dans le même
paragraphe (les deux cases voisines cochées ensemble) — comportement du
code déjà existant, pas une régression, juste documenté par le test.

**Constat critique trouvé en testant la génération de bout en bout** :
`load_guide()` fonctionne, mais un essai réel de rédaction sur T37 (bloc
ex ante) du projet `id=12` a produit un texte qui **invente des détails
de méthodologie non sourcés** (« TPDDTEC Version 4.0 », « TOOL33
Version 03.0 », des équations non fournies) — un risque d'hallucination
direct. Cause identifiée avec précision : `ai_writer.py`'s
`_format_methodology_parameters_context()` et
`_format_confirmed_parameters_context()` lisent
`project_info["project_intake"]["methodology_parameters"]` (un champ
JSON de l'intake projet) et `parameter_engine.get_parameters_as_dict()`
(le système `project_parameters` de SPEC-03) — **ni l'un ni l'autre ne
lit la table `methodology_parameters` de SPEC-06** (les 26 paramètres
RECH extraits) **ni le résultat de
`parameter_instantiation.instantiate_parameter_blocks()`**. Le
`template_scaffold` construit par l'adaptateur ne contient que des
libellés de colonnes, aucune valeur — sans données sourcées à citer, le
modèle en invente. C'est le blocage principal pour l'objectif annoncé de
la session suivante (voir plus bas).

Tests : `test_guides_db_adapter.py` (8), `test_doc_exporter.py` (5).
249/249 tests de la suite complète passent. Diff Git vide sur les 8
guides Python et `ai_writer.py`.

**Travail de suite identifié, non fait (session suivante)** : T4
(décomposition de l'annexe Safeguarding du v3.0 — 27 lignes
Principe/Sous-principe/Risques/Indicateurs, structure différente de celle
envisagée initialement pour le v2.3 — et détection des pièces jointes),
T5 (résolution de version applicable, mode double piste Verra), T8
(fusion `GS-TPDDTEC`/`407`), T9 (endpoints/automatisation de la
détection de nouvelles versions).

**Fait (03.08.2026)** : le prérequis ci-dessus est comblé.
`carbongpt/repository/parameter_block_drafting.py` applique à la
rédaction de bloc de paramètre la même discipline qu'à
`defendability.py` (SPEC-04) : le modèle ne voit qu'un jeu de faits fermé
— UN paramètre `methodology_parameters` (identifiant ICS, description,
unité, source de données, méthode de mesure, fréquence, référence de
section et page) — et `validate_parameter_block_content()` rejette
mécaniquement tout nombre, référence de section, ou jeton en majuscules
(nom de méthodologie/outil/norme) absent de ce jeu de faits — réutilise
directement les regex nombre/section de `defendability.py`, pas
réimplémentées. `ai_writer.py::generate_section_draft()` accepte
maintenant un paramètre `parameter_id` optionnel : quand la sous-section
est de type `parameter_blocks` et qu'un `parameter_id` est fourni, la
génération passe par ce pipeline sourcé au lieu du prompt générique.
Repli inchangé (prompt générique) si aucun `parameter_id` n'est fourni —
rien ne casse pour l'usage existant. Portée limitée à RECH v5.0
(`methodology_code='407'`) pour l'instant : `project_info['methodology']`
reste un champ texte non fiable (le projet `id=12` a « TPDDTEC », pas
« 407 ») et ce dépôt n'a pas encore de résolveur
projet → méthodologie fiable — généraliser au-delà de RECH est un travail
distinct, non fait ici.

**Démonstration réelle sur le projet `id=12`** : bloc ex ante (ICS 17,
WCCF) et bloc monitoring (ICS 22, taux d'usage) rédigés via le pipeline
de production complet (`generate_section_draft`, pas un script à part).
Aucun des deux textes n'invente de référence de méthodologie, d'outil ou
d'équation — le garde-fou n'a déclenché aucun rejet sur ces deux essais
réels. Vérifié séparément que le garde-fou bloque bien le motif exact
observé au tour précédent (« TPDDTEC Version 4.0 », « TOOL33 Version
03.0 ») quand il est rejoué contre le vrai jeu de faits — capturé dans
`test_parameter_block_drafting.py`. Nuance trouvée en le testant :
« TPDDTEC » seul n'est pas bloqué, à raison — le nom du document RECH
v5.0 en base est littéralement « ...(RECH) (formerly TPDDTEC) », donc
c'est un fait vrai et sourcé ; ce sont les numéros de version inventés et
l'outil CDM TOOL33 (jamais mentionné par RECH pour ce paramètre) qui sont
rejetés. Bug de budget de tokens trouvé et corrigé au passage (même
défaut que SPEC-04 en session précédente) : `max_tokens=500` coupait le
bloc ICS 22 en plein milieu de phrase — RECH v5.0 documente ce paramètre
en détail (niveaux Mandatory/Good practice/Best practice de suivi
d'usage) ; porté à 1600.

**Résultat trouvé en testant, honnête** : le bloc ICS 22 (monitoring) est
directement utilisable — complet, fidèle à RECH v5.0, aucune invention.
Le bloc ICS 17 (ex ante) n'est PAS présentable tel quel, mais pas à cause
d'une hallucination : le texte source de RECH v5.0 lui-même écrit
littéralement « Source of data: Value(s) applied » pour ICS 16/17 (une
bizarrerie de rédaction du document, pas une erreur d'extraction) et le
champ méthode de mesure hérite un artefact déjà documenté au moment de
l'extraction (SPEC-06 T3 : « Choice of data or » ouvre le champ sans
attendre la suite de l'étiquette, un compromis assumé plutôt qu'une
reconnaissance complète des fragments — voir le commit d'implémentation
T3). Le garde-fou a fait exactement ce qu'on lui demandait : ne rien
inventer, même quand la source elle-même est confuse — préférer un bloc
fidèle mais maladroit à un bloc propre mais faux. Le nettoyage du champ
« Choice of data or » de l'extracteur T3 reste à faire.

Tests : `test_parameter_block_drafting.py` (13, dont la nuance TPDDTEC/
CDM), `test_ai_writer_parameter_block_routing.py` (3, routage mocké).
265/265 tests de la suite complète passent.

---

## SPEC-06 — Moteur d'instanciation (template × méthodologie × exigences transverses)

**Statut : implémentée en entier (03.08.2026) — T1 à T6.**

Correction demandée sur le rapport SPEC-05 : « 3 `parameter_block` » dans
le VPA-DD v3.0 comptait des **patrons** de bloc (ex ante 10 champs,
monitoring 18 champs, SDG 13 champs), pas des paramètres réels — un VPA-DD
réel en contient autant d'exemplaires qu'il a de paramètres de calcul
(16 pour le VPA-DD Kenya cité en SPEC-04). Le template seul ne dit ni
combien ni lesquels ; c'est la méthodologie qui le dit, et les sections
Safeguarding/Genre/Consultation/Développement durable du VPA-DD ne
viennent pas de RECH mais de documents Gold Standard transversaux séparés.

`docs/SPEC-06.md` : modélise l'équation template × méthodologie ×
exigences transverses → champs réels. Confirmé par lecture directe du
PDF RECH v5.0 déjà ingéré : chaque paramètre (« Parameter ID ICS 24 »,
25, 26...) porte un bloc structuré quasiment identique champ pour champ
au patron monitoring du VPA-DD v3.0 — le discriminant ex ante/monitoring
se lit dans le champ « Measurement and updating frequency », pas dans un
champ séparé. Liste réelle des 7 documents transversaux vérifiée en ligne
(même démarche que RECH en SPEC-01) : 101 Principles & Requirements,
102 Stakeholder Consultation, 103 Safeguarding Principles & Requirements,
104 Gender Equality Requirements & Guidelines, 118 SDG Impact Tool
Monitoring Indicators, 119 Paris Agreement Alignment Requirements, 201
Community Services Activity Requirements (daté 2019, signalé comme
potentiellement obsolète, hors périmètre).

**Piège trouvé en vérifiant avant d'écrire du code** : les pages de ces
documents transversaux ont le même défaut de balisage `<tr>` non fermé
que les pages de template (SPEC-05 T0) — pas la structure propre des
pages de méthodologie. Le mécanisme d'ingestion SPEC-01 est réutilisable
dans son principe, mais l'implémentation doit reprendre le parseur `lxml`
de `gs_template_ingest.py`, pas celui de `gs_ingest.py`.

**T1** : migration additive — `methodology_parameters` (`key` en `TEXT`,
pas `VARCHAR(100)` comme prévu dans la spec — RECH nomme certains
paramètres avec leur nom complet en toutes lettres, trouvé en important
les 26 vrais paramètres, corrigé avant de committer).

**T3** : `carbongpt/repository/rech_parameter_extractor.py`. **Bug
sérieux trouvé en testant contre le vrai PDF** : une première version
aplatissait les espaces d'un bloc pour reconstituer les étiquettes de
champ fragmentées sur plusieurs lignes — ça a échoué silencieusement sur
les 9 paramètres monitorés (`measurement_frequency_note` toujours vide,
y compris pour le fNRB, dont dépend justement la classification 'both').
Cause : dans ce PDF, la valeur n'est pas seulement coupée par
l'étiquette, elle est **intercalée entre ses fragments**
(« Measurement Determined ex-ante... / and updating biennially... /
frequency (Mandatory update...) »). Remplacé par une machine à états
ligne par ligne qui reconnaît chaque fragment d'étiquette connu et
n'assigne un champ ambigu (« Measurement » ouvre soit la fréquence soit
la méthode) qu'une fois la suite désambiguïsée. Deuxième bug trouvé en
testant : un bloc à cheval sur deux pages absorbait l'en-tête/pied de
page suivant dans son dernier champ (ICS 15, ICS 19) — corrigé en
retirant l'en-tête/pied de page répété avant découpage en blocs.

Classification ex ante/monitoring : **le signal primaire est la section
RECH elle-même** (§14.2 « Data and parameters not monitored » vs §14.3
« Data and parameters monitored », dont le texte introductif dit
littéralement leur nature) — plus fiable que le seul contenu de
`Measurement and updating frequency`, absent par construction pour les
paramètres de §14.2 (rien à monitorer). Ce contenu sert de signal
secondaire pour détecter le cas « les deux » (fNRB, ICS 20 : sous §14.3
mais son propre texte offre une option ex ante fixe) — jamais tranché
automatiquement, conforme à la demande explicite.

26 paramètres extraits et stockés, tous `extraction_method='llm_extracted'`,
`verified_by`/`verified_at` NULL — aucun marqué vérifié sans confirmation
de l'utilisateur.

**T5** : `carbongpt/repository/parameter_instantiation.py`. Les trois
patrons de bloc du VPA-DD v3.0 (SPEC-05 T7) ne sont pas distingués par
comptage de lignes (fragile) mais par lecture réelle des libellés de leurs
lignes dans le `.docx` (présence de « QA/QC », « Entity/person », etc.
pour le patron monitoring ; « SDG », « Net benefit » pour le patron SDG,
non couvert par RECH — remonté comme non associé, jamais deviné).

**Résultat sur RECH v5.0 × VPA-DD v3.0** : patron ex ante (T37) → 18
instances (ICS 1-17 + fNRB) ; patron monitoring (T40) → 9 instances
(ICS 18, 19, 21-26 + fNRB) ; patron SDG (T55) → non associé (source :
document 118, hors périmètre T2) ; 0 paramètre en attente de révision.

**Document 201 (Community Services Activity Requirements) vérifié** :
toujours en v1.2 (23.10.2019), confirmé « CURRENT DOCUMENT » sur la page
officielle — Gold Standard n'a pas republié ce document lors du
rafraîchissement de mai 2026. Reste le plus ancien document du corpus
utilisé par RECH/cookstoves.

**Bug trouvé par l'utilisateur en relisant la table livrée, corrigé** :
ICS 7 a un champ « Equations referred: » que RECH n'utilise que pour ce
seul paramètre parmi les 26 — non reconnu par l'extracteur, sa valeur
(« N/A ») se déversait dans `unit` (« N/A Equations N/A referred: »).
Ajouté comme frontière de champ reconnue mais non stockée ; test de
non-régression ajouté.

**T2** : `carbongpt/repository/gs_crosscutting_ingest.py`. Réutilise
`gs_template_ingest.py` (parseur `lxml`) sans dupliquer son code — importe
directement `fetch_template_page`, `parse_template_revision_history`,
`download_document`. Nouvelle table `crosscutting_requirements`
(migration additive). Deux bugs trouvés en ingérant réellement les 7
pages :
1. La page 118 (SDG Impact Tool Monitoring Indicators) n'a **aucun** bloc
   REVISION HISTORY — une seule version publiée depuis sa création
   (v1.0, 18.10.2025), pas encore d'historique à afficher. Repli dédié
   (`_parse_single_version`) qui lit le lien de téléchargement et la date
   affichée près du titre plutôt que de forcer le motif REVISION HISTORY.
2. `gs_template_ingest.py::_find_current_document_url` (SPEC-05) ne
   reconnaissait que `.docx`/`.doc` — juste pour les templates à remplir.
   Les 7 documents transversaux sont publiés en **`.pdf`** : les 5 dont
   le lien de la version courante n'était pas dans le tableau (comme pour
   le VPA-DD v3.0, SPEC-05) revenaient silencieusement sans fichier
   téléchargé. Corrigé en élargissant l'extension acceptée — revérifié
   contre les tests VPA-DD existants (SPEC-05), aucune régression.

Les 7 documents ingérés, versionnés et datés comme les méthodologies —
101 v2.1 (31.01.2025), 102 v2.1 (14.06.2022), 103 v2.1 (29.06.2023),
104 v2.0 (16.05.2023), 118 v1.0 (18.10.2025), 119 v1.1 (02.02.2026),
201 v1.2 (23.10.2019, confirmé non republié en mai 2026).

**T4** : `carbongpt/repository/field_requirement_linking.py`. Table de
correspondance vérifiée à la main (pas d'extraction automatique par
similarité de texte — écartée explicitement dans SPEC-06.md comme
heuristique fragile) entre les 9 sections de niveau 1 du VPA-DD v3.0 et
leurs sources : RECH v5.0 pour « Application of methodology(ies) » ;
103+104 pour Safeguarding/Genre ; 104 seule pour Gender equality
assessment ; 118 pour Sustainable development contribution (source aussi
du patron de bloc T55, laissé non associé par T5) ; 102 pour Stakeholder
Consultation ; 101+201 pour Project description ; 101 pour Appendices
(couverture partielle, mélange plusieurs sujets). Deux sections sans
aucune source : « Contact information of CME » (donnée administrative
pure) et « LUF additional information » (hors périmètre RECH/cookstoves,
gouvernée par l'Activity Requirement 203, non ingéré). 12 liens écrits.
`find_unlinked_sections()` retrouve ces deux gaps mécaniquement, pas
depuis une liste maintenue à la main.

**T6** : `carbongpt/repository/non_deducible_facts.py`. Catalogue de 5
catégories de faits non déductibles (choix de piste genre, échelle du
VPA, données de terrain, statut CORSIA/A6.4/PACM, coordonnées CME) —
important : une section « couverte » par une source (T4) fournit la
RÈGLE, pas toujours la VALEUR ; ce module documente précisément où
l'écart reste malgré une source liée. `ensure_open_questions_for_project()`
réutilise `project_open_questions` (SPEC-03) sans nouvelle table — 5
questions créées et vérifiées sur le projet réel `id=12`.

Tests : `test_rech_parameter_extractor.py` (10, dont la régression ICS 7),
`test_parameter_instantiation.py` (7), `test_gs_crosscutting_ingest.py` (7),
`test_field_requirement_linking.py` (6), `test_non_deducible_facts.py` (5).
236/236 tests de la suite complète passent. Diff Git vide sur
`carbongpt/guides/`, `doc_exporter.py`, `ai_writer.py` — rien de cassé.
`gs_template_ingest.py` (SPEC-05, pas la liste protégée) modifié pour le
bug `.pdf` ci-dessus, revérifié sans régression sur ses propres tests.

SPEC-06 est maintenant entièrement implémentée (T1 à T6).

**Travail de suite identifié, non fait** : T4 ne lie que les 9 sections
de niveau 1 et les 3 blocs de paramètres — pas les 161 champs
individuels du VPA-DD v3.0 (SPEC-05). « Appendices » (H303) mériterait une
liaison sous-section par sous-section, plus précise que la référence
générale à 101 retenue ici. Land-use & Forests (203) non ingéré — pas
pertinent pour RECH/cookstoves, mais bloquerait toute extension future à
des méthodologies forestières.

---

## Environnement local

Développement dans WSL (Ubuntu 26.04) — voir CLAUDE.md §5. PostgreSQL 18 +
pgvector installés via apt. `./start_local.sh` lance backend + frontend.
