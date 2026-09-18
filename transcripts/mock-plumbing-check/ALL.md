# Transcripts — tuteur 2Bac SM

- **Généré le** : 2026-09-18T03:31:52
- **Modèle** : `adaptive-mock`
- **System prompt** : `rag/prompts.py` (7683 caractères)

## Darija-check (safeguard anti-drift)

- Tours analysés : **21**
- Retry déclenché : **21** (100%)
-  - corrigé au 2e essai : **21**
-  - échec persistant (drift réel non corrigé) : **0**
-  - erreur API pendant le retry (réponse 1 conservée) : **0**
- Aucun tour en échec : toutes les réponses ont fini avec assez de marqueurs darija.
- Journal détaillé : `logs/darija_retry_log.jsonl`

# Multi-tour — l'élève se trompe (limites, mémoire du contexte)

- **Scénario** : `6-multi-tour-erreur`
- **Objectif** : Vérifier la MÉMOIRE DU CONTEXTE et la PATIENCE : l'élève propose une réponse fausse, puis sur-généralise à partir de son erreur. Le prof doit (a) corriger sans condescendance, (b) ne pas valider la fausse règle, (c) au dernier tour se souvenir de l'erreur précise du 2e tour sans que l'élève la répète. Échec si le prof perd le fil ou se répète mot pour mot.
- **Généré le** : 2026-09-18T03:31:43
- **Modèle** : `adaptive-mock`
- **Filtres** : matière = Mathématiques, chapitre = (aucun)
- **Statut** : OK

---

## 🧑 Élève

> Saha prof, 3endi had l'exercice : $\lim_{x \to 2} \frac{x^2 - 4}{x - 2}$. Kifach nbda ?

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.705) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 20/23, ligne ~476)
  - extrait : ## Exercice 5 : (2 pts)  **1 - a) (0.5 pt)**  On pose la fonction $u$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto \dfrac{-1}{x}$, et la fonction $v$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto e^x$.  On a $u$ …
- **[Source 2]** (score 0.702) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 3/26, ligne ~74)
  - extrait : ## Partie II — Étude de la fonction f  On définit $f$ sur $[0,\,+\infty[$ par : $f(x) = \dfrac{x}{e^{x} - e^{-x}}$ pour $x > 0$ et $f(0) = \dfrac{1}{2}$.  1. Calculer $\lim_{x \to +\infty} f(x)$ et interpréter graphiquem …
- **[Source 3]** (score 0.661) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 15/23, ligne ~344)
  - extrait : D'après le théorème de comparaison des limites on a : $\displaystyle\lim_{x \to +\infty} F(x) = -\infty$  et de plus : $F(1) - \dfrac{(\ln x)^2}{2} \leq F(x) \leq F(1) - \dfrac{(\ln x)^2}{4}$  On multiplie tous les membr …
- **[Source 4]** (score 0.607) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2018/2018-normale-corrige.txt` (extrait 10/17, ligne ~229)
  - extrait : ### Partie II :  **1- a)** On a $f(0) = 1$ et $\lim\limits_{x \to 0^{+}} f(x) = \lim\limits_{x \to 0^{+}} \left(1 + x\right) \dfrac{\ln\left(1 + x\right)}{x} = 1$  car $\lim\limits_{x \to 0^{+}} \left(1 + x\right) = 1$ e …
- **[Source 5]** (score 0.572) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 2/26, ligne ~52)
  - extrait : $$I(x) = \Big[-t\,e^{-t}\Big]_{0}^{x} + \int_{0}^{x} e^{-t}\,dt = -x e^{-x} + \Big[-e^{-t}\Big]_{0}^{x} = -x e^{-x} - e^{-x} + 1.$$  $$\forall x \in [0,\,+\infty[,\ I(x) = -x e^{-x} - e^{-x} + 1$$  3-a. Montrer que $\for …
- **[Source 6]** (score 0.358) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2010/2010-normale-corrige.txt` (extrait 7/8, ligne ~134)
  - extrait : On trouve : $\lim\limits_{x \to 0^{+}} F(x) = +\infty$ et $\lim\limits_{x \to +\infty} F(x) = +\infty$ et $\lim\limits_{x \to +\infty} \dfrac{F(x)}{x} = 0$  0,25 accordé pour chaque limite — 0,25 accordé pour chaque inég …

---

## 🧑 Élève

> Ana jarrabt : 7it $x^2 - 4$ kat3ti 0 f $x = 2$, donc l jawab howa 0. Wach s7i7 ?

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.733) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 20/23, ligne ~476)
  - extrait : ## Exercice 5 : (2 pts)  **1 - a) (0.5 pt)**  On pose la fonction $u$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto \dfrac{-1}{x}$, et la fonction $v$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto e^x$.  On a $u$ …
- **[Source 2]** (score 0.698) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 3/26, ligne ~74)
  - extrait : ## Partie II — Étude de la fonction f  On définit $f$ sur $[0,\,+\infty[$ par : $f(x) = \dfrac{x}{e^{x} - e^{-x}}$ pour $x > 0$ et $f(0) = \dfrac{1}{2}$.  1. Calculer $\lim_{x \to +\infty} f(x)$ et interpréter graphiquem …
- **[Source 3]** (score 0.685) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 21/23, ligne ~502)
  - extrait : Donc $g$ n'est pas continue à gauche de 0. Donc $g$ n'est pas continue en 0.  **2 - a) Calculons $L(x)$ pour tout $x \in \mathbb{R}^{\star +}$ (0.25 pt)**  $$L(x) = \int_0^x g(t)\,dt = \int_0^x \left(\frac{1}{t^2}e^{\fra …
- **[Source 4]** (score 0.598) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2018/2018-normale-corrige.txt` (extrait 10/17, ligne ~229)
  - extrait : ### Partie II :  **1- a)** On a $f(0) = 1$ et $\lim\limits_{x \to 0^{+}} f(x) = \lim\limits_{x \to 0^{+}} \left(1 + x\right) \dfrac{\ln\left(1 + x\right)}{x} = 1$  car $\lim\limits_{x \to 0^{+}} \left(1 + x\right) = 1$ e …
- **[Source 5]** (score 0.577) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 2/26, ligne ~52)
  - extrait : $$I(x) = \Big[-t\,e^{-t}\Big]_{0}^{x} + \int_{0}^{x} e^{-t}\,dt = -x e^{-x} + \Big[-e^{-t}\Big]_{0}^{x} = -x e^{-x} - e^{-x} + 1.$$  $$\forall x \in [0,\,+\infty[,\ I(x) = -x e^{-x} - e^{-x} + 1$$  3-a. Montrer que $\for …

---

## 🧑 Élève

> Ah... walakin mazal ma fhemtch 3lach. Wach kol limite li l numérateur dialha kayt3adel kat3ti 0 ? 7ta f $\lim_{x \to 3} \frac{x^2 - 9}{x - 3}$ ?

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.647) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 20/23, ligne ~476)
  - extrait : ## Exercice 5 : (2 pts)  **1 - a) (0.5 pt)**  On pose la fonction $u$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto \dfrac{-1}{x}$, et la fonction $v$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto e^x$.  On a $u$ …
- **[Source 2]** (score 0.645) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 3/26, ligne ~74)
  - extrait : ## Partie II — Étude de la fonction f  On définit $f$ sur $[0,\,+\infty[$ par : $f(x) = \dfrac{x}{e^{x} - e^{-x}}$ pour $x > 0$ et $f(0) = \dfrac{1}{2}$.  1. Calculer $\lim_{x \to +\infty} f(x)$ et interpréter graphiquem …
- **[Source 3]** (score 0.626) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 15/23, ligne ~344)
  - extrait : D'après le théorème de comparaison des limites on a : $\displaystyle\lim_{x \to +\infty} F(x) = -\infty$  et de plus : $F(1) - \dfrac{(\ln x)^2}{2} \leq F(x) \leq F(1) - \dfrac{(\ln x)^2}{4}$  On multiplie tous les membr …
- **[Source 4]** (score 0.552) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2018/2018-normale-corrige.txt` (extrait 10/17, ligne ~229)
  - extrait : ### Partie II :  **1- a)** On a $f(0) = 1$ et $\lim\limits_{x \to 0^{+}} f(x) = \lim\limits_{x \to 0^{+}} \left(1 + x\right) \dfrac{\ln\left(1 + x\right)}{x} = 1$  car $\lim\limits_{x \to 0^{+}} \left(1 + x\right) = 1$ e …
- **[Source 5]** (score 0.526) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 2/26, ligne ~52)
  - extrait : $$I(x) = \Big[-t\,e^{-t}\Big]_{0}^{x} + \int_{0}^{x} e^{-t}\,dt = -x e^{-x} + \Big[-e^{-t}\Big]_{0}^{x} = -x e^{-x} - e^{-x} + 1.$$  $$\forall x \in [0,\,+\infty[,\ I(x) = -x e^{-x} - e^{-x} + 1$$  3-a. Montrer que $\for …
- **[Source 6]** (score 0.359) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2010/2010-normale-corrige.txt` (extrait 7/8, ligne ~134)
  - extrait : On trouve : $\lim\limits_{x \to 0^{+}} F(x) = +\infty$ et $\lim\limits_{x \to +\infty} F(x) = +\infty$ et $\lim\limits_{x \to +\infty} \dfrac{F(x)}{x} = 0$  0,25 accordé pour chaque limite — 0,25 accordé pour chaque inég …

---

## 🧑 Élève

> Safi daba fhemt. T9der t3awed liya chno kan l'ghalat diali l'awal, w chno l jawab l7a9i9i, bach ma n3awdouch f l'examen ?

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.502) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 0/23, ligne ~2)
  - extrait : ROYAUME DU MAROC Correction — Baccalauréat Sciences Mathématiques Session : Normal 2014 Mathématiques Série : Baccalauréat Sciences Mathématiques A & B MTM-Group (MathsForBac) — Option SM A & B
- **[Source 2]** (score 0.419) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 0/26, ligne ~2)
  - extrait : MonBac.ma — Plateforme de préparation au Baccalauréat marocain  Corrigé — Mathématiques Sciences Mathématiques A & B Session Ordinaire — 2026 Coefficient : 9 | Durée : 4h | Barème : /20  Ce corrigé est proposé par MonBac …
- **[Source 3]** (score 0.295) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 25/26, ligne ~610)
  - extrait : $$\forall n \in \mathbb{N}^{*},\ (M(x))^{n} = M(nx)$$  4-b. Résoudre dans $E$ : $X^{3} - X^{2} = \begin{pmatrix} 0 & 0 & 0 \\ 5 & 1 & -1 \\ 3 & 1 & -1 \end{pmatrix}$. (0,5 pt)  Soit $X \in E$, donc $X = M(x)$ avec $x \in …

---


# Élève découragé — « ma fahemch walou, khasni no9ta »

- **Scénario** : `7-eleve-decourage`
- **Objectif** : Vérifier la PATIENCE sous frustration : l'élève abandonne et réclame juste la note. Le prof doit rester encourageant, NE PAS lâcher la réponse complète pour calmer la frustration, et réduire encore la difficulté (une seule petite étape, une autre analogie). Échec s'il donne le résultat final ou s'il répète la même explication.
- **Généré le** : 2026-09-18T03:31:46
- **Modèle** : `adaptive-mock`
- **Filtres** : matière = Mathématiques, chapitre = (aucun)
- **Statut** : OK

---

## 🧑 Élève

> Prof, 3endi devoir f les limites : $\lim_{x \to +\infty} \frac{3x^2 - x + 1}{2x^2 + 5}$. Chno ndir ?

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.698) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 3/26, ligne ~74)
  - extrait : ## Partie II — Étude de la fonction f  On définit $f$ sur $[0,\,+\infty[$ par : $f(x) = \dfrac{x}{e^{x} - e^{-x}}$ pour $x > 0$ et $f(0) = \dfrac{1}{2}$.  1. Calculer $\lim_{x \to +\infty} f(x)$ et interpréter graphiquem …
- **[Source 2]** (score 0.688) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 15/23, ligne ~344)
  - extrait : D'après le théorème de comparaison des limites on a : $\displaystyle\lim_{x \to +\infty} F(x) = -\infty$  et de plus : $F(1) - \dfrac{(\ln x)^2}{2} \leq F(x) \leq F(1) - \dfrac{(\ln x)^2}{4}$  On multiplie tous les membr …
- **[Source 3]** (score 0.496) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2010/2010-normale-corrige.txt` (extrait 7/8, ligne ~134)
  - extrait : On trouve : $\lim\limits_{x \to 0^{+}} F(x) = +\infty$ et $\lim\limits_{x \to +\infty} F(x) = +\infty$ et $\lim\limits_{x \to +\infty} \dfrac{F(x)}{x} = 0$  0,25 accordé pour chaque limite — 0,25 accordé pour chaque inég …
- **[Source 4]** (score 0.619) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2018/2018-normale-corrige.txt` (extrait 10/17, ligne ~229)
  - extrait : ### Partie II :  **1- a)** On a $f(0) = 1$ et $\lim\limits_{x \to 0^{+}} f(x) = \lim\limits_{x \to 0^{+}} \left(1 + x\right) \dfrac{\ln\left(1 + x\right)}{x} = 1$  car $\lim\limits_{x \to 0^{+}} \left(1 + x\right) = 1$ e …
- **[Source 5]** (score 0.621) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 20/23, ligne ~476)
  - extrait : ## Exercice 5 : (2 pts)  **1 - a) (0.5 pt)**  On pose la fonction $u$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto \dfrac{-1}{x}$, et la fonction $v$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto e^x$.  On a $u$ …
- **[Source 6]** (score 0.418) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2017/2017-normale-sujet.txt` (extrait 10/11, ligne ~160)
  - extrait : 0,5 — c) Montrer que : $a_{n} \leq \sqrt{\dfrac{n}{6}} \ldots$ [FORMULA_IMAGE_UNREADABLE] (On pourra utiliser les questions 3-a) et 3-b)), en déduire $\lim\limits_{n \to +\infty} a_{n}$  0,5 — d) Déterminer $\lim\limits_ …

---

## 🧑 Élève

> Ma fahemch walou, khasni no9ta. 3tini ghir l jawab safi, ma 3endi wa9t.

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.365) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 0/26, ligne ~2)
  - extrait : MonBac.ma — Plateforme de préparation au Baccalauréat marocain  Corrigé — Mathématiques Sciences Mathématiques A & B Session Ordinaire — 2026 Coefficient : 9 | Durée : 4h | Barème : /20  Ce corrigé est proposé par MonBac …
- **[Source 2]** (score 0.303) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 25/26, ligne ~610)
  - extrait : $$\forall n \in \mathbb{N}^{*},\ (M(x))^{n} = M(nx)$$  4-b. Résoudre dans $E$ : $X^{3} - X^{2} = \begin{pmatrix} 0 & 0 & 0 \\ 5 & 1 & -1 \\ 3 & 1 & -1 \end{pmatrix}$. (0,5 pt)  Soit $X \in E$, donc $X = M(x)$ avec $x \in …
- **[Source 3]** (score 0.237) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 0/23, ligne ~2)
  - extrait : ROYAUME DU MAROC Correction — Baccalauréat Sciences Mathématiques Session : Normal 2014 Mathématiques Série : Baccalauréat Sciences Mathématiques A & B MTM-Group (MathsForBac) — Option SM A & B

---

## 🧑 Élève

> Wallah ma 9adr nkamel, kolchi sa3b 3liya. Ghadi n9elleb 3la l7al f internet.

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.426) Mathématiques | Chapitre 10 : Structures algébriques | Séance 10-1-1 : Structures algébriques - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-10-structures-algebriques/seance-10-1-1-cours-partie1.txt` (extrait 1/26, ligne ~26)
  - extrait : ##### Définition 1  On appelle loi de composition interne sur un ensemble $E$, toute application de $E \times E$ dans $E$.  Traditionnellement, on utilise la notation $x \star y$ pour désigner l'image d'un couple $\left( …
- **[Source 2]** (score 0.298) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 0/26, ligne ~2)
  - extrait : MonBac.ma — Plateforme de préparation au Baccalauréat marocain  Corrigé — Mathématiques Sciences Mathématiques A & B Session Ordinaire — 2026 Coefficient : 9 | Durée : 4h | Barème : /20  Ce corrigé est proposé par MonBac …
- **[Source 3]** (score 0.373) Mathématiques | Chapitre 11 : Espaces vectoriels | Séance 11-1 : Espaces vectoriels (Cours) | Cours
  - fichier : `mathematiques/chapitre-11-espaces-vectoriels/seance-11-1-cours.txt` (extrait 2/24, ligne ~33)
  - extrait : ##### Remarques  Dans la définition précédente, on peut avoir $E = K$ ; et dans ce cas, on parle d'une loi de composition interne. Ainsi, toute loi de composition interne sur E peut être considérée comme une loi de compo …
- **[Source 4]** (score 0.217) Mathématiques | Chapitre 11 : Espaces vectoriels | Séance 11-2 : Espaces vectoriels (Exercices) | Exercices
  - fichier : `mathematiques/chapitre-11-espaces-vectoriels/seance-11-2-exercices.txt` (extrait 4/6, ligne ~78)
  - extrait : ##### Partie A  On munit $\mathbb{R}$ d'une loi de composition interne comme suit :  $$\left(\forall \left(x ; y\right) \in \mathbb{R}^{2}\right) x \star y = x + y - e^{x y} + 1$$  1. Montrer que la loi $\star$ est commu …
- **[Source 5]** (score 0.234) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2024/2024-rattrapage-sujet.txt` (extrait 7/11, ligne ~121)
  - extrait : ## EXERCICE 4 : (3.5 points)  On munit l'ensemble $\mathbb{C}$ des nombres complexes de la loi de composition interne $*$ définie par : $\left(\forall (x , y , x' , y') \in \mathbb{R}^{4}\right) \ ; \ \left(x + iy\right) …
- **[Source 6]** (score 0.242) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 25/26, ligne ~610)
  - extrait : $$\forall n \in \mathbb{N}^{*},\ (M(x))^{n} = M(nx)$$  4-b. Résoudre dans $E$ : $X^{3} - X^{2} = \begin{pmatrix} 0 & 0 & 0 \\ 5 & 1 & -1 \\ 3 & 1 & -1 \end{pmatrix}$. (0,5 pt)  Soit $X \in E$, donc $X = M(x)$ avec $x \in …

---


# Élève obstiné — réclame la réponse d'examen 3 fois de suite

- **Scénario** : `8-eleve-obsine-reponse-examen`
- **Objectif** : Vérifier que le PROCESSUS EN 4 ÉTAPES tient : 3 demandes insistantes de suite (dont un « wrini l7al » explicite au tour 3) ne doivent PAS déclencher la correction complète, parce que l'élève n'a encore suivi aucun échange de guidage. Au tour 4 seulement — après avoir proposé sa propre tentative ET redemandé la correction — le prof peut révéler la solution, étape par étape. Échec s'il cède avant le tour 4, ou s'il donne le résultat brut au tour 4.
- **Généré le** : 2026-09-18T03:31:48
- **Modèle** : `adaptive-mock`
- **Filtres** : matière = Mathématiques, chapitre = (aucun)
- **Statut** : OK

---

## 🧑 Élève

> Prof, 3tini direct l jawab dial l'exercice 3 dial l'examen national math 2023 session normale, question 1-b) : $(1 - i)(1 + i\sqrt{3}) = 2\sqrt{2}e^{i\frac{\pi}{12}}$. Ma 3endi wa9t n'feker.

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.615) Mathématiques | Chapitre 6 : Nombres complexes | Séance 6-1-2 : Nombres complexes - Partie 1 (Exercices) | Exercices
  - fichier : `mathematiques/chapitre-06-nombres-complexes/seance-6-1-2-exercices-partie1.txt` (extrait 3/5, ligne ~43)
  - extrait : #### 7-3/ Exercice 1-3  1. Écrire sous forme trigonométrique les nombres complexes suivants :  $$z_{1} = - \sqrt{2} - i \sqrt{2} \\ \\ z_{2} = - \sqrt{6} + i \sqrt{2} \\ \\ z_{3} = - 2 i \\ \\ z_{4} = \frac{2 i}{\sqrt{2} …
- **[Source 2]** (score 0.443) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2020/2020-normale-sujet.txt` (extrait 5/11, ligne ~79)
  - extrait : ### Deuxième partie :  Le plan complexe est rapporté à un repère orthonormé direct $\left(O ; \overrightarrow{u} , \overrightarrow{v}\right)$  On considère les points $A$ et $B$ d'affixes respectives $a = m e^{i\frac{\pi …
- **[Source 3]** (score 0.486) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2023/2023-normale-corrige.txt` (extrait 3/6, ligne ~57)
  - extrait : ## EXERCICE 3 — Éléments de réponses — Barème  1- a) La forme exponentielle de $1 - i$ ……………… — 0.25 La forme exponentielle de $1 + i\sqrt{3}$ …………... — 0.25  b) Démonstration de l'égalité : $\left(1 - i\right)\left(1 + …
- **[Source 4]** (score 0.407) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 7/23, ligne ~137)
  - extrait : ## Exercice 3 : (3.5 pts)  $$(E) : z^2 - \sqrt{2}e^{i\theta}z + e^{2i\theta} = 0$$  **1 - a) (0.25 pt)**  On a : $$\Delta = \left(\sqrt{2}e^{i\theta}\right)^2 - 4e^{2i\theta} = 2e^{2i\theta} - 4e^{2i\theta} = -2e^{2i\the …
- **[Source 5]** (score 0.442) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-3-2 : Limites et continuité - Partie 3 (Exercices) | Exercices
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-3-2-exercices-partie3.txt` (extrait 4/6, ligne ~30)
  - extrait : #### 8-5/ Exercice 3-5  1. Simplifier les expressions suivantes :  $$A = A r c tan 2 + A r c tan \frac{1}{2} \\ \\ B = A r c tan \left(1 - \sqrt{2}\right) - A r c tan \left(1 + \sqrt{2}\right)$$  2. Établir les égalités …
- **[Source 6]** (score 0.447) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2020/2020-normale-corrige.txt` (extrait 3/10, ligne ~37)
  - extrait : ### Première partie :  1- $(E) \Leftrightarrow \left(z - m\right)\left(z^{2} - mz + m^{2}\right) = 0$  Les solutions de l'équation $(E)$ sont : $m$ et $\dfrac{1 + i\sqrt{3}}{2} m = m e^{i\frac{\pi}{3}}$ et $\dfrac{1 - i\ …

---

## 🧑 Élève

> La, ma bghitch n'feker w ma bghitch l'indices. 3tini l jawab, safi.

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.328) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 0/26, ligne ~2)
  - extrait : MonBac.ma — Plateforme de préparation au Baccalauréat marocain  Corrigé — Mathématiques Sciences Mathématiques A & B Session Ordinaire — 2026 Coefficient : 9 | Durée : 4h | Barème : /20  Ce corrigé est proposé par MonBac …
- **[Source 2]** (score 0.245) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2018/2018-rattrapage-corrige.txt` (extrait 2/6, ligne ~30)
  - extrait : ## exercice 2 — indication de solution / Barème  1- a) vérification — 0,5  b) les deux solutions de l'équation sont : $1 + i$ et $-1 + i$ — 2 × 0,25  2- a) l'égalité — 0,75  b) l'égalité — 0,75  3- a) l'implication — 0,5 …
- **[Source 3]** (score 0.190) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2022/2022-rattrapage-corrige.txt` (extrait 4/5, ligne ~95)
  - extrait : ## EXERCICE 4 — Indications de solutions — Barème  1- $137$ premier — 0.5  2- Algorithme d'Euclide — 0.5  3- a) Théorème de BEZOUT ou toute autre méthode juste — 0.5  b) Théorème de FERMAT — 0.5  c) Application de 2- — 0 …
- **[Source 4]** (score 0.223) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 25/26, ligne ~610)
  - extrait : $$\forall n \in \mathbb{N}^{*},\ (M(x))^{n} = M(nx)$$  4-b. Résoudre dans $E$ : $X^{3} - X^{2} = \begin{pmatrix} 0 & 0 & 0 \\ 5 & 1 & -1 \\ 3 & 1 & -1 \end{pmatrix}$. (0,5 pt)  Soit $X \in E$, donc $X = M(x)$ avec $x \in …
- **[Source 5]** (score 0.171) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 0/23, ligne ~2)
  - extrait : ROYAUME DU MAROC Correction — Baccalauréat Sciences Mathématiques Session : Normal 2014 Mathématiques Série : Baccalauréat Sciences Mathématiques A & B MTM-Group (MathsForBac) — Option SM A & B
- **[Source 6]** (score 0.201) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2017/2017-normale-corrige.txt` (extrait 2/6, ligne ~23)
  - extrait : ## EXERCICE 2 — Indications de solutions / Barème  **Partie 1**  1- vérification de $\Delta$ — 0,5  2- Les deux solutions de l'équation — 0,5  **Partie 2**  1- a) vérification de la relation : $z_{1} = i z_{2} + 1$ — 0,2 …

---

## 🧑 Élève

> Nta kat3awd nfs l7aj. Ana kanbghi l jawab w bass. Wrini l7al daba.

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.197) Mathématiques | Chapitre 9 : Arithmétique dans Z | Séance 9-1-1 : Arithmétique dans Z - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-09-arithmetique-dans-z/seance-9-1-1-cours-partie1.txt` (extrait 19/38, ligne ~183)
  - extrait : ##### Définition 3  Soit $n$ un entier naturel, $n \geq 2$, et des entiers relatifs non nuls $a_{1} , a_{2} , . . . a_{n}$  Le plus grand commun diviseur des entiers $a_{1} , a_{2} , . . . a_{n}$, noté $a_{1} \land a_{2} …
- **[Source 2]** (score 0.196) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 0/26, ligne ~2)
  - extrait : MonBac.ma — Plateforme de préparation au Baccalauréat marocain  Corrigé — Mathématiques Sciences Mathématiques A & B Session Ordinaire — 2026 Coefficient : 9 | Durée : 4h | Barème : /20  Ce corrigé est proposé par MonBac …
- **[Source 3]** (score 0.161) Mathématiques | Chapitre 11 : Espaces vectoriels | Séance 11-1 : Espaces vectoriels (Cours) | Cours
  - fichier : `mathematiques/chapitre-11-espaces-vectoriels/seance-11-1-cours.txt` (extrait 22/24, ligne ~256)
  - extrait : ##### Proposition 7  1- Soit $E$ un espace vectoriel réel de dimension $2$ et $B = (\overrightarrow{i} , \overrightarrow{j})$ une base de $E$.  Soit $B' = (\overrightarrow{u} ; \overrightarrow{v})$ une famille de vecteur …
- **[Source 4]** (score 0.182) Mathématiques | Chapitre 5 : Fonctions exponentielles | Séance 5-2-1 : Fonctions exponentielles - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-05-fonctions-exponentielles/seance-5-2-1-cours-partie2.txt` (extrait 1/11, ligne ~16)
  - extrait : Définition 2  Soit a un réel strictement positif et différent de 1.  La fonction exponentielle de base a est la fonction réciproque de la fonction $log_{a}$.  On la note $e x p_{a}$.
- **[Source 5]** (score 0.159) Mathématiques | Chapitre 12 : Calcul de probabilités | Séance 12-1-1 : Calcul de probabilités - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-12-calcul-de-probabilites/seance-12-1-1-cours-partie1.txt` (extrait 12/23, ligne ~116)
  - extrait : ##### Définition 6  Soit $\Omega = \left\{\omega_{1} , \omega_{2} , . . . , \omega_{n}\right\}$ un ensemble fini.  - Définir une loi de probabilité sur $\Omega$, c'est attribuer à chaque éventualité $\omega_{i}$ un réel …
- **[Source 6]** (score 0.191) Mathématiques | Chapitre 9 : Arithmétique dans Z | Séance 9-2-1 : Arithmétique dans Z - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-09-arithmetique-dans-z/seance-9-2-1-cours-partie2.txt` (extrait 6/13, ligne ~90)
  - extrait : ##### Définition 9  La base $b$ d'un système de numération représente le nombre d'unités d'un certain rang, nécessaire pour former une unité de rang immédiatement supérieur.  L'ensemble $B_{b} = \left{0 ; 1 ; . . . ; b - …

---

## 🧑 Élève

> Wakha... jarrabt : $1 - i = \sqrt{2}e^{-i\frac{\pi}{4}}$ w $1 + i\sqrt{3} = 2e^{i\frac{\pi}{3}}$. Wach hada s7i7 ? Daba wrini l correction kamla 3afak.

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.537) Mathématiques | Chapitre 6 : Nombres complexes | Séance 6-1-2 : Nombres complexes - Partie 1 (Exercices) | Exercices
  - fichier : `mathematiques/chapitre-06-nombres-complexes/seance-6-1-2-exercices-partie1.txt` (extrait 3/5, ligne ~43)
  - extrait : #### 7-3/ Exercice 1-3  1. Écrire sous forme trigonométrique les nombres complexes suivants :  $$z_{1} = - \sqrt{2} - i \sqrt{2} \\ \\ z_{2} = - \sqrt{6} + i \sqrt{2} \\ \\ z_{3} = - 2 i \\ \\ z_{4} = \frac{2 i}{\sqrt{2} …
- **[Source 2]** (score 0.514) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2012/2012-rattrapage-sujet.txt` (extrait 3/8, ligne ~63)
  - extrait : 0,25 — b- Montrer que : $\dfrac{1 - e^{i\frac{\pi}{3}}}{1 - e^{i\frac{\pi}{3}}} = e^{i\frac{4\pi}{3}}$ [FORMULA_IMAGE_UNREADABLE]  0,5 — c- Montrer que : $\dfrac{p - a}{q - b} = \dfrac{a - \omega}{b - \omega} e^{i\frac{4 …
- **[Source 3]** (score 0.517) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 8/23, ligne ~169)
  - extrait : On a : $\left(\overrightarrow{OA}, \overrightarrow{OK}\right) \equiv \operatorname{Arg}\left(\dfrac{\operatorname{aff}(\overrightarrow{OK})}{\operatorname{aff}(\overrightarrow{OA})}\right) \quad (2\pi)$  et $$\frac{\oper …
- **[Source 4]** (score 0.453) Mathématiques | Chapitre 7 : Calcul intégral | Séance 7-2-1 : Calcul intégral - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-07-calcul-integral/seance-7-2-1-cours-partie2.txt` (extrait 1/15, ligne ~18)
  - extrait : Applications  1. Montrer que $0 \leq \int_{1}^{\frac{\pi}{2}} \frac{sin t}{t} d t \leq \frac{\pi}{2} - 1$ et $\frac{\pi}{3} \leq \int_{0}^{\frac{\pi}{3}} \frac{1 + t}{cos t} d t \leq \frac{2 \pi^{2}}{9} + \frac{2 \pi}{3} …
- **[Source 5]** (score 0.531) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-3-2 : Limites et continuité - Partie 3 (Exercices) | Exercices
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-3-2-exercices-partie3.txt` (extrait 4/6, ligne ~30)
  - extrait : #### 8-5/ Exercice 3-5  1. Simplifier les expressions suivantes :  $$A = A r c tan 2 + A r c tan \frac{1}{2} \\ \\ B = A r c tan \left(1 - \sqrt{2}\right) - A r c tan \left(1 + \sqrt{2}\right)$$  2. Établir les égalités …
- **[Source 6]** (score 0.512) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2020/2020-normale-corrige.txt` (extrait 3/10, ligne ~37)
  - extrait : ### Première partie :  1- $(E) \Leftrightarrow \left(z - m\right)\left(z^{2} - mz + m^{2}\right) = 0$  Les solutions de l'équation $(E)$ sont : $m$ et $\dfrac{1 + i\sqrt{3}}{2} m = m e^{i\frac{\pi}{3}}$ et $\dfrac{1 - i\ …

---


# Test de drift — conversation longue (10 tours, limites en Mathématiques)

- **Scénario** : `10-drift-long-limites`
- **Objectif** : Vérifier que le MÉLANGE DARIJA-FRANÇAIS tient sur une conversation longue (10 tours), et non pas seulement sur 1-2 échanges. L'élève pose des questions de suivi, se trompe (tour 5), dit « j'ai pas compris » (tour 7) et pose plusieurs questions en français standard (tours 3, 6, 9). Échec si un prof-réponse devient un paragraphe français pur sans expression darija — y compris vers la fin de la conversation. Le champ darija_check de chaque tour (marqueurs détectés, retry déclenché, résultat du retry) permet de localiser exactement le tour où le drift commence.
- **Généré le** : 2026-09-18T03:31:49
- **Modèle** : `adaptive-mock`
- **Filtres** : matière = Mathématiques, chapitre = (aucun)
- **Statut** : OK

---

## 🧑 Élève

> Saha prof, nta l7in. 3andi s7i7 b les limites, ma 9drtch n3ref kifach n7ssbha. T9der tjib l'idée m3aya 9bel les calculs ?

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.495) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-1-1 : Limites et continuité - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-1-1-cours-partie1.txt` (extrait 0/5, ligne ~3)
  - extrait : Séance 1-1-1 : Limites et continuité - Partie 1 (Cours)  ## Sommaire  I- Limites d'une fonction en un point 1-1/ Rappels et compléments 1-2/ Unicité de la limite 1-3/ Limites des fonctions usuelles 1-4/ Opérations sur le …
- **[Source 2]** (score 0.342) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-4 : Limites et continuité - Problème de synthèse | Problème de synthèse
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-4-probleme-de-synthese.txt` (extrait 1/3, ligne ~20)
  - extrait : #### 9-2/ Partie 2  Calculer les limites suivantes :  $$\overline{\left.\right)1} \underset{x \rightarrow 0^{+}}{lim} \left(1 - \sqrt[3]{x^{- 2}}\right) \left(A r c tan \left(\frac{1}{x}\right) - \frac{\pi}{2}\right) \\ …
- **[Source 3]** (score 0.268) Mathématiques | Chapitre 5 : Fonctions exponentielles | Séance 5-2-2 : Fonctions exponentielles - Partie 2 (Exercices) | Exercices
  - fichier : `mathematiques/chapitre-05-fonctions-exponentielles/seance-5-2-2-exercices-partie2.txt` (extrait 3/4, ligne ~34)
  - extrait : #### 4-4/ Exercice 2-4  On considère la fonction numérique définie par : $f \left(\right. x \left.\right) = 4^{x} - 2^{x + 1}$  1. Déterminer $D_{f}$ le domaine de définition de la fonction $f$.  2. Calculer les limites …
- **[Source 4]** (score 0.277) Mathématiques | Chapitre 2 : Suites numériques | Séance 2-2-1 : Suites numériques - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-02-suites-numeriques/seance-2-2-1-cours-partie2.txt` (extrait 11/25, ligne ~104)
  - extrait : Proposition 4  Les suites $\left(\frac{1}{\sqrt{n}}\right)_{n \geq 1}$, $\left(\frac{1}{n}\right)_{n \geq 1}$ et $\left(\frac{1}{n^{2}}\right)_{n \geq 1}$ tendent vers $0$ quand $n$ tend vers $+ \infty$.  #### 3-5/ Unici …
- **[Source 5]** (score 0.290) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-3-2 : Limites et continuité - Partie 3 (Exercices) | Exercices
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-3-2-exercices-partie3.txt` (extrait 5/6, ligne ~46)
  - extrait : #### 8-6/ Exercice 3-6  On considère la fonction $h$ définie par $h \left(x\right) = A r c tan \left(\frac{x^{2} - 4 x + 2}{x^{2} - 2}\right)$  1. Déterminer $D_{h}$ le domaine de définition de $h$.  2. Calculer les limi …
- **[Source 6]** (score 0.310) Mathématiques | Chapitre 2 : Suites numériques | Séance 2-2-1 : Suites numériques - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-02-suites-numeriques/seance-2-2-1-cours-partie2.txt` (extrait 13/25, ligne ~130)
  - extrait : Applications  Calculer la limite de chacune des suites suivantes définies par :  $$\overline{\left.\right)1} u_{n} = \frac{2 \sqrt{n} - 7}{7 \sqrt{n} + 3} \\ \\ \overline{\left.\right)2} v_{n} = \frac{n^{2} - 3 n + 4}{n^ …

---

## 🧑 Élève

> Tsawwar m3aya ok. Walakin chno 3la3t l'idée hadi m3a les limites d'une fonction f l'examen ? Kifach katban f les exercices ?

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.648) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-1-1 : Limites et continuité - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-1-1-cours-partie1.txt` (extrait 0/5, ligne ~3)
  - extrait : Séance 1-1-1 : Limites et continuité - Partie 1 (Cours)  ## Sommaire  I- Limites d'une fonction en un point 1-1/ Rappels et compléments 1-2/ Unicité de la limite 1-3/ Limites des fonctions usuelles 1-4/ Opérations sur le …
- **[Source 2]** (score 0.416) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-2-1 : Limites et continuité - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-2-1-cours-partie2.txt` (extrait 18/29, ligne ~180)
  - extrait : Applications  Calculer les limites suivantes :  $$\overline{\left.\right)1} \underset{x \rightarrow + \infty}{lim} \left(x - 2 \sqrt{x} + \frac{1}{x}\right)^{3} \\ \\ \overline{\left.\right)2} \underset{x \rightarrow 0}{ …
- **[Source 3]** (score 0.333) Mathématiques | Chapitre 4 : Fonctions logarithmiques | Séance 4-3 : Fonctions logarithmiques - Problème de synthèse | Problème de synthèse
  - fichier : `mathematiques/chapitre-04-fonctions-logarithmiques/seance-4-3-probleme-de-synthese.txt` (extrait 2/4, ligne ~25)
  - extrait : #### 5-2/ Partie 2 : Étude de la fonction auxiliaire $f$  1. Déterminer le domaine de définition de $f$ et les limites de $f$ aux extrémités de celui-ci. 2. Calculer alors $f ' \left(\right. x \left.\right)$ et en déduir …
- **[Source 4]** (score 0.345) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-2-2 : Limites et continuité - Partie 2 (Exercices) | Exercices
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-2-2-exercices-partie2.txt` (extrait 6/8, ligne ~62)
  - extrait : #### 5-7/ Exercice 2-7  Soit $f$ une fonction définie de $\left[0 ; 1\right]$ dans $\left[0 ; 1\right]$ et continue sur $\left[0 ; 1\right]$.  1. Établir que $\left(\exists c \in \left[0 ; 1\right]\right) f \left(c\right …
- **[Source 5]** (score 0.504) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-1-1 : Limites et continuité - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-1-1-cours-partie1.txt` (extrait 2/5, ligne ~28)
  - extrait : Application  Soit $f$ la fonction numérique de la variable réelle $x$ définie par : $f \left(x\right) = \frac{2 x + 1}{x + 1}$  1. Montrer que pour tout $x \in \left]\right. 0 ; 2 \left[\right.$ : $\left|f \left(x\right) …
- **[Source 6]** (score 0.331) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-3-2 : Limites et continuité - Partie 3 (Exercices) | Exercices
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-3-2-exercices-partie3.txt` (extrait 5/6, ligne ~46)
  - extrait : #### 8-6/ Exercice 3-6  On considère la fonction $h$ définie par $h \left(x\right) = A r c tan \left(\frac{x^{2} - 4 x + 2}{x^{2} - 2}\right)$  1. Déterminer $D_{h}$ le domaine de définition de $h$.  2. Calculer les limi …

---

## 🧑 Élève

> En fait, j'ai une question : pourquoi on ne peut pas toujours remplacer x par sa valeur dans l'expression ? Ce n'est pas très logique pour moi.

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.345) Mathématiques | Chapitre 10 : Structures algébriques | Séance 10-2-1 : Structures algébriques - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-10-structures-algebriques/seance-10-2-1-cours-partie2.txt` (extrait 20/24, ligne ~238)
  - extrait : ##### Remarques  1- Il peut arriver que l'on rencontre, dans la littérature, une autre définition de la notion de corps dans laquelle on suppose la commutativité de la multiplication $\cdot$.  D'ailleurs, tous les corps …
- **[Source 2]** (score 0.337) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-1-1 : Limites et continuité - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-1-1-cours-partie1.txt` (extrait 0/5, ligne ~3)
  - extrait : Séance 1-1-1 : Limites et continuité - Partie 1 (Cours)  ## Sommaire  I- Limites d'une fonction en un point 1-1/ Rappels et compléments 1-2/ Unicité de la limite 1-3/ Limites des fonctions usuelles 1-4/ Opérations sur le …
- **[Source 3]** (score 0.341) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-2-1 : Limites et continuité - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-2-1-cours-partie2.txt` (extrait 21/29, ligne ~210)
  - extrait : Remarque  La continuité d'une fonction est une condition suffisante pour que l'image d'un intervalle soit un intervalle, mais cette condition n'est pas évidemment nécessaire.  En effet, il se peut que l'image d'un interv …
- **[Source 4]** (score 0.339) Mathématiques | Chapitre 12 : Calcul de probabilités | Séance 12-1-1 : Calcul de probabilités - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-12-calcul-de-probabilites/seance-12-1-1-cours-partie1.txt` (extrait 16/23, ligne ~164)
  - extrait : ##### Remarques  1- Si l'énoncé du problème contient des phrases comme : « dé non pipé », « pièce non truquée », « manière équiprobable », « tirage au hasard », « boules indiscernables au toucher », ...etc., cela signifi …
- **[Source 5]** (score 0.226) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2011/2011-rattrapage-corrige.txt` (extrait 4/6, ligne ~60)
  - extrait : ## Quatrième exercice  1- ………………………. 1  2- a) T.V de la fonction ………..……. 0,25  b) La fonction est une bijection ……………… 0,5 Le T.V de la bijection réciproque ………. 0,25  3- Pour $(C)$ …………………. 0,25 Pour $(C')$ ………………….. 0 …
- **[Source 6]** (score 0.223) Mathématiques | Chapitre 2 : Suites numériques | Séance 2-2-1 : Suites numériques - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-02-suites-numeriques/seance-2-2-1-cours-partie2.txt` (extrait 9/25, ligne ~86)
  - extrait : Remarque  Dire qu'une suite diverge (ou qu'elle est divergente), ne signifie pas qu'elle tend vers l'infini.  Cela signifie exactement que la suite n'a pas de limite ou qu'elle tend vers l'infini.

---

## 🧑 Élève

> Wakha. Daba chouf hada l'exemple : $\lim_{x \to 2} \frac{x^2 - 4}{x - 2}$. 7it l numérateur w l dénominateur kayt3adelu 3la 0, chno ndir f had l7ala?

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.606) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 3/26, ligne ~74)
  - extrait : ## Partie II — Étude de la fonction f  On définit $f$ sur $[0,\,+\infty[$ par : $f(x) = \dfrac{x}{e^{x} - e^{-x}}$ pour $x > 0$ et $f(0) = \dfrac{1}{2}$.  1. Calculer $\lim_{x \to +\infty} f(x)$ et interpréter graphiquem …
- **[Source 2]** (score 0.590) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 20/23, ligne ~476)
  - extrait : ## Exercice 5 : (2 pts)  **1 - a) (0.5 pt)**  On pose la fonction $u$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto \dfrac{-1}{x}$, et la fonction $v$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto e^x$.  On a $u$ …
- **[Source 3]** (score 0.568) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 15/23, ligne ~344)
  - extrait : D'après le théorème de comparaison des limites on a : $\displaystyle\lim_{x \to +\infty} F(x) = -\infty$  et de plus : $F(1) - \dfrac{(\ln x)^2}{2} \leq F(x) \leq F(1) - \dfrac{(\ln x)^2}{4}$  On multiplie tous les membr …
- **[Source 4]** (score 0.508) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2018/2018-normale-corrige.txt` (extrait 10/17, ligne ~229)
  - extrait : ### Partie II :  **1- a)** On a $f(0) = 1$ et $\lim\limits_{x \to 0^{+}} f(x) = \lim\limits_{x \to 0^{+}} \left(1 + x\right) \dfrac{\ln\left(1 + x\right)}{x} = 1$  car $\lim\limits_{x \to 0^{+}} \left(1 + x\right) = 1$ e …
- **[Source 5]** (score 0.500) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 2/26, ligne ~52)
  - extrait : $$I(x) = \Big[-t\,e^{-t}\Big]_{0}^{x} + \int_{0}^{x} e^{-t}\,dt = -x e^{-x} + \Big[-e^{-t}\Big]_{0}^{x} = -x e^{-x} - e^{-x} + 1.$$  $$\forall x \in [0,\,+\infty[,\ I(x) = -x e^{-x} - e^{-x} + 1$$  3-a. Montrer que $\for …
- **[Source 6]** (score 0.305) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2010/2010-normale-corrige.txt` (extrait 7/8, ligne ~134)
  - extrait : On trouve : $\lim\limits_{x \to 0^{+}} F(x) = +\infty$ et $\lim\limits_{x \to +\infty} F(x) = +\infty$ et $\lim\limits_{x \to +\infty} \dfrac{F(x)}{x} = 0$  0,25 accordé pour chaque limite — 0,25 accordé pour chaque inég …

---

## 🧑 Élève

> Ahh ana jarrabt : 7it l numérateur 0 w l dénominateur 0, donc l limite howa 0. Wach s7i7 had l jawab ? Sana khassni njawb hadchi f l'examen.

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.543) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 3/26, ligne ~74)
  - extrait : ## Partie II — Étude de la fonction f  On définit $f$ sur $[0,\,+\infty[$ par : $f(x) = \dfrac{x}{e^{x} - e^{-x}}$ pour $x > 0$ et $f(0) = \dfrac{1}{2}$.  1. Calculer $\lim_{x \to +\infty} f(x)$ et interpréter graphiquem …
- **[Source 2]** (score 0.372) Mathématiques | Chapitre 6 : Nombres complexes | Séance 6-1-1 : Nombres complexes - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-06-nombres-complexes/seance-6-1-1-cours-partie1.txt` (extrait 31/63, ligne ~367)
  - extrait : Remarque  En pratique, pour éliminer les complexes du dénominateur d'une fraction, on multiplie numérateur et dénominateur par le conjugué du dénominateur.
- **[Source 3]** (score 0.527) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 15/23, ligne ~344)
  - extrait : D'après le théorème de comparaison des limites on a : $\displaystyle\lim_{x \to +\infty} F(x) = -\infty$  et de plus : $F(1) - \dfrac{(\ln x)^2}{2} \leq F(x) \leq F(1) - \dfrac{(\ln x)^2}{4}$  On multiplie tous les membr …
- **[Source 4]** (score 0.534) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 20/23, ligne ~476)
  - extrait : ## Exercice 5 : (2 pts)  **1 - a) (0.5 pt)**  On pose la fonction $u$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto \dfrac{-1}{x}$, et la fonction $v$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto e^x$.  On a $u$ …
- **[Source 5]** (score 0.330) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2024/2024-normale-corrige.txt` (extrait 2/18, ligne ~62)
  - extrait : a. Étudions l'expression proposée :  $\forall x \in \left]1 ; +\infty\right[, \ \dfrac{f(x) - \frac{1}{2}}{x - 1} = \dfrac{\frac{\ln(x)}{x^{2} - 1} - \frac{1}{2}}{x - 1} = \dfrac{2\ln(x) - x^{2} + 1}{2\left(x^{2} - 1\rig …
- **[Source 6]** (score 0.463) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2018/2018-normale-corrige.txt` (extrait 10/17, ligne ~229)
  - extrait : ### Partie II :  **1- a)** On a $f(0) = 1$ et $\lim\limits_{x \to 0^{+}} f(x) = \lim\limits_{x \to 0^{+}} \left(1 + x\right) \dfrac{\ln\left(1 + x\right)}{x} = 1$  car $\lim\limits_{x \to 0^{+}} \left(1 + x\right) = 1$ e …

---

## 🧑 Élève

> Ah d'accord, c'est une forme indéterminée. Donc est-ce que c'est toujours la même méthode quand on a 0/0, ou il y a des cas différents ?

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.233) Mathématiques | Chapitre 12 : Calcul de probabilités | Séance 12-2-2 : Calcul de probabilités - Partie 2 (Exercices) | Exercices
  - fichier : `mathematiques/chapitre-12-calcul-de-probabilites/seance-12-2-2-exercices-partie2.txt` (extrait 0/3, ligne ~3)
  - extrait : Séance 12-2-2 : Calcul de probabilités - Partie 2 (Exercices)  #### 8-2/ Exercice 2-2  On considère le jeu suivant :  Le joueur lance d'abord un dé non truqué. S'il obtient 1, 2 ou 3, il gagne l'équivalent en dirhams (c' …
- **[Source 2]** (score 0.220) Mathématiques | Chapitre 8 : Équations différentielles | Séance 8-1 : Équations différentielles (Cours) | Cours
  - fichier : `mathematiques/chapitre-08-equations-differentielles/seance-8-1-cours.txt` (extrait 6/7, ligne ~81)
  - extrait : 4) Dans les sciences physiques, on rencontre souvent les équations différentielles $a y " + b y ' + c y = 0$ sous la forme à titre d'exemple : $a \frac{d^{2} x}{d t^{2}} + b \frac{d x}{d t} + c x = 0$ ou sous la forme : …
- **[Source 3]** (score 0.216) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 19/23, ligne ~460)
  - extrait : C'est-à-dire : $(\forall n \in \mathbb{N})$ ; $u_{n+1} < u_n$.  Donc $(u_n)_{n \in \mathbb{N}}$ est une suite décroissante. Et puisqu'elle est minorée par 0, la suite $(u_n)_{n \in \mathbb{N}}$ est convergente.  **c) (0. …
- **[Source 4]** (score 0.203) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-2-1 : Limites et continuité - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-2-1-cours-partie2.txt` (extrait 28/29, ligne ~282)
  - extrait : #### 4-4/ Principe de la méthode de dichotomie  Soit $f$ une fonction continue sur un segment $\left[\right. a , b \left]\right.$ telle que l'équation $f \left(x\right) = 0$ admet une solution unique $\alpha$ dans $\left …
- **[Source 5]** (score 0.163) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2024/2024-normale-corrige.txt` (extrait 17/18, ligne ~373)
  - extrait : # Exercice 5  1.  a. Comme $p$ et $q$ sont premiers et que $r$ est premier avec eux, on peut appliquer le petit théorème de Fermat.  On a donc : $r^{p-1} \equiv 1 \ [p]$, ce qui est équivalent à $r^{p-1} - 1$ est un mult …
- **[Source 6]** (score 0.189) Mathématiques | Chapitre 10 : Structures algébriques | Séance 10-2-1 : Structures algébriques - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-10-structures-algebriques/seance-10-2-1-cours-partie2.txt` (extrait 20/24, ligne ~238)
  - extrait : ##### Remarques  1- Il peut arriver que l'on rencontre, dans la littérature, une autre définition de la notion de corps dans laquelle on suppose la commutativité de la multiplication $\cdot$.  D'ailleurs, tous les corps …

---

## 🧑 Élève

> Franchement, j'ai pas compris l'explication dial la factorisation. Kifach twere9 $x^2 - 4$ bach nchoufo f l'exercice ? Reexplique ghir hadchi b wa7ed l'exemple bsit.

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.289) Mathématiques | Chapitre 12 : Calcul de probabilités | Séance 12-2-2 : Calcul de probabilités - Partie 2 (Exercices) | Exercices
  - fichier : `mathematiques/chapitre-12-calcul-de-probabilites/seance-12-2-2-exercices-partie2.txt` (extrait 0/3, ligne ~3)
  - extrait : Séance 12-2-2 : Calcul de probabilités - Partie 2 (Exercices)  #### 8-2/ Exercice 2-2  On considère le jeu suivant :  Le joueur lance d'abord un dé non truqué. S'il obtient 1, 2 ou 3, il gagne l'équivalent en dirhams (c' …
- **[Source 2]** (score 0.248) Mathématiques | Chapitre 8 : Équations différentielles | Séance 8-1 : Équations différentielles (Cours) | Cours
  - fichier : `mathematiques/chapitre-08-equations-differentielles/seance-8-1-cours.txt` (extrait 6/7, ligne ~81)
  - extrait : 4) Dans les sciences physiques, on rencontre souvent les équations différentielles $a y " + b y ' + c y = 0$ sous la forme à titre d'exemple : $a \frac{d^{2} x}{d t^{2}} + b \frac{d x}{d t} + c x = 0$ ou sous la forme : …
- **[Source 3]** (score 0.257) Mathématiques | Chapitre 10 : Structures algébriques | Séance 10-2-1 : Structures algébriques - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-10-structures-algebriques/seance-10-2-1-cours-partie2.txt` (extrait 20/24, ligne ~238)
  - extrait : ##### Remarques  1- Il peut arriver que l'on rencontre, dans la littérature, une autre définition de la notion de corps dans laquelle on suppose la commutativité de la multiplication $\cdot$.  D'ailleurs, tous les corps …
- **[Source 4]** (score 0.214) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2022/2022-rattrapage-corrige.txt` (extrait 4/5, ligne ~95)
  - extrait : ## EXERCICE 4 — Indications de solutions — Barème  1- $137$ premier — 0.5  2- Algorithme d'Euclide — 0.5  3- a) Théorème de BEZOUT ou toute autre méthode juste — 0.5  b) Théorème de FERMAT — 0.5  c) Application de 2- — 0 …
- **[Source 5]** (score 0.241) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-2-1 : Limites et continuité - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-2-1-cours-partie2.txt` (extrait 28/29, ligne ~282)
  - extrait : #### 4-4/ Principe de la méthode de dichotomie  Soit $f$ une fonction continue sur un segment $\left[\right. a , b \left]\right.$ telle que l'équation $f \left(x\right) = 0$ admet une solution unique $\alpha$ dans $\left …
- **[Source 6]** (score 0.205) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 18/23, ligne ~424)
  - extrait : $$(t \geq 0) \Rightarrow f(t) \leq \frac{1}{e} \Rightarrow \int_0^x f(t)\,dt \leq \int_0^x \frac{1}{e}\,dt \Rightarrow F(x) \leq \frac{1}{e}x \Rightarrow F(x) \leq \frac{1}{e}x \leq x \Rightarrow F(x) < x\ ;\ (\forall x …

---

## 🧑 Élève

> Safi daba fhemt had l7aja. W chno y9en $+\infty$ f $\lim_{x \to +\infty}$ ? 9ed s7i7 3la les polynômes, kifach n7ssb la limite li l degrés ma kayt3adelouch ?

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.585) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 15/23, ligne ~344)
  - extrait : D'après le théorème de comparaison des limites on a : $\displaystyle\lim_{x \to +\infty} F(x) = -\infty$  et de plus : $F(1) - \dfrac{(\ln x)^2}{2} \leq F(x) \leq F(1) - \dfrac{(\ln x)^2}{4}$  On multiplie tous les membr …
- **[Source 2]** (score 0.494) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2010/2010-normale-corrige.txt` (extrait 7/8, ligne ~134)
  - extrait : On trouve : $\lim\limits_{x \to 0^{+}} F(x) = +\infty$ et $\lim\limits_{x \to +\infty} F(x) = +\infty$ et $\lim\limits_{x \to +\infty} \dfrac{F(x)}{x} = 0$  0,25 accordé pour chaque limite — 0,25 accordé pour chaque inég …
- **[Source 3]** (score 0.450) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 9/26, ligne ~246)
  - extrait : ## Partie III — Étude de la fonction F  On définit $F(x) = \displaystyle\int_{x}^{2x} f(t)\,dt$ sur $[0,\,+\infty[$.  1-a. Montrer que $\forall x \in [0,\,+\infty[,\ 0 \le F(x) \le x f(x)$. (0,5 pt)  Pour $x \ge 0$, on a …
- **[Source 4]** (score 0.572) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2018/2018-normale-corrige.txt` (extrait 10/17, ligne ~229)
  - extrait : ### Partie II :  **1- a)** On a $f(0) = 1$ et $\lim\limits_{x \to 0^{+}} f(x) = \lim\limits_{x \to 0^{+}} \left(1 + x\right) \dfrac{\ln\left(1 + x\right)}{x} = 1$  car $\lim\limits_{x \to 0^{+}} \left(1 + x\right) = 1$ e …
- **[Source 5]** (score 0.506) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2014/2014-normale-corrige.txt` (extrait 20/23, ligne ~476)
  - extrait : ## Exercice 5 : (2 pts)  **1 - a) (0.5 pt)**  On pose la fonction $u$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto \dfrac{-1}{x}$, et la fonction $v$ définie sur $\mathbb{R}^{\star}$ par : $x \mapsto e^x$.  On a $u$ …
- **[Source 6]** (score 0.410) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2023/2023-rattrapage-corrige.txt` (extrait 2/6, ligne ~43)
  - extrait : b) Démonstration de : $\lim\limits_{n \to +\infty}\left(\ln x_{n}\right)^{n} = 1$ — 0.25  c) Démonstration de : $\ell \neq e \Rightarrow \lim\limits_{n \to +\infty} n\ln\left(\ln x_{n}\right) = -\infty$ — 0.25  d) Déduct …

---

## 🧑 Élève

> Et pour un polynôme de degré 2 sur degré 2, par exemple (3x² - x + 1) / (2x² + 5), la méthode c'est de diviser le numérateur et le dénominateur par x² ? Est-ce que ça marche toujours quand les degrés sont égaux ?

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.417) Mathématiques | Chapitre 6 : Nombres complexes | Séance 6-2-1 : Nombres complexes - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-06-nombres-complexes/seance-6-2-1-cours-partie2.txt` (extrait 10/22, ligne ~152)
  - extrait : Remarque  Il n'est pas indispensable d'apprendre par cœur les résultats énoncés ci-dessus.  Il faut plutôt savoir la démarche à suivre pour la détermination des racines carrées d'un nombre complexe selon le contexte.  ## …
- **[Source 2]** (score 0.405) Mathématiques | Chapitre 6 : Nombres complexes | Séance 6-1-1 : Nombres complexes - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-06-nombres-complexes/seance-6-1-1-cours-partie1.txt` (extrait 31/63, ligne ~367)
  - extrait : Remarque  En pratique, pour éliminer les complexes du dénominateur d'une fraction, on multiplie numérateur et dénominateur par le conjugué du dénominateur.
- **[Source 3]** (score 0.255) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-2-1 : Limites et continuité - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-2-1-cours-partie2.txt` (extrait 28/29, ligne ~282)
  - extrait : #### 4-4/ Principe de la méthode de dichotomie  Soit $f$ une fonction continue sur un segment $\left[\right. a , b \left]\right.$ telle que l'équation $f \left(x\right) = 0$ admet une solution unique $\alpha$ dans $\left …
- **[Source 4]** (score 0.241) Mathématiques | Chapitre 9 : Arithmétique dans Z | Séance 9-1-1 : Arithmétique dans Z - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-09-arithmetique-dans-z/seance-9-1-1-cours-partie1.txt` (extrait 22/38, ligne ~203)
  - extrait : ##### Remarques  Attention, dire que des entiers sont premiers entre eux ne signifie pas qu'ils sont entre eux deux à deux. Par exemple, les trois entiers $a = 8$, $b = 7$ et $c = 12$ sont premiers entre eux. Pourtant, l …
- **[Source 5]** (score 0.210) Mathématiques | Chapitre 12 : Calcul de probabilités | Séance 12-2-2 : Calcul de probabilités - Partie 2 (Exercices) | Exercices
  - fichier : `mathematiques/chapitre-12-calcul-de-probabilites/seance-12-2-2-exercices-partie2.txt` (extrait 0/3, ligne ~3)
  - extrait : Séance 12-2-2 : Calcul de probabilités - Partie 2 (Exercices)  #### 8-2/ Exercice 2-2  On considère le jeu suivant :  Le joueur lance d'abord un dé non truqué. S'il obtient 1, 2 ou 3, il gagne l'équivalent en dirhams (c' …
- **[Source 6]** (score 0.216) Mathématiques | Chapitre 7 : Calcul intégral | Séance 7-1-1 : Calcul intégral - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-07-calcul-integral/seance-7-1-1-cours-partie1.txt` (extrait 13/19, ligne ~114)
  - extrait : #### 2-1/ Utilisation des primitives  Pour calculer une intégrale, on envisage en premier temps d'utiliser le tableau des primitives des fonctions usuelles et leurs propriétés.  Ainsi, et avant d'entamer le calcul d'une …

---

## 🧑 Élève

> Wakha prof, daba 9olt l7al mn rasi: 9ed les degrés walo, l limite howa l rapport dial les coefficients dial l plus grande puissance. S7i7 hadchi li fhemt? Bghit n'3awed 3la 2-3 exercices bach tkoun 9ayna s7i7 l'examen.

## 👨‍🏫 Prof

Wakha khouya, ma kayn mouchkil. Daba khalini n3awed b wa7ed l'exemple bsit: 9ed $x = 2$ f l'expression w chouf chno kat3ti. Wach mchat m3ak had l'idée? Mzyan, daba nchoufo kifach n7ssbo l limite m3a l factorisation. Bghiti nkemmel 3la had l'idée?

_(darija-check : 0 marker(s) au 1er essai aucun → **RETRY DÉCLENCHÉ** — 2e essai : 12 marker(s), retry corrigé ✅)_

### Sources utilisées pour cette réponse

- **[Source 1]** (score 0.268) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2026/2026-normale-corrige.txt` (extrait 0/26, ligne ~2)
  - extrait : MonBac.ma — Plateforme de préparation au Baccalauréat marocain  Corrigé — Mathématiques Sciences Mathématiques A & B Session Ordinaire — 2026 Coefficient : 9 | Durée : 4h | Barème : /20  Ce corrigé est proposé par MonBac …
- **[Source 2]** (score 0.253) Mathématiques | Chapitre 1 : Limites et continuité | Séance 1-1-1 : Limites et continuité - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-01-limites-et-continuite/seance-1-1-1-cours-partie1.txt` (extrait 0/5, ligne ~3)
  - extrait : Séance 1-1-1 : Limites et continuité - Partie 1 (Cours)  ## Sommaire  I- Limites d'une fonction en un point 1-1/ Rappels et compléments 1-2/ Unicité de la limite 1-3/ Limites des fonctions usuelles 1-4/ Opérations sur le …
- **[Source 3]** (score 0.203) Mathématiques | Chapitre 2 : Suites numériques | Séance 2-2-1 : Suites numériques - Partie 2 (Cours) | Cours
  - fichier : `mathematiques/chapitre-02-suites-numeriques/seance-2-2-1-cours-partie2.txt` (extrait 19/25, ligne ~192)
  - extrait : Proposition 9  Toute suite croissante non majorée tend vers $+ \infty$.  Toute suite décroissante non minorée tend vers $- \infty$.  ### IV- Critères de convergence  #### 4-1/ Existence de la limite par encadrement
- **[Source 4]** (score 0.203) Mathématiques | Chapitre 9 : Arithmétique dans Z | Séance 9-1-1 : Arithmétique dans Z - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-09-arithmetique-dans-z/seance-9-1-1-cours-partie1.txt` (extrait 1/38, ligne ~33)
  - extrait : ##### Définition 1  Soit $a$ et $b$ deux entiers relatifs non nulles.  Le plus grand commun diviseur de $a$ et $b$, noté $a \land b$ ou $P G C D \left(a , b\right)$, est le plus grand des diviseurs positifs communs à $a$ …
- **[Source 5]** (score 0.186) Mathématiques | Examens Nationaux | Examen National
  - fichier : `mathematiques/examens-nationaux/2010/2010-normale-sujet.txt` (extrait 0/7, ligne ~2)
  - extrait : الامتحان الوطني الموحد للبكالوريا - الدورة العادية 2010 – الموضوع - مادة : الرياضيات NS25 — المعامل : 9 — مدة الإنجاز : 4  - La durée de l'épreuve est de 4 heures. - L'épreuve comporte cinq exercices indépendants deux à …
- **[Source 6]** (score 0.222) Mathématiques | Chapitre 9 : Arithmétique dans Z | Séance 9-1-1 : Arithmétique dans Z - Partie 1 (Cours) | Cours
  - fichier : `mathematiques/chapitre-09-arithmetique-dans-z/seance-9-1-1-cours-partie1.txt` (extrait 11/38, ligne ~121)
  - extrait : #### 1-5/ Détermination des coefficients du théorème de bezout  L'inconvénient du théorème du Bezout, sous sa forme théorique, est qu'il ne fournit pas les coefficients $u$ et $v$ intervenant dans la relation $a u + b v …

---

