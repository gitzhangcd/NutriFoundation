"""Mechanism tests that do not require the vault PDFs."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import fitz

from tools.ndf_d1_a2_pilot.build_run import CUTOFF, _redact
from tools.ndf_d1_a2_pilot.span_replay import locate, replay_pdf
from tools.source_archive_verifier import ndf_d1_twelve_source_recovery as recovery


class PilotMechanismTests(unittest.TestCase):
    def test_span_replays_on_synthetic_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.pdf"
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "HOMA-IR change was -1.08 in the trial arm.")
            document.save(path)
            document.close()
            from tools.ndf_d1_a2_pilot.span_replay import page_text
            raw = page_text(path, 1)
            found = locate(raw, "HOMA-IR change was -1.08")
            self.assertTrue(found["ok"])
            self.assertTrue(replay_pdf(path, 1, found["start"], found["end"], found["literal_text"])["ok"])

    def test_cookie_redaction_keeps_other_headers(self):
        redacted = _redact({"set-cookie": "session=secret", "content-type": "application/pdf"})
        self.assertEqual(redacted["set-cookie"], "[REDACTED]")
        self.assertEqual(redacted["content-type"], "application/pdf")

    def test_oa_route_wording_is_distinct_from_every_lawful_channel(self):
        source = Path(recovery.__file__).read_text(encoding="utf-8")
        self.assertIn("NO_QUALIFYING_OA_ROUTE_FOUND_THIS_RUN", source)
        self.assertIn("not a finding that every lawful channel", source)

    def test_cutoff_is_not_a_retrieval_timestamp(self):
        self.assertEqual(CUTOFF, "2026-10-07")
        retrieval = "2026-10-10T10:20:02+00:00"
        publication = "2022-02-22"
        self.assertGreater(retrieval[:10], CUTOFF)
        self.assertLess(publication, CUTOFF)
        self.assertNotEqual(retrieval[:10], publication)

    def test_quarantine_registry_exists_for_offline_package(self):
        path = Path("tools/source_archive_verifier/fixtures/quarantine_registry_r1_3.json")
        self.assertTrue(path.is_file())

    def test_pilot_questions_are_not_one_synthesis(self):
        questions = {"Q-PILOT-004-001", "Q-PILOT-033-001"}
        self.assertEqual(len(questions), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
