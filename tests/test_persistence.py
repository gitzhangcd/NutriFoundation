from datetime import datetime, timezone

from nutrifoundation.domain.enums import SourceType
from nutrifoundation.domain.models import Provenance, SourceArtifact, SourceIdentifiers
from nutrifoundation.domain.run_manifest import RunManifest
from nutrifoundation.persistence.sqlite import SQLiteStore


def test_sqlite_roundtrip(tmp_path):
    store = SQLiteStore(tmp_path / "x.db")
    store.initialize()

    source = SourceArtifact(
        source_id="SA-1",
        source_type=SourceType.RCT,
        title="Trial",
        identifiers=SourceIdentifiers(pmid="1", doi="10/x"),
        provenance=Provenance(source="fixture"),
    )

    store.upsert_source(source)
    assert store.get_source("SA-1") == source


def test_run_manifest_persists(tmp_path):
    store = SQLiteStore(tmp_path / "x.db")
    store.initialize()

    manifest = RunManifest(
        run_id="RUN-1",
        pipeline_name="test",
        pipeline_version="E0.2",
        mode="test",
        started_at=datetime.now(timezone.utc),
    )

    store.save_run_manifest(manifest)

    import sqlite3

    connection = sqlite3.connect(tmp_path / "x.db")
    row = connection.execute(
        "SELECT run_id,status FROM run_manifest"
    ).fetchone()
    connection.close()

    assert row == ("RUN-1", "running")
