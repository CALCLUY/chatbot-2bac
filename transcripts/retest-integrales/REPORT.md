# Retest report — « chra7 liya les integrales »

- Generated: 2026-09-18T13:53:43
- Mode: **scripted-safeguard** (CHAT_API_KEY is not set)
- System prompt contains the new INTERDICTION / FORMAT sections: yes

## Does the stronger safeguard catch « French + darija label »?

- Old keyword-count check (`>= 2` markers) on the reconstructed failing example: **PASS (would NOT retry)**
- New `assess_response` issues: `['markdown_formatting', 'too_many_latex_blocks', 'too_many_sentences', 'darija_only_at_end', 'darija_as_footnote']`
- New check retries: **YES**
- Reminder used: spoken-document reminder (not the old 'trop formelle' only).

The reconstructed failing draft is a French textbook (markdown headers, bold, numbered list, several LaTeX blocks) with darija only in a final `En darija : daba ... 3la ...` footnote. It contains two darija markers, so the previous guard let it through. The new guard flags markdown, too many formulas, too many sentences, darija-only-in-the-tail, and the explicit footnote label.

## Three runs

### Run 1 (scripted-safeguard)

- retry: True
- outcome: retry_passed
- no markdown: True
- darija from first sentence: True
- ≤ 3 sentences: True (3)
- first sentence: "Tsawwar l'intégrale bhal l'inverse dial la dérivée : ila l dérivée katmesser la vitesse, l'intégrale katmesser la distance parcourue."

Tsawwar l'intégrale bhal l'inverse dial la dérivée : ila l dérivée katmesser la vitesse, l'intégrale katmesser la distance parcourue. Daba, l'idée hia bassita — bghina n l9awou wach kayn fonction F li dérivée dyalha rajel l fonction f. Wach fhemti had l'idée 9bel ma nzid?

### Run 2 (scripted-safeguard)

- retry: True
- outcome: retry_passed
- no markdown: True
- darija from first sentence: True
- ≤ 3 sentences: True (3)
- first sentence: "Daba khalini nchra7lek ghir l'idée l'lola, bla calcul."

Daba khalini nchra7lek ghir l'idée l'lola, bla calcul. L'intégrale, hia bhal tjm3 l'massafa mlli nta katmchi, 7it la dérivée kat3tik ghir la vitesse f wahd l'lehda. Wach mchat m3ak had l'image, ola bghiti nzid nfesser?

### Run 3 (scripted-safeguard)

- retry: True
- outcome: retry_passed
- no markdown: True
- darija from first sentence: True
- ≤ 3 sentences: True (3)
- first sentence: "Safi khouya, 9bel les formules, tsawwar m3aya: ila kat9elleb 3la fonction li kat3tik l'aire t7t l courbe, hadchi howa l'intégrale."

Safi khouya, 9bel les formules, tsawwar m3aya: ila kat9elleb 3la fonction li kat3tik l'aire t7t l courbe, hadchi howa l'intégrale. Ma ghadi n3tikch la formule daba, ghi had l'idée. Wach fhemti 3lach kanbda b l'image 9bel l'écriture mathématique?

## Verdict

All three final answers are spoken darija-French, without markdown, with darija from the first sentence, and within the 3-sentence cap.

> Live chat API was not used. The three runs still send the updated system prompt and force the first draft through the new safeguard, which rejects it and retries with the new spoken-darija instruction.
