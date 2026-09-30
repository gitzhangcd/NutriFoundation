from __future__ import annotations

from pathlib import Path
from typing import Any

from nutrifoundation.domain.blind_replay import BlindnessClass
from nutrifoundation.services.blind_runner import score_blind_artifact_run
from nutrifoundation.services.canonical_batch_scoring import score_canonical_batch
from nutrifoundation.services.strict_blind import require_strict_blind


def score_strict_blind_batch(
    *,
    source_fixture_path: str | Path,
    response_dir: str | Path,
    hidden_reference_path: str | Path,
    db_path: str | Path,
    batch_id: str = "B001",
) -> dict[str, Any]:
    attestation = require_strict_blind(response_dir)

    operational = score_blind_artifact_run(
        source_fixture_path=source_fixture_path,
        response_dir=response_dir,
        hidden_gold_path=hidden_reference_path,
        db_path=db_path,
        batch_id=batch_id,
        blindness_class=BlindnessClass.STRICT,
    )
    canonical = score_canonical_batch(
        response_dir=response_dir,
        hidden_reference_path=hidden_reference_path,
        batch_id=batch_id,
    )

    return {
        "strict_blind_attestation": attestation.as_dict(),
        "operational_blind_replay": operational.as_dict(),
        "canonical_semantic_scoring": canonical.as_dict(),
    }
