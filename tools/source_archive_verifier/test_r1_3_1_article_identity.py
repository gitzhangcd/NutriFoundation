#!/usr/bin/env python3
"""Independent adversarial tests for R1.3 article-identity region assumptions.

Run from NutriFoundation repository root:
  python -m unittest -v path/to/R1_3_Independent_Adversarial_Tests.py
Or directly:
  python path/to/R1_3_Independent_Adversarial_Tests.py
Expected against R1.3 dd936ac7: three FAIL results (false CONFIRMED).
Only synthetic PDFs are created. No real source documents are modified.
"""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
import fitz
from tools.source_archive_verifier.identity_evaluator import evaluate_pdf_identity_canonical

TARGET_TITLE = "Dietary Patterns and Risk of Cardiovascular Disease in Older Adults"
TARGET_DOI = "10.1234/target-study.2025.007"

class ArticleIdentityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp.cleanup()

    def make_pdf(self, pages):
        path = Path(self.temp.name) / "synthetic.pdf"
        doc = fitz.open()
        for body in pages:
            page = doc.new_page()
            y = 65
            for line in body.split("\n"):
                page.insert_text((40, y), line, fontsize=9)
                y += 17
        doc.save(path)
        doc.close()
        return path

    def evaluate(self, pages):
        return evaluate_pdf_identity_canonical(
            self.make_pdf(pages), TARGET_TITLE, TARGET_DOI, "41234567"
        )

    def test_toc_listing_is_not_article_identity(self):
        res = self.evaluate([
            "Journal of Clinical Nutrition\nVolume 37 Issue 5\nTable of Contents\n"
            f"Article 1: {TARGET_TITLE}\ndoi: {TARGET_DOI}\n"
            "Article 2: Microbiome diversity in pregnancy"
        ])
        self.assertNotEqual(res["identity_verdict"], "CONFIRMED", res)

    def test_editorial_citation_is_not_article_identity(self):
        res = self.evaluate([
            "Editorial: Current directions in nutrition research\n"
            "In this issue we discuss the following paper:\n"
            f"{TARGET_TITLE}\ndoi: {TARGET_DOI}\n"
            "This editorial discusses several studies, it is not the target paper."
        ])
        self.assertNotEqual(res["identity_verdict"], "CONFIRMED", res)

    def test_title_and_doi_on_different_pages_are_not_same_identity_block(self):
        res = self.evaluate([
            f"Journal contents\n{TARGET_TITLE}",
            f"Unrelated appendix\ndoi: {TARGET_DOI}"
        ])
        self.assertNotEqual(res["identity_verdict"], "CONFIRMED", res)

    def test_same_page_identity_block_keeps_separate_anchors(self):
        res = self.evaluate([
            "Original Investigation\n"
            f"{TARGET_TITLE}\n"
            f"doi: {TARGET_DOI}\n"
            "Abstract: Adults were enrolled.\n"
        ])
        self.assertEqual(res["identity_verdict"], "CONFIRMED")
        self.assertEqual(res["article_identity_block_page"], 1)
        self.assertTrue(res["article_identity_block_id"])
        self.assertNotEqual(res["title_anchor"]["literal_text"], res["doi_anchor"]["literal_text"])
        self.assertIn(TARGET_DOI, res["doi_anchor"]["literal_text"])
        from tools.source_archive_verifier.identity_evaluator import replay_proof_anchor
        pdf = Path(self.temp.name) / "synthetic.pdf"
        self.assertTrue(replay_proof_anchor(pdf, res["title_anchor"])["ok"])
        self.assertTrue(replay_proof_anchor(pdf, res["doi_anchor"])["ok"])

if __name__ == "__main__":
    unittest.main(verbosity=2)
