#!/usr/bin/env python3
"""Unit tests for the spoken-darija / anti-document response guard in chat.py.

No live model is called. The reconstructed failing example is the one the
keyword-count check used to let through (2 darija words, 90% French document).
"""
from __future__ import annotations

import unittest

from rag.llm import ChatResponse
from chat import (
    DARIJA_RETRY_REMINDER,
    RESPONSE_RETRY_REMINDER,
    TutorSession,
    assess_response,
    darija_min_markers,
    find_darija_markers,
    retry_reminder_for,
)


# Reconstructed from the observed failure: a French textbook dump with darija
# only as a last-line translation. Contains two darija markers (daba, 3la) so
# the OLD keyword-count check would have accepted it.
FAILING_FRENCH_THEN_DARIJA = """\
### Primitive et intégrale

Une fonction **F** est une primitive de $f$ si $F'(x) = f(x)$.

L'intégrale indéfinie s'écrit :

$$\\int f(x)\\,dx = F(x) + C$$

### Exemple travaillé

Calculons $\\int 2x\\,dx$.

1. On cherche une primitive $F$ telle que $F'(x) = 2x$.
2. On trouve $F(x) = x^2$.
3. Donc $\\int 2x\\,dx = x^2 + C$.

En darija : daba l'intégrale katqelleb 3la fonction li dérivée dyalha hiya f(x).
"""

GOOD_SPOKEN = (
    "Tsawwar l'intégrale bhal l'inverse dial la dérivée : ila l dérivée "
    "katmesser la vitesse, l'intégrale katmesser la distance parcourue. "
    "Daba, l'idée hia bassita — bghina n l9awou wach kayn fonction F li "
    "dérivée dyalha rajel l fonction f. Wach fhemti had l'idée 9bel ma nzid?"
)

GOOD_SPOKEN_2 = (
    "Daba khalini nchra7lek ghir l'idée l'lola, bla calcul. L'intégrale, "
    "hia bhal tjm3 l'massafa mlli nta katmchi, 7it la dérivée kat3tik ghir "
    "la vitesse f wahd l'lehda. Wach mchat m3ak had l'image, ola bghiti nzid nfesser?"
)

GOOD_SPOKEN_3 = (
    "Safi khouya, 9bel les formules, tsawwar m3aya: ila kat9elleb 3la fonction "
    "li kat3tik l'aire t7t l courbe, hadchi howa l'intégrale. Ma ghadi n3tikch "
    "la formule daba, ghi had l'idée. Wach fhemti 3lach kanbda b l'image 9bel "
    "l'écriture mathématique?"
)


class DummyRetriever:
    def retrieve(self, *args, **kwargs):
        return []


class ScriptedClient:
    """First complete() returns *failing*; later ones pop from *goods*."""

    def __init__(self, failing: str, goods: list[str], model: str = "scripted"):
        self.failing = failing
        self.goods = list(goods)
        self.model = model
        self.calls: list[list[dict]] = []

    def complete(self, messages):
        self.calls.append(list(messages))
        last = messages[-1]["content"] if messages else ""
        if "parle directement en mélange darija-français dès la première phrase" in last:
            return ChatResponse(content=self.goods.pop(0), model=self.model)
        if "trop formelle et 100% française" in last:
            return ChatResponse(content=self.goods.pop(0), model=self.model)
        return ChatResponse(content=self.failing, model=self.model)


class AssessResponseTests(unittest.TestCase):
    def test_failing_example_has_enough_markers_for_old_check(self):
        markers = find_darija_markers(FAILING_FRENCH_THEN_DARIJA)
        self.assertGreaterEqual(
            len(markers), darija_min_markers(),
            f"fixture must still pass the old keyword-count check, got {markers}",
        )

    def test_failing_example_is_now_rejected(self):
        verdict = assess_response(FAILING_FRENCH_THEN_DARIJA)
        self.assertTrue(verdict["should_retry"], verdict)
        for needed in (
            "markdown_formatting",
            "too_many_latex_blocks",
            "too_many_sentences",
            "darija_only_at_end",
            "darija_as_footnote",
        ):
            self.assertIn(needed, verdict["issues"], verdict)

    def test_failing_example_uses_document_retry_reminder(self):
        verdict = assess_response(FAILING_FRENCH_THEN_DARIJA)
        self.assertEqual(retry_reminder_for(verdict["issues"]), RESPONSE_RETRY_REMINDER)

    def test_good_spoken_replies_pass(self):
        for text in (GOOD_SPOKEN, GOOD_SPOKEN_2, GOOD_SPOKEN_3):
            with self.subTest(text=text[:40]):
                verdict = assess_response(text)
                self.assertFalse(verdict["should_retry"], verdict)
                self.assertGreaterEqual(len(verdict["markers"]), darija_min_markers())
                self.assertLessEqual(verdict["n_sentences"], 5)
                self.assertLessEqual(verdict["n_latex"], 2)

    def test_markdown_header_alone_retries(self):
        text = "Daba wach fhemti.\n### Les limites\nTsawwar m3aya had l'idée."
        self.assertIn("markdown_formatting", assess_response(text)["issues"])

    def test_bold_alone_retries(self):
        text = "Daba wach fhemti. La **dérivée** hia l'idée."
        self.assertIn("markdown_formatting", assess_response(text)["issues"])

    def test_list_structure_retries(self):
        text = "Daba wach fhemti.\n1. première idée\n2. deuxième idée"
        self.assertIn("markdown_formatting", assess_response(text)["issues"])

    def test_too_many_latex_retries(self):
        text = "Daba wach fhemti $a$ puis $b$ puis $c$."
        self.assertIn("too_many_latex_blocks", assess_response(text)["issues"])

    def test_too_many_sentences_retries(self):
        text = "Daba un. Wach deux. Tsawwar trois. Kayn quatre. Mzyan cinq. Bzzaf six."
        verdict = assess_response(text)
        self.assertIn("too_many_sentences", verdict["issues"], verdict)

    def test_pure_french_still_retries_on_markers(self):
        text = "Une primitive de f est une fonction F telle que F'(x)=f(x)."
        verdict = assess_response(text)
        self.assertIn("too_few_darija_markers", verdict["issues"])
        self.assertEqual(retry_reminder_for(verdict["issues"]), DARIJA_RETRY_REMINDER)


class TutorSessionRetryTests(unittest.TestCase):
    def test_failing_first_draft_is_retried_and_replaced(self):
        client = ScriptedClient(FAILING_FRENCH_THEN_DARIJA, [GOOD_SPOKEN])
        session = TutorSession(retriever=DummyRetriever(), client=client, verbose=False)
        result = session.ask("chra7 liya les integrales")
        self.assertEqual(result["answer"], GOOD_SPOKEN)
        check = result["darija_check"]
        self.assertTrue(check["retried"])
        self.assertEqual(check["outcome"], "retry_passed")
        self.assertIn("darija_as_footnote", check["first_issues"])
        self.assertEqual(check["reminder"], RESPONSE_RETRY_REMINDER)
        self.assertEqual(len(client.calls), 2)
        self.assertIn(RESPONSE_RETRY_REMINDER, client.calls[1][-1]["content"])


if __name__ == "__main__":
    unittest.main()
