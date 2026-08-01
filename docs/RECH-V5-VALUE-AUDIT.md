# RECH-V5-VALUE-AUDIT — Audit des constantes de `gs_rech_v5.py`

Statut : rapport soumis à l'utilisateur — aucune valeur ci-dessous n'est marquée
`verified`. Toutes les valeurs extraites du PDF portent `extraction_method =
llm_extracted` (ou `llm_unverified` quand la valeur codée n'a pas pu être
retrouvée dans le texte) et sont écrites en base dans `regulatory_values`,
`verified_by`/`verified_at` restant `NULL` tant que ce rapport n'a pas été
validé.

**Source examinée** : `407_v5.0_PAA-M400-08_Reduced-Emission-from-Cooking-and-Heating.pdf`
(97 pages), téléchargé le 01.08.2026 depuis
`https://globalgoals.goldstandard.org/standards/407_v5.0_PAA-M400-08_Reduced-Emission-from-Cooking-and-Heating.pdf`,
sha256 vérifiable dans `documents`. Toutes les références de section et de
page ci-dessous renvoient à ce document.

---

## Résumé

| Constante | Codée en dur | Trouvée dans le PDF ? | Écart |
|---|---|---|---|
| NCV bois | 0.0156 TJ/t | ✅ Oui, identique | Aucun |
| NCV charbon | 0.0295 TJ/t | ✅ Oui, identique | Aucun |
| EF CO2 bois | 112.0 tCO2/TJ | ✅ Oui, identique | Aucun |
| EF CO2 charbon | 165.22 tCO2/TJ | ❌ **Absent du texte** | **Écart critique** — le PDF donne 3 valeurs possibles (112 / 355.36 / 236.91), aucune n'est 165.22 |
| EF non-CO2 bois | 9.46 tCO2e/TJ | ✅ Oui, identique | Aucun |
| EF non-CO2 charbon | 44.83 tCO2e/TJ | ❌ **Absent du texte** | **Écart critique** — le PDF donne 3 valeurs possibles (5.87 / 89.68 / 61.74), aucune n'est 44.83 |
| PCAP bois | 1.25 t/cap/an | ✅ Oui, identique | Référence de section erronée (voir détail) |
| PCAP charbon | 0.40 t/cap/an | ✅ Oui, identique | Référence de section erronée (voir détail) |
| fNRB défaut | 0.75 | ❌ **Absent du texte** | **Écart critique** — fNRB n'est pas une valeur fixe dans cette méthodologie |
| DAF défaut | 0.025 | ❌ **Absent du texte** | fNRB non plus, mais pour une raison différente : DAF vient d'un autre document (Tool 05) |
| embodied | 0.017 tCO2e/unité | ✅ Oui, identique | Aucun sur la valeur — mais une partie du calcul manque (voir détail) |
| leakage marché | 5% (0.05) | ❌ **Absent du texte** | **Écart critique** — la vraie valeur par défaut est 2% (0.02), et conditionnelle |

**5 des 12 constantes examinées sont soit absentes du texte, soit fausses.**
Sur 12 valeurs numériques codées en dur, 6 correspondent exactement au texte, 1
a la bonne valeur mais la mauvaise référence de section, 1 est manquante pour
une raison structurelle (dépend d'un autre document), et **4 n'ont aucune
trace dans le PDF RECH v5.0** : EF CO2 charbon, EF non-CO2 charbon, fNRB,
leakage marché.

---

## Détail, constante par constante

### 1. NCV (Net Calorific Value / pouvoir calorifique net)

**Codé** (`_NCV`) : bois 0.0156 TJ/t, charbon 0.0295 TJ/t
**Source déclarée dans le code** : aucune

**Ce que dit le PDF** : identique, exactement.
> « Wood: Methodology default, 0.0156 TJ/ton » / « Charcoal: Methodology
> default, 0.0295 TJ/ton »

**Référence** : §14.2, Paramètre ICS 12 (scénario de référence) et ICS 13
(scénario d'activité), page 60. Valeurs dérivées des défauts IPCC.

**Écart** : aucun. **Verdict : correct, à sourcer formellement (§14.2, ICS
12/13, p.60).**

---

### 2. EF CO2 — bois

**Codé** (`_EF_CO2["wood"]`) : 112.0 tCO2/TJ
**Source déclarée dans le code** : « Annexe 2 » — **cette annexe n'existe
pas sous ce nom dans le document v5.0** (les annexes du v5.0 sont : 1.
Demande captive, 2. Lignes directrices KPT, 3. Calendrier de préparation, 4.
Analyse d'additionnalité — aucune n'est une table de facteurs d'émission).

**Ce que dit le PDF** : identique.
> « Wood: 112 tCO2/TJ »

**Référence** : §14.2, Paramètres ICS 8 (référence) / ICS 10 (activité),
pages 57-58. Défaut IPCC 2019.

**Écart** : aucun sur la valeur. **La référence « Annexe 2 » du code est
fausse — la bonne référence est §14.2 (ICS 8/10).**

---

### 3. EF CO2 — charbon — **ÉCART CRITIQUE, traite l'incohérence signalée**

**Codé** (`_EF_CO2["charcoal"]`) : **165.22 tCO2/TJ**
**Codé séparément dans `er_simulator.py`** (plafond TPDDTEC) : **197.15
tCO2/TJ**
**Source déclarée dans le code** : « Annexe 2 » (inexistante, voir ci-dessus)

**Ce que dit le PDF** : le document ne donne **pas une seule valeur** pour le
charbon, mais **trois**, selon que les émissions de carbonisation
(fabrication du charbon) sont incluses ou non, et selon le ratio de
conversion bois→charbon (WCCF, Wood-to-Charcoal Conversion Factor) :

| Cas | Valeur | Applicabilité |
|---|---|---|
| Combustion seule (sans carbonisation) | **112 tCO2/TJ** | Par défaut, identique au bois |
| Avec carbonisation, WCCF 6:1 (≈17% rendement de meule) | **355.36 tCO2/TJ** | Afrique subsaharienne et pays les moins avancés (défaut) |
| Avec carbonisation, WCCF 4:1 (≈25% rendement de meule) | **236.91 tCO2/TJ** | Régions industrialisées / haute efficacité (obligatoire) ; ou choix conservateur optionnel partout, y compris ASS/PMA |

**Référence** : §14.2, Paramètres ICS 8 / ICS 10, pages 57-58. Définition du
WCCF : page 10.

**Écart** : **critique. Ni 165.22 (`gs_rech_v5.py`) ni 197.15
(`er_simulator.py`) ne correspondent à une seule des trois valeurs
officielles.** Les deux modules semblent avoir chacun inventé ou mal recopié
un nombre, et ils ne sont même pas cohérents entre eux. Aucun des deux
fichiers ne peut être considéré comme correct actuellement.

**Ce que je ne tranche pas** : la spec le disait déjà — il n'existe pas un
facteur d'émission du charbon, il en existe plusieurs selon la source des
émissions de carbonisation retenue. **C'est à toi de décider** quelle
combinaison (combustion seule / WCCF 6:1 / WCCF 4:1) s'applique à quels
projets dans le portefeuille, en fonction du pays et de la méthode de
carbonisation réellement utilisée. J'ai enregistré les trois valeurs dans
`regulatory_values`, différenciées par leur `applicability`, sans en choisir
une par défaut.

---

### 4. EF non-CO2 — bois

**Codé** (`_EF_NONCO2["wood"]`) : 9.46 tCO2e/TJ
**Source déclarée** : « Annexe 2 » (inexistante)

**Ce que dit le PDF** : identique.
> « Wood: 9.46 tCO2e/TJ (AR5 GWP) »

**Référence** : §14.2, Paramètres ICS 9 / ICS 11, pages 58-59.

**Écart** : aucun sur la valeur. Même erreur de référence (« Annexe 2 » au
lieu de §14.2).

---

### 5. EF non-CO2 — charbon — **ÉCART CRITIQUE**

**Codé** (`_EF_NONCO2["charcoal"]`) : **44.83 tCO2e/TJ**
**Source déclarée** : « Annexe 2 » (inexistante)

**Ce que dit le PDF** : trois valeurs, même logique que EF CO2 charbon :

| Cas | Valeur |
|---|---|
| Combustion seule | **5.87 tCO2/TJ** |
| Avec carbonisation, WCCF 6:1 | **89.68 tCO2/TJ** |
| Avec carbonisation, WCCF 4:1 | **61.74 tCO2/TJ** |

**Référence** : §14.2, Paramètres ICS 9 / ICS 11, pages 58-59.

**Écart** : **critique. 44.83 n'apparaît nulle part dans le document.**
Enregistré dans `regulatory_values` avec les trois vraies valeurs,
applicabilité différenciée, aucun choix imposé.

---

### 6. PCAP (plafond de consommation per capita)

**Codé** (`_PCAP`) : bois 1.25 t/cap/an, charbon 0.40 t/cap/an
**Source déclarée dans le code** : « §8.2 »

**Ce que dit le PDF** : identique — **mais ce sont des « Cap values », pas
de simples valeurs par défaut**, et il existe aussi des « Threshold values »
distinctes qui ne sont PAS les mêmes nombres :

> Utilisateurs bois primaires (≥75% des cuissons au bois) :
> - Threshold : 0.75 t/personne/an — si dépassé, une justification par étude
>   tierce indépendante est exigée
> - **Cap : 1.25 t/personne/an** ← c'est cette valeur que `gs_rech_v5.py` code
>
> Utilisateurs charbon primaires ou baseline mixte :
> - Threshold : 0.20 t/personne/an
> - **Cap : 0.40 t/personne/an** ← idem

**Référence réelle** : §7.4.2.3 (« Threshold and Cap Values »), sous l'étape
7.4 (« Application of the Downward Adjustment »), page 31 — **pas §8.2**
(§8.2 est « Calculation of Activity Emissions », une section différente).

**Écart** : la valeur est correcte, la référence de section codée est
fausse. **Point d'attention supplémentaire** : le nombre 0.75 existe bel et bien
dans le document, mais comme *threshold* du bois, pas comme cap — et c'est
une coïncidence troublante avec le défaut fNRB codé en dur (voir point 7).
Ne pas confondre les deux tables.

---

### 7. fNRB (fraction de biomasse non-renouvelable) — **ÉCART CRITIQUE**

**Codé** (`fNRB` défaut) : **0.75**
**Source déclarée dans le code** : aucune

**Ce que dit le PDF** : fNRB n'est **pas une valeur fixe** dans cette
méthodologie. C'est un paramètre suivi/dérivé (désigné « ICS 20 » dans le
texte), qui doit être obtenu via des outils approuvés — MoFuSS ou l'outil
fNRB A6.4 (équivalent de l'ancien CDM TOOL33) — et qui varie selon le pays et
la source de biomasse. Aucun défaut numérique global n'est donné.

**Le nombre « 0.75 » apparaît deux fois dans le document, mais ni l'une ni
l'autre n'est fNRB** : c'est le *threshold value* de consommation bois
(§7.4.2.3(a), voir point 6 ci-dessus) — un paramètre totalement différent qui
a la même valeur numérique par coïncidence.

**Écart** : **critique. 0.75 comme défaut fNRB n'a aucune base dans le texte
RECH v5.0.** Marqué `llm_unverified` dans `regulatory_values` (pas
`llm_extracted`, parce que je n'ai rien pu extraire — c'est une absence
constatée, pas une valeur lue). Un calcul qui utiliserait cette ligne lèvera
une erreur, par construction.

**Ce que je ne comble pas** : je ne sais pas d'où vient le 0.75 codé. Ce
n'est ni une erreur de copie évidente (comme 165.22 pourrait l'être d'une
faute de frappe), ni un défaut sectoriel typique que je reconnaisse. À
vérifier avec toi.

---

### 8. DAF (Downward Adjustment Factor / facteur d'ambition Net Zero)

**Codé** (`DAF` défaut) : **0.025**
**Source déclarée dans le code** : « GS Tool 05 » — **cette partie de la
source est correcte.**

**Ce que dit le PDF** : le DAF est bien défini formellement (§7.4.6, Eq.9 :
`BE_adj = BE_unc × (1 − DAF_NetZero)`), mais **sa valeur numérique n'est pas
dans ce document**. Le texte est explicite :
> « This factor remains fixed and shall be sourced from the GS4GG Tool 05
> corresponding to the host country and the calendar year of the monitoring
> period. »

Autrement dit : le DAF dépend du pays hôte ET du millésime, et se lit dans
un document séparé (**GS4GG Tool 05 — Downward Adjustment Factor
Determination**), que je n'ai pas ingéré (hors périmètre de SPEC-01, qui ne
couvrait que la page de méthodologie RECH elle-même).

**Écart** : je ne peux **ni confirmer ni infirmer** 0.025 depuis ce document.
Marqué `llm_unverified`. **Pour trancher cette valeur, il faudra ingérer
GS4GG Tool 05 séparément** — je le signale comme travail de suite, je ne
l'ai pas fait ici pour rester dans le périmètre de SPEC-01.

---

### 9. Embodied emissions (émissions incorporées des appareils)

**Codé** (`embodied`) : 0.017 tCO2e/unité
**Source déclarée dans le code** : « défaut GS » (vague mais correct dans
l'esprit)

**Ce que dit le PDF** : identique, exactement.
> « A standardized default deduction of 17.0 kg CO2e per unit (0.017
> tCO2e/unit) may be applied... proxy conservateur et standardisé dérivé
> d'analyses de cycle de vie globales agrégées » (note de bas de page)

**Référence** : §9.2.2, Eq.18/19, page 39.

**Écart sur la valeur** : aucun.

**Point d'attention important, hors du périmètre strict « une constante »**
: la méthodologie prévoit **deux méthodes d'amortissement** selon la durée
de vie technique de l'appareil :
- Durée de vie < 5 ans (ou choix simplifié pour les autres) : déduction
  intégrale en une fois, dès la première période de suivi (Eq.18) — **c'est
  la seule méthode que `gs_rech_v5.py` implémente**, d'après le docstring
  (« one-time, charged in year 1 »)
- Durée de vie ≥ 5 ans : la déduction doit être **amortie sur les 5 ans de la
  première période de comptabilisation** (Eq.19) — **absente du code
  actuel**

Ce n'est pas une valeur fausse, mais une branche de calcul manquante. Je le
signale parce que ça peut fausser des résultats pour des technologies
durables, mais je ne l'ai pas codé — ce serait sortir du périmètre de
SPEC-01 (corpus documentaire), pas une correction de donnée.

---

### 10. Leakage marché (fuite marché et comportementale) — **ÉCART CRITIQUE**

**Codé** (dans le docstring de `calculate_gs_rech_v5_er`) : **5% (0.05)**,
appliqué de façon inconditionnelle : `LE_market = (BEy − AEy) × 0.05`
**Source déclarée dans le code** : aucune

**Ce que dit le PDF** : la méthodologie prévoit **trois options**, pas une
valeur fixe :
1. **Option 1 — Négligeable (de minimis)** : LE_Market = 0, si deux
   conditions strictes sont démontrées (transfert d'équipement négligeable +
   effet rebond pleinement internalisé dans le suivi)
2. **Option 2 — Défaut conservateur** : **2% (0.02)**, appliquée seulement
   si les conditions de l'Option 1 ne sont pas remplies et que l'Option 3
   n'est pas choisie — `LE_Market = (BEy − AEy) × 0.02` (Eq.20)
3. **Option 3 — Évaluation détaillée** : enquête quantitative propre au
   projet, avec suivi biennal

**Référence** : §9.3.2, Eq.20, Paramètre ICS 24, pages 40-41.

**Écart** : **critique, sur deux points à la fois** : (1) la valeur codée
(5%) ne correspond à aucune des trois options — la seule valeur numérique
fixe du texte est 2%, pas 5% ; (2) même 2% n'est pas censé s'appliquer
systématiquement — c'est un défaut conditionnel (Option 2 sur 3), pas une
constante universelle. Le code actuel applique un taux qui n'existe nulle
part dans le texte, et sans jamais considérer les deux autres options.

---

## Ce que je n'ai pas pu vérifier du tout

- **DAF (0.025)** — dépend d'un document externe non ingéré (GS4GG Tool 05).
- **fNRB (0.75)** — n'est structurellement pas une constante dans cette
  méthodologie ; aucune source ne peut le confirmer par nature.

Pour les deux, je n'ai « rien trouvé » plutôt que d'avoir trouvé un chiffre
différent — c'est une absence, pas une contradiction, et je ne l'ai pas
comblée par une supposition.

---

## Prochaines étapes possibles (non faites, à ta décision)

1. **Trancher, valeur par valeur**, celles marquées `llm_extracted` ou
   `llm_unverified` ci-dessus — rien ne devient `verified_by`/`verified_at`
   sans ton accord explicite.
2. Pour EF CO2/non-CO2 charbon : décider quelle règle d'applicabilité
   (combustion seule / WCCF 6:1 / WCCF 4:1) s'applique à quels pays/projets
   du portefeuille, ou si ça doit rester un choix au cas par cas dans
   l'outil.
3. Ingérer **GS4GG Tool 05** séparément pour sourcer le DAF par pays et
   millésime — nouvelle spec, hors périmètre de SPEC-01.
4. Une fois les valeurs tranchées : modifier `gs_rech_v5.py` pour lire
   depuis `regulatory_values` au lieu des constantes codées en dur (prévu par
   SPEC-01 T5.4, volontairement pas fait dans cette passe — je ne voulais
   pas reconnecter le moteur de calcul à des valeurs que tu n'as pas encore
   validées).
5. Décider si la branche d'amortissement sur 5 ans des embodied emissions
   (Eq.19) doit être implémentée.
