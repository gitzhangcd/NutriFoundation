from pathlib import Path

import yaml


def test_batch001_gold_registry_is_still_human_gated():
    root = Path(__file__).resolve().parents[1]
    path = root / "fixtures" / "Batch001_ScientificClaim_Gold_Registry_v0.1.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert data["frozen_gold_count"] == 0
    assert data["gold_claims"] == []
    assert len(data["ready_candidates"]) == 3
    assert all(
        x["human_adjudication"] == "pending"
        for x in data["ready_candidates"]
    )
