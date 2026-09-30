from datetime import date
from pathlib import Path

import yaml

from nutrifoundation.connectors.ncbi import PubMedArticle
from nutrifoundation.domain.enums import SourceType
from nutrifoundation.services.ingestion import classify_source_type


def test_corrected_trial_classifies_as_rct_when_abstract_preserves_design():
    article = PubMedArticle(
        "1",
        "Primary prevention corrected publication",
        "J",
        date(2020, 1, 1),
        (),
        None,
        None,
        ("Corrected and Republished Article",),
        "Participants were randomly assigned.",
    )
    assert classify_source_type(article) == SourceType.RCT


def test_consensus_title_classifies_as_consensus():
    article = PubMedArticle(
        "1",
        "Nutrition Therapy: A Consensus Report",
        "J",
        date(2020, 1, 1),
        (),
        None,
        None,
        ("Review",),
    )
    assert classify_source_type(article) == SourceType.CONSENSUS


def test_batch001_gold_gate_still_zero():
    path = (
        Path(__file__).resolve().parents[1]
        / "fixtures/Batch001_ScientificClaim_Gold_Registry_v0.1.yaml"
    )
    data = yaml.safe_load(path.read_text())
    assert data["frozen_gold_count"] == 0
    assert len(data["ready_candidates"]) == 3
