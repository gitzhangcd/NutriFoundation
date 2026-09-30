from pathlib import Path

from nutrifoundation.connectors.fixture import FixturePubMedConnector
from nutrifoundation.persistence.sqlite import SQLiteStore
from nutrifoundation.services.ingestion import SourceArtifactIngestionService
from nutrifoundation.services.replay import replay_batch001


ROOT = Path(__file__).resolve().parents[1]


def test_single_ingestion(tmp_path):
    connector = FixturePubMedConnector(
        ROOT / "fixtures/pubmed_batch001_articles.json"
    )
    store = SQLiteStore(tmp_path / "x.db")

    manifest = SourceArtifactIngestionService(
        connector,
        store,
        mode="test",
    ).ingest(
        [("SA-B001-001", "19721018")]
    )

    assert manifest.status == "completed"
    assert manifest.outputs["saved_count"] == 1

    source = store.get_source("SA-B001-001")
    assert source.identifiers.pmid == "19721018"
    assert source.identifiers.doi.startswith("10.7326/")
    assert source.provenance.metadata["run_id"] == manifest.run_id


def test_batch001_replay_matches_all_identifiers(tmp_path):
    connector = FixturePubMedConnector(
        ROOT / "fixtures/pubmed_batch001_articles.json"
    )
    store = SQLiteStore(tmp_path / "replay.db")

    report = replay_batch001(
        ROOT / "fixtures/Batch001_Verified_SourceArtifact_Registry_v0.1.yaml",
        connector,
        store,
    )

    assert report.status == "PASS"
    assert report.expected_count == 20
    assert report.stored_count == 20
    assert report.pmid_match_count == 20
    assert report.doi_match_count == 20
    assert report.mismatch_count == 0
