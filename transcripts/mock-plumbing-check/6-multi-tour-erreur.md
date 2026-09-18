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
