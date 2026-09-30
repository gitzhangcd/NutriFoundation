from pathlib import Path

from nutrifoundation.persistence.sqlite import SQLiteStore
from nutrifoundation.services.evidence_replay import replay_batch001_evidence


ROOT = Path(__file__).resolve().parents[1]


def test_batch001_evidence_replay_freezes_all_20(tmp_path):
    store = SQLiteStore(tmp_path / "replay.db")
    report = replay_batch001_evidence(
        ROOT / "fixtures/Batch001_Verified_SourceArtifact_Registry_v0.1.yaml",
        ROOT / "fixtures/pubmed_batch001_articles.json",
        ROOT / "fixtures/Batch001_EvidenceUnit_Frozen_v0.1.yaml",
        store,
    )

    print(report.as_dict())
    assert report.status == "PASS", report.as_dict()
    assert report.expected_count == 20
    assert report.stored_f0_count == 20
    assert report.payload_match_count == 20
    assert report.mismatch_count == 0

    stored = store.list_f0_evidence()
    assert len(stored) == 20
    assert all(x.status == "frozen_F0" for x in stored)
