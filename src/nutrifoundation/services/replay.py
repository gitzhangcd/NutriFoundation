from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from nutrifoundation.connectors.ncbi import PubMedProvider
from nutrifoundation.io.loaders import load_structured
from nutrifoundation.persistence.sqlite import SQLiteStore
from nutrifoundation.services.ingestion import SourceArtifactIngestionService


@dataclass(frozen=True)
class ReplayReport:
    expected_count: int
    stored_count: int
    pmid_match_count: int
    doi_match_count: int
    mismatch_count: int
    mismatches: tuple[dict[str, Any], ...]
    run_id: str
    status: str

    def as_dict(self):
        return asdict(self)


def replay_batch001(
    registry_path: str | Path,
    connector: PubMedProvider,
    store: SQLiteStore,
    *,
    mode: str = "offline_replay",
) -> ReplayReport:
    registry = load_structured(registry_path)
    expected = registry["sources"]

    mapping = [
        (source["source_id"], str(source["pmid"]))
        for source in expected
    ]

    manifest = SourceArtifactIngestionService(
        connector,
        store,
        mode=mode,
    ).ingest(mapping)

    saved = {source.source_id: source for source in store.list_sources()}

    mismatches = []
    pmid_matches = 0
    doi_matches = 0

    for expected_source in expected:
        source_id = expected_source["source_id"]
        actual = saved.get(source_id)

        if actual is None:
            mismatches.append(
                {
                    "source_id": source_id,
                    "field": "source",
                    "expected": "present",
                    "actual": "missing",
                }
            )
            continue

        expected_pmid = str(expected_source["pmid"])
        if actual.identifiers.pmid == expected_pmid:
            pmid_matches += 1
        else:
            mismatches.append(
                {
                    "source_id": source_id,
                    "field": "pmid",
                    "expected": expected_pmid,
                    "actual": actual.identifiers.pmid,
                }
            )

        expected_doi = (expected_source.get("doi") or "").lower().strip()
        actual_doi = (actual.identifiers.doi or "").lower().strip()

        if expected_doi == actual_doi:
            doi_matches += 1
        else:
            mismatches.append(
                {
                    "source_id": source_id,
                    "field": "doi",
                    "expected": expected_doi,
                    "actual": actual_doi,
                }
            )

    status = (
        "PASS"
        if not mismatches and manifest.status == "completed"
        else "FAIL"
    )

    return ReplayReport(
        expected_count=len(expected),
        stored_count=len(saved),
        pmid_match_count=pmid_matches,
        doi_match_count=doi_matches,
        mismatch_count=len(mismatches),
        mismatches=tuple(mismatches),
        run_id=manifest.run_id,
        status=status,
    )
