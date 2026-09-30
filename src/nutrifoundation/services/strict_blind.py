from __future__ import annotations

from pathlib import Path

from nutrifoundation.adapters.chat_window import ChatWindowFileBridge
from nutrifoundation.domain.semantic_equivalence import StrictBlindAttestation


def validate_strict_blind_responses(response_dir: str | Path) -> StrictBlindAttestation:
    bridge = ChatWindowFileBridge()
    paths = sorted(Path(response_dir).glob("*.response.json"))
    if not paths:
        return StrictBlindAttestation(
            fresh_context=False,
            prior_batch_exposure=True,
            hidden_reference_available_to_worker=False,
            independent_worker_session=False,
        )

    responses = [bridge.load_response(path) for path in paths]
    metadata = [response.worker.metadata for response in responses]

    fresh_context = all(bool(item.get("fresh_context_attestation")) for item in metadata)
    prior_batch_exposure = any(bool(item.get("prior_batch_exposure", True)) for item in metadata)
    hidden_reference_available = any(
        bool(item.get("hidden_reference_available_to_worker", False))
        for item in metadata
    )
    independent_worker_session = all(
        bool(item.get("independent_worker_session"))
        for item in metadata
    )

    return StrictBlindAttestation(
        fresh_context=fresh_context,
        prior_batch_exposure=prior_batch_exposure,
        hidden_reference_available_to_worker=hidden_reference_available,
        independent_worker_session=independent_worker_session,
    )


def require_strict_blind(response_dir: str | Path) -> StrictBlindAttestation:
    attestation = validate_strict_blind_responses(response_dir)
    if not attestation.qualifies:
        raise ValueError(
            "Response set does not qualify for strict_blind_fresh_context: "
            f"{attestation.as_dict()}"
        )
    return attestation
