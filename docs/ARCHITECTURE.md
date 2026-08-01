# Architecture cible — CarbonGPT

Version 1.0 — 30.07.2026

---

## Le principe fondateur

L'application actuelle est un **générateur de documents** avec un workflow
autour. Ce qu'elle doit devenir est un **moteur de raisonnement réglementaire**,
dont les documents ne sont qu'une sortie parmi d'autres.

Un consultant carbone ne remplit pas des templates. Il fait ceci, dans cet ordre :

1. **Diagnostic d'éligibilité** — ce projet est-il viable, sous quel standard,
   quelle méthodologie, **quelle version**
2. **Traçage du chemin réglementaire** — quelle séquence, quels jalons
   bloquants, quels délais
3. **Sourçage défendable des paramètres** — quel fNRB, de quelle source
   approuvée, avec quelle décote
4. **Production documentaire** — conséquence des trois premiers
5. **Anticipation de l'audit** — ce que le VVB va challenger
6. **Veille** — nouvelles versions, retraits, notes de clarification

L'état actuel couvre correctement l'étape 4 et une partie de la 3. Les étapes
1, 2, 5 et 6 sont absentes ou décoratives. C'est la cause racine du sentiment
que « l'application ne marche pas très bien » : elle commence par la fin.

---

## Les 7 couches

### Couche 0 — Corpus réglementaire vivant et versionné

Pas un dossier de PDF. Un référentiel où chaque document porte : version, date
d'entrée en vigueur, date de retrait, règles de transition, période de grâce.

Contenu : standards, méthodologies, tools CDM (TOOL30, TOOL33…), Rule Updates,
Rule Clarifications, Deviations, Clarification Requests, FAQ officielles.

**Constat clé (30.07.2026)** : `globalgoals.goldstandard.org` est totalement
ouvert et publie l'historique de versions sous forme structurée, avec URL PDF
directe par version. Le blocage Cloudflare documenté dans le code ne concerne
que l'**Assurance Platform** (documents des projets : PDD, MR d'un GS ID donné),
pas les méthodologies. L'ingestion automatique du corpus réglementaire est donc
réalisable immédiatement.

C'est le prérequis de tout le reste.

### Couche 1 — Extraction structurée des règles

Transformer la prose réglementaire en exigences exploitables : critères
d'éligibilité, paramètres requis (unité, source, tier, conservativité),
exigences de monitoring (fréquence, taille d'échantillon), annexes obligatoires,
contraintes de séquencement.

Chaque règle tracée jusqu'au document + section + version.

**Non négociable** : extraction par LLM *puis vérification*. Jamais d'extraction
traitée comme vérité. Une règle mal extraite qui passe en production, c'est un
CAR en audit.

### Couche 2 — Base de précédents

Les PDD et MR déjà publiés, oui — mais surtout les **rapports de validation et
de vérification, avec leurs CAR / CL / FAR**. Les findings disent empiriquement
ce que les VVB challengent réellement, par méthodologie, par pays, parfois par
VVB. Plus les projets rejetés ou retirés, et pourquoi.

Existant à exploiter : table `pack_findings` et l'extracteur de findings.

### Couche 3 — Moteur de raisonnement

**Totalement absent aujourd'hui. C'est le vrai chantier.** Quatre fonctions :

- **Diagnostic** : caractéristiques du projet → standards, méthodologies et
  versions éligibles, classés, avec justification et exclusions motivées
- **Pathfinding** : feuille de route réelle avec dépendances et jalons
  bloquants — consultation des parties prenantes avant soumission, timing du KPT
  par rapport à la période de crédit, séquence design certification →
  validation → première vérification
- **Résolution de paramètres** : pays + combustible + technologie → options
  candidates avec hiérarchie de sources, décotes applicables, et argument de
  défendabilité de chacune
- **Analyse de risque** : ce qui manque, ce qui sera challengé, avec probabilité
  fondée sur les précédents de la couche 2

C'est cette couche qui permet de répondre à : *« je veux distribuer des foyers
améliorés au Burkina Faso »* → quel fNRB, quelle consultation, dans quel ordre.

### Couche 4 — Production documentaire

**Existe, et c'est la partie la plus solide du projet.** Rédaction assistée avec
RAG hybride, classeur Excel à formules traçables, export DOCX.

À conserver. À rebrancher sur les couches 0 à 3 pour que la rédaction découle du
raisonnement au lieu de le précéder.

### Couche 5 — Adversaire d'audit

Simuler le VVB en s'appuyant sur les findings historiques réels de cette
méthodologie et de ce pays — pas sur un scoring de règles génériques comme
aujourd'hui.

### Couche 6 — Veille

Détection de nouvelles versions et de retraits, évaluation de l'impact sur le
portefeuille de projets de l'utilisateur, alerte.

Exemple concret : Gold Standard impose les versions alignées Paris pour toutes
les émissions de millésime 2026. Un système avec couche 6 aurait signalé
l'échéance sans qu'on ait à la chercher.

---

## Principe transversal : flexibilité par les données

L'exigence structurante : **on doit pouvoir ajouter ou retirer une
fonctionnalité sans casser l'application.**

La réponse technique est unique et vaut pour toutes les couches : *les règles
métier sont des données, pas du code.*

- Ajouter une méthodologie = ajouter des données
- Ajouter une version = ajouter des données
- Changer un template = changer des données
- Corriger un facteur d'émission = changer une donnée, tracée vers sa source

Le code ne contient que des **moteurs génériques** : un moteur de calcul qui lit
une spécification de méthodologie, un moteur de rédaction qui lit une structure
de document, un moteur de règles qui lit des contraintes.

Écart actuel à corriger : `carbongpt/guides/*.py` encode des structures de
documents en Python, et `carbongpt/core/gs_rech_v5.py` contient des constantes
réglementaires en dur, sans source.

---

## Stratégie de mise en œuvre

**Une méthodologie, traitée en profondeur totale, sur un projet réel.**

RECH v5.0 (cookstoves) a été retenue délibérément parce que c'est le cas le plus
dur : tout l'enjeu opérationnel est la transition v4.0 → v5.0. Le système est
donc obligé, dès le premier jour, de savoir qu'une méthodologie a des versions,
des dates d'effet et des règles de transition. Une méthodologie « simple »
aurait produit une architecture plate qu'il aurait fallu casser ensuite.

Les couches 0 à 3 sont génériques par construction. La deuxième méthodologie
coûtera donc beaucoup moins cher que la première.

**Critère de réussite du MVP** : le système produit un VPA-DD que l'utilisateur
n'a pas honte d'envoyer à son VVB.
