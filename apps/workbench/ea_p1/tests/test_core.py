"""Runtime tests: no external network, synthetic data only. Python stdlib unittest."""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from core import EAError, EvidenceEngine, digest, utf16_slice
from seed_demo import populate, anchor, CONTRACT


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.engine = EvidenceEngine(Path(self.tmp.name) / "store.sqlite", CONTRACT)
        self.p = {"actor": "SYN-PRODUCER-1", "role": "producer"}
        self.e = {"actor": "SYN-EXPERT-A", "role": "expert"}
        self.b = {"actor": "SYN-EXPERT-B", "role": "expert"}
        self.a = {"actor": "SYN-AUDITOR", "role": "auditor"}
        self.seed = populate(self.engine)
        self.rct = self.engine.read_source(**self.e, task_id="EA-P1-SYN-01",
                                           source_id="RCT-001", revision_id="r1")
        self.guide = self.engine.read_source(**self.e, task_id="EA-P1-SYN-01",
                                             source_id="GUIDE-001", revision_id="r1")

    def fail_code(self, code, f, *args, **kwargs):
        with self.assertRaises(EAError) as caught:
            f(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)

    def test_all_seven_profiles_frozen_candidates(self):
        self.assertEqual(self.seed["sources"], 7)
        for task_id in self.seed["agent_verify_tasks"]:
            pack = self.engine.workpack(**self.e, task_id=task_id)
            self.assertEqual(pack["state"], "CANDIDATE_FROZEN")
            self.assertEqual(pack["candidate_status"], "AVAILABLE")
            data = self.engine.read_candidates(**self.e, task_id=task_id)
            self.assertEqual(len(data["items"]), 1)
            self.assertFalse(data["scientific_capture"])

    def test_two_source_registry_and_cross_task_deny(self):
        d = self.engine.list_sources(**self.e, task_id="EA-P1-SYN-01")
        self.assertEqual(d["source_count"], 2)
        self.assertEqual({x["source_id"] for x in d["sources"]}, {"RCT-001", "GUIDE-001"})
        self.fail_code("DENY_SOURCE_NOT_ALLOWED", self.engine.read_source, **self.e,
                       task_id="EA-P1-SYN-01", source_id="META-001", revision_id="r1")
        self.fail_code("TASK_NOT_ASSIGNED", self.engine.read_source, **self.b,
                       task_id="EA-P1-SYN-01", source_id="RCT-001", revision_id="r1")

    def test_agent_candidate_review_roundtrip_and_immutable(self):
        set_ = self.engine.read_candidates(**self.e, task_id="EA-P1-SYN-01")
        cand = set_["items"][0]
        review = self.engine.freeze_review(**self.e, task_id="EA-P1-SYN-01",
            candidate_set_digest=set_["content_sha256"],
            items=[{"candidate_id": cand["candidate_id"], "disposition": "MODIFY",
                    "field_group": cand["field_group"], "source_support_status": "PARTIAL",
                    "reason": "Clarify that all content is fabricated",
                    "corrected_candidate_payload": {"training_note": "This is invented."}}])
        self.assertTrue(review["immutable"])
        self.assertEqual(review["candidate_set_digest"], set_["content_sha256"])
        exported = self.engine.export_record(**self.e, task_id="EA-P1-SYN-01")
        self.assertFalse(exported["promotion_authorized"])
        self.assertEqual(exported["gold_qualification"], "NOT_ELIGIBLE")
        self.assertEqual(exported["state"], "EXPERT_REVIEW_FROZEN")
        self.fail_code("REVIEW_ALREADY_FROZEN", self.engine.freeze_review, **self.e,
                       task_id="EA-P1-SYN-01", items=[{"candidate_id": cand["candidate_id"],
                           "disposition": "ACCEPT"}], candidate_set_digest=set_["content_sha256"])
        with self.engine.connect() as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("UPDATE reviews SET record='forged' WHERE task_id='EA-P1-SYN-01'")
        self.assertTrue(self.engine.audit(**self.a)["chain_valid"])

    def test_cannot_use_candidate_missing_quote(self):
        candidate = self.engine.read_candidates(**self.e, task_id="EA-P1-SYN-01")["items"][0]
        self.fail_code("CANDIDATES_ALREADY_FROZEN", self.engine.freeze_candidates, **self.p,
                       task_id="EA-P1-SYN-01", items=[candidate])
        bad = dict(candidate, original_anchors=[])
        task = self._new_rct_task("FRESH-01")
        self.fail_code("BLOCK_UNVERIFIED_CANDIDATE", self.engine.freeze_candidates, **self.p,
                       task_id=task, items=[bad])

    def _new_rct_task(self, task_id):
        src = self.rct
        self.engine.create_task(**self.p, task={
            "task_id": task_id, "task_kind": "EVIDENCE_ECOSYSTEM_CASE",
            "profile_id": "WB_EA_RCT_V0_1",
            "primary_source": {"source_id": src["source_id"], "revision_id": src["revision_id"]},
            "allowed_source_versions": [{"source_id": src["source_id"],
                 "revision_id": src["revision_id"],
                 "canonical_document_sha256": src["canonical_document_sha256"]}],
            "knowledge_cutoff": "2026-10-09T00:00:00+00:00",
            "workflow_strategy": "AGENT_PROPOSE_EXPERT_VERIFY",
            "expert_actor": "SYN-EXPERT-A",
        })
        return task_id

    def test_anchor_offset_and_tampering(self):
        self.assertEqual(utf16_slice("😀diet", 2, 6), "diet")
        self.fail_code("INVALID_UTF16_BOUNDARY", utf16_slice, "😀diet", 0, 1)
        task = self._new_rct_task("FRESH-02")
        item = dict(self.engine.read_candidates(**self.e, task_id="EA-P1-SYN-01")["items"][0])
        wrong = dict(item["original_anchors"][0], source_quote="altered")
        item["original_anchors"] = [wrong]
        self.fail_code("SOURCE_SPAN_MISMATCH", self.engine.freeze_candidates, **self.p,
                       task_id=task, items=[item])
        correct = dict(wrong, source_quote=wrong["source_quote_sha256"])
        item["original_anchors"] = [correct]
        self.fail_code("SOURCE_SPAN_MISMATCH", self.engine.freeze_candidates, **self.p,
                       task_id=task, items=[item])

    def test_no_clinical_or_gold_promotion(self):
        self.fail_code("DECISION_CASE_DELEGATE_EXISTING_NDS_ONLY", self.engine.create_task, **self.p,
                       task={"task_id": "DEC", "task_kind": "DECISION_CASE",
                             "profile_id": "NDS_R1_DECISION_CAPTURE",
                             "primary_source": {"source_id": "RCT-001", "revision_id": "r1"},
                             "allowed_source_versions": [], "knowledge_cutoff": "2026-10-09T00:00:00+00:00",
                             "workflow_strategy": "NDS_R1_EXISTING", "expert_actor": "SYN-EXPERT-A"})
        self.assertEqual(self.engine.contract["task_kinds"]["DECISION_CASE"]["field_count"], 19)

    def test_independent_blind_and_freeze(self):
        task = "EA-P1-SYN-INDEPENDENT"
        self.fail_code("DENY_INDEPENDENT_AGENT_EXPOSURE", self.engine.read_candidates,
                       **self.b, task_id=task)
        self.fail_code("INDEPENDENT_MODE_NO_AGENT", self.engine.freeze_candidates,
                       **self.p, task_id=task, items=[{"candidate_id": "fake"}])
        result = self.engine.freeze_review(**self.b, task_id=task,
                                           items=[{"statement": "Observed association remains not causal."}])
        self.assertIsNone(result["candidate_set_digest"])
        self.fail_code("REVIEW_ALREADY_FROZEN", self.engine.freeze_review, **self.b,
                       task_id=task, items=[{"statement": "Changed mind"}])
        self.fail_code("TASK_NOT_ASSIGNED", self.engine.export_record, **self.e, task_id=task)

    def test_bad_review_rejected(self):
        task = "EA-P1-SYN-02"
        set_ = self.engine.read_candidates(**self.e, task_id=task)
        item = set_["items"][0]
        self.fail_code("CANDIDATE_DIGEST_MISMATCH", self.engine.freeze_review,
                       **self.e, task_id=task,
                       items=[{"candidate_id": item["candidate_id"], "disposition": "ACCEPT"}],
                       candidate_set_digest="invalid")
        self.fail_code("REVIEW_REASON_REQUIRED", self.engine.freeze_review,
                       **self.e, task_id=task,
                       items=[{"candidate_id": item["candidate_id"], "disposition": "REJECT",
                               "field_group": item["field_group"], "source_support_status": "UNSUPPORTED"}],
                       candidate_set_digest=set_["content_sha256"])
        self.fail_code("REVIEW_ITEMS_EMPTY", self.engine.freeze_review,
                       **self.e, task_id=task, items=[],
                       candidate_set_digest=set_["content_sha256"])

    def test_reject_revision_conflict(self):
        src = dict(self.rct)
        src["units"] = [{"unit_id": "u1", "text": "malicious replacement"}]
        self.fail_code("IMMUTABLE_SOURCE_VERSION_CONFLICT", self.engine.register_source,
                       **self.p, source=src)
        with self.engine.connect() as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("DELETE FROM sources WHERE source_id='RCT-001'")

    def test_source_time_and_bad_type(self):
        source = {"source_id": "TEMP", "revision_id": "r1", "source_type": "GUIDELINE",
                  "title": "[SYNTHETIC] future", "available_at": "2027-01-01T00:00:00Z",
                  "fetched_at": "2027-01-02T00:00:00Z", "rights_status": "SYNTHETIC_FIXTURE",
                  "units": [{"unit_id": "1", "text": "Future source"}]}
        created = self.engine.register_source(**self.p, source=source)
        self.assertFalse(created["scientific_capture"])
        self.fail_code("FUTURE_SOURCE_AT_CUTOFF", self.engine.create_task, **self.p,
                       task={"task_id": "BAD-TIME", "task_kind": "EVIDENCE_ECOSYSTEM_CASE",
                         "profile_id": "WB_EA_GUIDELINE_V0_1",
                         "primary_source": {"source_id": "TEMP", "revision_id": "r1"},
                         "allowed_source_versions": [{"source_id": "TEMP", "revision_id": "r1",
                             "canonical_document_sha256": created["canonical_document_sha256"]}],
                         "knowledge_cutoff": "2026-10-09T00:00:00Z",
                         "workflow_strategy": "AGENT_PROPOSE_EXPERT_VERIFY",
                         "expert_actor": "SYN-EXPERT-A"})
        source["source_type"] = "UNDEFINED"
        source["source_id"] = "BAD"
        self.fail_code("TYPE_UNRESOLVED_HOLD", self.engine.register_source,
                       **self.p, source=source)

    def test_non_actor_denied_and_historical_immutable(self):
        self.fail_code("ROLE_FORBIDDEN", self.engine.register_source, **self.e, source=self.rct)
        self.fail_code("ROLE_FORBIDDEN", self.engine.audit, **self.p)
        self.fail_code("ROLE_FORBIDDEN", self.engine.freeze_review, **self.p,
                       task_id="EA-P1-SYN-01", items=[{"disposition": "ACCEPT"}])
        self.assertTrue(self.engine.audit(**self.a)["chain_valid"])


if __name__ == "__main__":
    unittest.main()
