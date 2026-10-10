#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R1.3 production entrypoint.

Content identity is delegated to identity_evaluator. This module re-exports
the production functions so tests and the replay auditor share one implementation.
"""

from tools.source_archive_verifier.identity_evaluator import (  # noqa: F401
    aggregate_identity_gate,
    aggregate_provenance_gate,
    aggregate_rights_gate,
    aggregate_study_type_gate,
    calculate_sha256,
    evaluate_acquisition_provenance,
    evaluate_content_completeness,
    evaluate_manifest_integrity,
    evaluate_pdf_identity_canonical,
    evaluate_rights_posture,
    normalize_text_canonical,
    normalize_title_canonical,
    replay_proof_anchor,
    resolve_administrative_hold,
    semantic_verdict,
)

def main():
    from tools.source_archive_verifier.r1_3_replay_auditor import main as run_audit
    run_audit()


if __name__ == "__main__":
    main()
