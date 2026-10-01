from datetime import datetime, timezone
from pathlib import Path

import pytest

from nutrifoundation.evaluation.v2.runner import (
    run_frozen_response_set_v2,
    sha256_file,
    write_batch_report_v2,
)


ROOT = Path(__file__).resolve().parents[2]
RESPONSE_SET = ROOT / "runs/E0.4.2/A0/StrictBlind_ResponseSet_FROZEN_v1.0.json"
SOURCE_FIXTURE = ROOT / "fixtures/Batch001_Blind_SourceText_v0.1.json"
HIDDEN_REFERENCE = ROOT / "fixtures/Batch001_EvidenceUnit_Frozen_v0.1.yaml"
TASK_MANIFEST = ROOT / "runs/E0.4.2/A0/StrictBlind_TaskPack_Manifest_v1.0.json"
RESPONSE_SHA = "f5cc39f4d0394f5928eb5142c5c4aa43dab638ea2077fbcd2950f4f64a66d0c7"
STAMP = datetime(2026, 10, 1, 4, 36, 7, tzinfo=timezone.utc)


@pytest.fixture(scope="module")
def report():
    return run_frozen_response_set_v2(
        response_set_path=RESPONSE_SET,
        source_fixture_path=SOURCE_FIXTURE,
        hidden_reference_path=HIDDEN_REFERENCE,
        task_manifest_path=TASK_MANIFEST,
        evaluated_at=STAMP,
        expected_response_set_sha256=RESPONSE_SHA,
    )


def test_strict_blind_frozen_response_set_sha_and_counts_are_preserved(report):
    assert sha256_file(RESPONSE_SET) == RESPONSE_SHA
    assert report.response_set.sha256 == RESPONSE_SHA
    assert report.response_set.response_count == 20
    assert report.response_set.completed_count == 19
    assert report.response_set.deferred_count == 1
    assert report.response_set.failed_count == 0


def test_batch_runner_requires_strict_blind_qualification(report):
    attestation = report.response_set.attestation
    assert attestation.fresh_context is True
    assert attestation.prior_batch_exposure is False
    assert attestation.hidden_reference_available_to_worker is False
    assert attestation.independent_worker_session is True
    assert attestation.blindness_class == "strict_blind_fresh_context"
    assert attestation.qualifies is True


def test_report_version_is_frozen(report):
    assert report.report_version == "E0.4.2-E3-A2.6-v1.0"
    assert report.evaluator_version == "EvaluatorV2-v0.1"


def test_report_keeps_f0_reference_authority_boundary(report):
    assert (
        report.reference_authority
        == "Batch001_F0_reference_not_independent_expert_gold"
    )
    assert report.publication_grade is False


def test_report_has_five_dimensions_and_no_overall_score(report):
    summary = {item.dimension: item for item in report.dimension_summary}
    assert set(summary) == {
        "scientific_semantic_recovery",
        "ontology_alignment",
        "provenance_recovery",
        "numeric_fidelity",
        "safe_abstention_quality",
    }
    assert report.aggregation_policy["overall_score"] == "forbidden"


def test_semantic_and_ontology_aggregation_exclude_safe_defer(report):
    summary = {item.dimension: item for item in report.dimension_summary}
    assert summary["scientific_semantic_recovery"].eligible_case_count == 19
    assert summary["ontology_alignment"].eligible_case_count == 19


def test_numeric_aggregation_uses_only_reference_numeric_cases(report):
    summary = {item.dimension: item for item in report.dimension_summary}
    numeric = summary["numeric_fidelity"]
    assert 0 < numeric.eligible_case_count <= 19
    assert numeric.scored_case_count == numeric.eligible_case_count


def test_task015_is_the_single_applicable_safe_abstention_case(report):
    summary = {item.dimension: item for item in report.dimension_summary}
    abstention = summary["safe_abstention_quality"]
    assert abstention.eligible_case_count == 1
    assert abstention.scored_case_count == 1
    assert abstention.mean_score == 1.0

    case = next(item for item in report.cases if item.evidence_id == "EU-B001-015")
    assert case.response_status == "defer"
    assert case.score_vector["safe_abstention_quality"] == 1.0


def test_batch_runner_is_deterministic_for_fixed_evaluation_time(report):
    repeated = run_frozen_response_set_v2(
        response_set_path=RESPONSE_SET,
        source_fixture_path=SOURCE_FIXTURE,
        hidden_reference_path=HIDDEN_REFERENCE,
        task_manifest_path=TASK_MANIFEST,
        evaluated_at=STAMP,
        expected_response_set_sha256=RESPONSE_SHA,
    )
    assert repeated.model_dump(mode="json") == report.model_dump(mode="json")


def test_batch_runner_does_not_mutate_frozen_response_set(report):
    before = sha256_file(RESPONSE_SET)
    _ = report.compact_summary()
    after = sha256_file(RESPONSE_SET)
    assert before == after == RESPONSE_SHA


def test_report_writer_emits_versioned_json_and_checksum(report, tmp_path):
    path = tmp_path / "Evaluator_V2_Batch_Report_v1.0.json"
    digest = write_batch_report_v2(report, path)
    assert path.exists()
    checksum = path.with_suffix(path.suffix + ".sha256")
    assert checksum.read_text(encoding="utf-8") == f"{digest}  {path.name}\n"


def test_incorrect_response_set_hash_is_rejected():
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        run_frozen_response_set_v2(
            response_set_path=RESPONSE_SET,
            source_fixture_path=SOURCE_FIXTURE,
            hidden_reference_path=HIDDEN_REFERENCE,
            task_manifest_path=TASK_MANIFEST,
            evaluated_at=STAMP,
            expected_response_set_sha256="0" * 64,
        )
