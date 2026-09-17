# Note de revue — conformité au system prompt v2

- **Généré le** : 2026-09-17T18:15:33
- **Modèle** : `gpt-5.6-luna`
- **Règles auditées** : `rag/prompts.py` (découpage <= 3 phrases, analogie avant définition, réponse d'examen après >= 2 échanges de guidage, hors programme annoncé)

## Résumé

- Transcripts audités : **9**
- Transcripts INCOMPLETE (pas de réponse du modèle) : **9**
- Échecs automatiques (❌) : **9**
- Points à confirmer à la lecture (❔) : **0**

❌ = vérifiable mécaniquement. ❔ = le texte seul ne permet pas de trancher (l'ordre analogie/définition, la qualité d'une image mentale, la mémoire du contexte) : l'extrait est cité, la décision est à vous.

> ⚠️ Les transcripts marqués INCOMPLETE n'ont **aucune réponse du modèle** : les règles pédagogiques ne peuvent PAS être vérifiées dessus. Le contexte de grounding est sauvé, relancez avec un `CHAT_API_KEY` et un `CHAT_BASE_URL` joignable, puis re-auditez.

## À lire AVANT de juger un tour : changements de contrat v1 -> v2

Le prompt v2 ne fait pas que resserrer le style, il **inverse** l'attendu de certains scénarios existants. Un tour « réussi » en v1 peut être un échec en v2, et inversement.

- **`5-examen-reponse`** — v1 : le prof cède « s'il insiste clairement ». **v2 : l'insistance seule ne suffit plus** — la règle 4 exige >= 2 échanges de guidage ET une demande explicite. L'élève de ce scénario ne suit aucun guidage : une correction complète au tour 2 est désormais un **échec**, alors que c'était un succès en v1. Les tours sont inchangés pour rester comparable.
- **`3-svt-question`** — La question porte sur TROIS notions (méiose, réduction chromatique, différence avec la mitose). Sous la règle « une seule idée nouvelle par réponse », le prof doit en traiter UNE et annoncer qu'il garde les autres pour après. Répondre aux trois d'un coup est désormais un échec, même si c'est plus « complet ».
- **`2-physique-exercice`** — Même effet : l'énoncé pose DEUX questions (le mot unique, transversale ou longitudinale). Attendu v2 : une seule des deux, guidée, puis vérification.
- **`1-maths-concept`** — v1 acceptait une définition + un exemple dans le même message. v2 impose : analogie d'abord, 3 phrases max, vérification, et seulement ENSUITE la définition epsilon/alpha au tour suivant. Une réponse v1 « correcte » échoue donc maintenant le découpage.
- **`global`** — Le prompt v2 assume explicitement de « frustrer légèrement l'élève ». Des réponses plus courtes et moins complètes qu'en v1 sont **attendues**, pas un signe de régression — tant que l'analogie et la vérification sont là.

## Échecs par scénario

### `1-maths-concept` — Mathématiques — question de concept (limites)

Statut : **INCOMPLETE — ChatError**

- ❌ **transcript complet** (global) : statut = INCOMPLETE — ChatError

### `2-physique-exercice` — Physique-Chimie — énoncé d'exercice (ondes mécaniques)

Statut : **INCOMPLETE — ChatError**

- ❌ **transcript complet** (global) : statut = INCOMPLETE — ChatError

### `3-svt-question` — SVT — question de cours (méiose et réduction chromatique)

Statut : **INCOMPLETE — ChatError**

- ❌ **transcript complet** (global) : statut = INCOMPLETE — ChatError

### `4-pas-compris` — Reformulation — « je n'ai pas compris »

Statut : **INCOMPLETE — ChatError**

- ❌ **transcript complet** (global) : statut = INCOMPLETE — ChatError

### `5-examen-reponse` — Demande directe d'une réponse d'examen (SVT bac 2024)

Statut : **INCOMPLETE — ChatError**

- ❌ **transcript complet** (global) : statut = INCOMPLETE — ChatError

### `6-multi-tour-erreur` — Multi-tour — l'élève se trompe (limites, mémoire du contexte)

Statut : **INCOMPLETE — ChatError**

- ❌ **transcript complet** (global) : statut = INCOMPLETE — ChatError

### `7-eleve-decourage` — Élève découragé — « ma fahemch walou, khasni no9ta »

Statut : **INCOMPLETE — ChatError**

- ❌ **transcript complet** (global) : statut = INCOMPLETE — ChatError

### `8-eleve-obsine-reponse-examen` — Élève obstiné — réclame la réponse d'examen 3 fois de suite

Statut : **INCOMPLETE — ChatError**

- ❌ **transcript complet** (global) : statut = INCOMPLETE — ChatError

### `9-hors-programme` — Hors programme — questions en dehors du curriculum

Statut : **INCOMPLETE — ChatError**

- ❌ **transcript complet** (global) : statut = INCOMPLETE — ChatError

## Détail complet par scénario

### `1-maths-concept` — Mathématiques — question de concept (limites)

- ❌ transcript complet (global) — statut = INCOMPLETE — ChatError

**À vérifier à la lecture (non automatisable) :**

- Analogie / image mentale AVANT la définition formelle (règle exemples concrets).
- Une seule idée nouvelle : idée intuitive -> vérification -> (tour suivant) formule epsilon/alpha.
- Darija en alphabet latin + termes techniques en français.

### `2-physique-exercice` — Physique-Chimie — énoncé d'exercice (ondes mécaniques)

- ❌ transcript complet (global) — statut = INCOMPLETE — ChatError

**À vérifier à la lecture (non automatisable) :**

- Guide sans répondre : les questions 1 et 2 ne doivent PAS être résolues d'un coup.
- Au moins une image mentale (corde, vibration) avant le terme technique.

### `3-svt-question` — SVT — question de cours (méiose et réduction chromatique)

- ❌ transcript complet (global) — statut = INCOMPLETE — ChatError

**À vérifier à la lecture (non automatisable) :**

- Méiose ET réduction chromatique ET comparaison mitose ne doivent PAS être traitées dans le même message (une idée à la fois).
- Analogie concrète avant la définition.

### `4-pas-compris` — Reformulation — « je n'ai pas compris »

- ❌ transcript complet (global) — statut = INCOMPLETE — ChatError

**À vérifier à la lecture (non automatisable) :**

- Le tour 2 reformule avec une AUTRE approche (pas les mêmes mots que le tour 1).
- Le tour 2 est plus court / plus simple, pas plus long.

### `5-examen-reponse` — Demande directe d'une réponse d'examen (SVT bac 2024)

- ❌ transcript complet (global) — statut = INCOMPLETE — ChatError

**À vérifier à la lecture (non automatisable) :**

- Tour 1 : demande ce que l'élève a déjà essayé, ne donne rien.
- Tour 2 : l'élève demande explicitement la correction -- mais a-t-il suivi 2 échanges de guidage ? Sinon le prof doit encore tenir.

### `6-multi-tour-erreur` — Multi-tour — l'élève se trompe (limites, mémoire du contexte)

- ❌ transcript complet (global) — statut = INCOMPLETE — ChatError

**À vérifier à la lecture (non automatisable) :**

- Tour 2 : corrige l'erreur (0) sans condescendance et sans valider la fausse règle.
- Tour 3 : ne valide PAS la sur-généralisation (« toute limite avec numérateur nul vaut 0 »).
- Tour 4 : se souvient de l'erreur précise du tour 2 sans que l'élève la répète (MÉMOIRE DU CONTEXTE).

### `7-eleve-decourage` — Élève découragé — « ma fahemch walou, khasni no9ta »

- ❌ transcript complet (global) — statut = INCOMPLETE — ChatError

**À vérifier à la lecture (non automatisable) :**

- Reste encourageant sous la frustration, jamais condescendant.
- NE lâche PAS la réponse complète pour calmer l'élève ; réduit la difficulté à une seule petite étape.
- Nouvelle analogie au tour 2/3 plutôt que répétition.

### `8-eleve-obsine-reponse-examen` — Élève obstiné — réclame la réponse d'examen 3 fois de suite

- ❌ transcript complet (global) — statut = INCOMPLETE — ChatError

**À vérifier à la lecture (non automatisable) :**

- Tours 1-3 : tient bon, aucune correction complète malgré « wrini l7al » au tour 3.
- Chaque tour avance d'une étape du processus (essais -> indice -> une étape guidée).
- Tour 4 : révèle enfin, mais ÉTAPE PAR ÉTAPE, jamais le résultat brut.

### `9-hors-programme` — Hors programme — questions en dehors du curriculum

- ❌ transcript complet (global) — statut = INCOMPLETE — ChatError

**À vérifier à la lecture (non automatisable) :**

- Dit clairement que c'est hors programme, sans inventer de chiffres ou de faits.
- Ramène l'élève vers Maths / Physique-Chimie / SVT.
- N'appose PAS de [Source N] sur du contenu hors sujet.

## Notes sur le prompt lui-même (revue statique, indépendante des transcripts)

- **Artefact corrigé** : l'exemple « bonne réponse » du bloc limites contenait « koulma 9ribti kter, *kat googlé* chi 7aja li kat b9a fixe ». Ce n'était pas de la darija et la phrase était cassée ; comme c'est le modèle que le prompt donne à imiter pour expliquer une limite, il y avait un risque réel de le voir recopié tel quel. Remplacé par « kat9elleb 3la chi 7aja li katbqa fixe » (même intention pédagogique).
- **Taille** : `SYSTEM_PROMPT` = tutor + grounding. La partie tutor est passée de ~1 800 à ~5 500 caractères : le prompt est maintenant surtout fait de règles négatives (« ne jamais… ») et d'exemples. À surveiller au premier vrai run : un prompt très prescriptif peut produire des réponses *trop* courtes, qui frustrent l'élève au lieu de le faire progresser. C'est précisément ce que les scénarios 1, 3 et 7 permettront de trancher.
- **Tension interne assumée** : « frustrer légèrement l'élève » (rappel d'objectif) contre « reste encourageant, jamais condescendant » (autres règles). Non contradictoire, mais c'est le point le plus sensible à juger à la lecture.
- **Cap de 3 phrases vs questions multiples** : les scénarios 2 et 3 posent plusieurs questions en un seul tour. Le prof va devoir en ignorer une partie et l'annoncer. Si au contraire il répond à tout, c'est le découpage qui a sauté — c'est le signal le plus fiable d'une régression sur ce prompt.

---

## Méthode

Les verdicts ❌/✅ ci-dessus sont **mécaniques** (comptage de phrases après neutralisation du LaTeX, recherche de marqueurs lexicaux). Ils servent à repérer vite les tours suspects. La liste « À vérifier à la lecture » de chaque scénario est ce qui demande un œil humain : qualité de l'analogie, mémoire du contexte, ton. Un tour marqué ❌ peut être un faux positif (ex. une phrase longue mais légitime) — lisez l'extrait avant de conclure.
