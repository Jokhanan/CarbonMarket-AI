# CLAUDE.md — Instructions permanentes

Ce fichier est lu automatiquement au début de chaque session. Il prime sur toute
instruction ponctuelle contradictoire donnée dans le chat.

---

## 1. Le projet

CarbonGPT est un **moteur de raisonnement réglementaire** pour la certification
carbone. Les documents (PDD, MR) sont une *sortie* du raisonnement, jamais le
point de départ.

Cible du MVP, verrouillée : produire, pour un projet réel sous **Gold Standard
RECH v5.0** (méthodologie 407, publiée le 05.05.2026), un paquet complet et
défendable devant un VVB :

- le PDD / VPA-DD
- le classeur Excel de calcul, à formules traçables
- la simulation ER
- les documents de consultation des parties prenantes

Rien d'autre n'est dans le périmètre. Toute proposition d'élargissement doit être
refusée et signalée à l'utilisateur.

---

## 2. Règles d'architecture — non négociables

### R1. Les règles métier sont des données, jamais du code

Ajouter une méthodologie, une version, un template ou un paramètre ne doit
**jamais** exiger d'écrire du Python. Cela doit se faire en ajoutant une entrée
en base ou un fichier YAML.

Conséquence directe : `carbongpt/guides/*.py` (structures de documents encodées
en Python) et les constantes en dur dans `carbongpt/core/gs_rech_v5.py` sont des
anti-patterns à migrer vers des données. Ne pas en créer de nouveaux.

### R2. Aucune valeur réglementaire sans source

Toute constante, seuil, facteur d'émission, plafond ou valeur par défaut doit
porter :

- le document source (nom, version, date d'entrée en vigueur)
- la référence de section ou de paragraphe
- l'URL d'origine

Une valeur sans source ne doit pas exister dans le système. Si une valeur est
nécessaire mais non sourçable, elle est marquée `UNVERIFIED` et remontée à
l'utilisateur — jamais utilisée silencieusement dans un calcul.

### R3. Un paramètre est une décision, pas un nombre

Modéliser un paramètre comme un ensemble d'options candidates, chacune avec :

- ses conditions d'applicabilité
- sa source et son rang dans la hiérarchie de préférence
- sa décote de conservativité éventuelle
- son argument de défendabilité face à un VVB

Ne jamais choisir une valeur à la place de l'utilisateur sans afficher les
alternatives écartées et la raison.

### R4. Tout est versionné et daté

Une méthodologie n'existe pas : il existe une *version* d'une méthodologie, avec
une date d'entrée en vigueur, éventuellement une date de retrait, et des règles
de transition. Toute logique qui ignore la version est fausse par construction.

### R5. Pas de correctif local

Si un bug révèle un problème de conception, le signaler et proposer une
correction structurelle. Ne pas rustiner. En cas de doute, s'arrêter et demander.

---

## 3. Méthode de travail

1. Une seule spec en cours à la fois. Jamais deux chantiers en parallèle.
2. Lire `docs/SPEC-XX.md` intégralement avant d'écrire la moindre ligne.
3. Tout ce qui n'est pas dans la spec est hors périmètre.
4. À la fin de chaque tâche : mettre à jour `docs/STATUS.md`, puis commit + push.
5. Toute décision d'architecture prise en cours de route va dans
   `docs/DECISIONS.md` avec sa justification.

### Tests

- La suite doit passer avant tout commit : `python3 -m pytest carbongpt/tests/`
- État connu au 30.07.2026 : **130 passent, 3 échouent** (tests obsolètes dans
  `test_ai_review.py` et `test_registry.py`, signatures de fonctions modifiées
  sans mise à jour des tests). Les corriger avant d'ajouter du code neuf.
- Toute logique de calcul ER nouvelle doit être couverte par un test avec des
  valeurs attendues vérifiées à la main.

### Ce qu'il ne faut pas casser

Ces modules fonctionnent et représentent le travail le plus solide du projet :

- `carbongpt/core/er_simulator.py` — placement du fNRB par méthode, décote
  TOOL30, plafonds EF appliqués après overrides
- `carbongpt/core/er_excel.py` — classeur à vraies formules Excel liées
- `carbongpt/core/parameter_engine.py` — validation, traçabilité, dérivés
- `carbongpt/repository/schema.py` — 41 tables

Les modifier uniquement si la spec en cours le demande explicitement.

---

## 4. Sécurité — à corriger dès que touché

- `carbongpt/app/main.py` : l'authentification est conditionnelle
  (`if not _API_KEY: return await call_next(request)`). Si la variable
  d'environnement n'est pas définie, **les 187 endpoints sont ouverts**. Le
  défaut doit être *fermé*, pas ouvert.
- `carbongpt/core/project_brain.py` (~ligne 1636) : `_get_project_field`
  interpole un nom de colonne directement dans une requête SQL. Non exploitable
  aujourd'hui (valeurs littérales seulement), mais à sécuriser par liste blanche.

---

## 5. Environnement

- Backend : FastAPI, port 3000 — toute la logique métier
- Frontend : React + Vite + TypeScript, servi par Express (port 5000), qui n'est
  **qu'un proxy** vers FastAPI
- Base : PostgreSQL + pgvector
- Streamlit est mort : `start_carbongpt.sh` ne fait que le tuer. Ne pas y
  retoucher, ne pas le ressusciter.
- Démarrage local : `./start_local.sh` (depuis WSL, à la racine) lance
  PostgreSQL, le backend et le frontend ensemble ; Ctrl+C arrête tout proprement.

### Clés d'API

Deux variables d'environnement distinctes, chacune requise pour une
capacité précise — aucune des deux ne dégrade silencieusement en son
absence, l'appel échoue avec un message explicite :

- `ANTHROPIC_API_KEY` — génération de texte (rédaction, revue, extraction,
  argument de défendabilité...). Toute la génération de texte passe par
  `carbongpt/core/openai_client.py` (nom historique conservé, contenu
  bascule vers Claude), modèle par défaut `claude-sonnet-5`.
- `OPENAI_API_KEY` — embeddings uniquement (`text-embedding-3-small`).
  Anthropic ne propose pas d'API d'embeddings. Utilisé par
  `carbongpt/repository/ingestion.py`.

Placer les deux dans un fichier `.env` à la racine du dépôt (non suivi par
Git — vérifier que `.env` est bien dans `.gitignore`) ou comme variables
d'environnement du shell avant de lancer `./start_local.sh`.

**Point d'attention non résolu** : `carbongpt/core/openai_client.py` est le
seul point vraiment centralisé — `ai_writer.py` et `calculation_engine.py`
passent par lui. Mais `methodology_parser.py`, `evidence_engine.py`,
`methodology_kb.py` et `research_orchestrator.py` ont chacun leur propre
`_call_openai` local, qui appelle OpenAI directement, sans passer par ce
fichier. Ils ne sont pas concernés par la bascule vers Anthropic — à
traiter dans une passe séparée si on veut une vraie centralisation.

---

## 6. Interlocuteurs

L'utilisateur est un expert de la certification carbone (Gold Standard, Verra,
CDM, Article 6) et **ne code pas**. Lui écrire en français, en termes métier, pas
en jargon technique. Lui poser des questions de fond réglementaire : c'est le
seul des trois à savoir ce qu'un VVB acceptera.

L'architecture et les specs sont définies dans une conversation séparée sur
claude.ai. Les fichiers `docs/` font foi.
