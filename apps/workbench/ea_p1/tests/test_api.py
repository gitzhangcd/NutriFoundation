"""FastAPI role-bound HTTP integration tests. Synthetic actors only."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from app import make_app
from core import digest
from seed_demo import populate


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.app = make_app(Path(self.temp.name) / "test.sqlite", allow_synthetic=True)
        populate(self.app.state.engine)
        self.client = TestClient(self.app)

    def headers(self, actor):
        return {"X-EA-Token": self.app.state.tokens[actor]}

    def test_health_and_no_gold(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["mode"], "SYNTHETIC_ENGINEERING_ONLY")
        self.assertEqual(r.json()["gold"], "NOT_QUALIFIED")
        self.assertEqual(r.headers["cache-control"], "no-store")
        self.assertEqual(self.client.get("/v1/ea/tasks").status_code, 401)

    def test_expert_profile_sources_candidates_and_export(self):
        hdr = self.headers("expert")
        tasks = self.client.get("/v1/ea/tasks", headers=hdr).json()["tasks"]
        self.assertEqual(len(tasks), 7)
        source = self.client.get("/v1/ea/tasks/EA-P1-SYN-01/sources", headers=hdr)
        self.assertEqual(source.status_code, 200)
        self.assertEqual(source.json()["source_count"], 2)
        bad = self.client.get("/v1/ea/tasks/EA-P1-SYN-01/sources/META-001/r1", headers=hdr)
        self.assertEqual(bad.status_code, 403)
        self.assertEqual(bad.json()["detail"], "DENY_SOURCE_NOT_ALLOWED")
        data = self.client.get("/v1/ea/tasks/EA-P1-SYN-01/sources/GUIDE-001/r1", headers=hdr)
        self.assertEqual(data.status_code, 200)
        self.assertEqual(data.json()["source_type"], "GUIDELINE")
        frozen = self.client.get("/v1/ea/tasks/EA-P1-SYN-01/candidates", headers=hdr)
        self.assertEqual(frozen.status_code, 200)
        c = frozen.json()
        request = {"items": [{"candidate_id": c["items"][0]["candidate_id"],
                              "disposition": "ACCEPT", "field_group": c["items"][0]["field_group"],
                              "source_support_status": "SUPPORTED",
                              "reason": "Synthetic acceptance only"}],
                   "candidate_set_digest": c["content_sha256"]}
        reviewed = self.client.post("/v1/ea/tasks/EA-P1-SYN-01/review/freeze",
                                   headers=hdr, json=request)
        self.assertEqual(reviewed.status_code, 200, reviewed.text)
        self.assertFalse(reviewed.json()["scientific_capture"])
        self.assertEqual(reviewed.json()["gold_qualification"], "NOT_ELIGIBLE")
        repeated = self.client.post("/v1/ea/tasks/EA-P1-SYN-01/review/freeze",
                                    headers=hdr, json=request)
        self.assertEqual(repeated.status_code, 409)
        exported = self.client.get("/v1/ea/tasks/EA-P1-SYN-01/export", headers=hdr)
        self.assertEqual(exported.json()["export_kind"], "UNQUALIFIED_EXPERT_REVIEW")
        self.assertFalse(exported.json()["promotion_authorized"])

    def test_blind_task_and_cross_actor(self):
        hdra, hdrb = self.headers("expert"), self.headers("expert_b")
        self.assertEqual(self.client.get("/v1/ea/tasks/EA-P1-SYN-INDEPENDENT/candidates",
                                         headers=hdrb).status_code, 403)
        self.assertEqual(self.client.get("/v1/ea/tasks/EA-P1-SYN-INDEPENDENT/workpack",
                                         headers=hdra).status_code, 403)
        p = self.client.post("/v1/ea/tasks/EA-P1-SYN-INDEPENDENT/review/freeze",
                            headers=hdrb,json={"items":[{"statement":"I cannot infer causality from this fictional example."}]})
        self.assertEqual(p.status_code, 200,p.text)
        self.assertIsNone(p.json()["candidate_set_digest"])

    def test_producer_endpoint_separated(self):
        h = self.headers("producer")
        self.assertEqual(self.client.post("/v1/ea/tasks/EA-P1-SYN-01/review/freeze",
                              headers=h,json={"items":[{"candidate_id":"X","disposition":"ACCEPT"}]}).status_code, 403)
        self.assertEqual(self.client.get("/v1/ea/audit",headers=h).status_code, 403)
        self.assertTrue(self.client.get("/v1/ea/audit",
                             headers=self.headers("auditor")).json()["chain_valid"])


if __name__ == "__main__":
    unittest.main()
