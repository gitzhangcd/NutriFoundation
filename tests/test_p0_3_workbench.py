import hashlib
import json
import pytest

from nutrifoundation.workbench.p0_3 import (
    AccessDenied,
    InvalidState,
    LockedRecordError,
    P03Workbench,
    SourceHashMismatch,
    bind_span,
    sha256_text,
    tokenize,
)


def rec(cid, round_id, text, *, incomplete=False):
    return {
        "calibration_slot_id": f"CAL-{round_id}-01",
        "round": round_id,
        "mode": "guided_training" if round_id == "A" else "blinded_reliability_validation",
        "candidate_id": cid,
        "pmid": "12345",
        "pmcid": None,
        "doi": None,
        "title": f"Fixture {cid}",
        "source_family": "primary_interventional",
        "domain": "nutrition_metabolic_cardiometabolic",
        "study_identity_cluster_id": f"PMID:{cid}",
        "source_text_status": "structured_abstract_only" if incomplete else "official_full_text_frozen",
        "worker_visible_text_sha256": sha256_text(text),
        "challenge_tags": {"incomplete_source_text": incomplete},
    }


TEXT_A = "Alpha beta gamma delta epsilon."
TEXT_B = "One two three four five."
A = rec("CAL-A-SRC", "A", TEXT_A)
B = rec("CAL-B-SRC", "B", TEXT_B)


def payload():
    return {
        "scientific_payload": {
            "study_identity": {"applicable": False},
            "evidence_units": [],
            "applicability_boundary": {"level": "source_level_evidence_scope", "dimensions": {}},
            "source_spans": [],
            "critical_error_opportunities": [],
            "annotation_quality": {"completeness": "complete"},
        },
        "independence_attestation": {
            "no_Gold100_source_access": True,
            "no_AB_outputs_seen": True,
            "no_evaluator_scores_seen": True,
            "no_other_annotator_first_pass_seen_before_lock": True,
            "no_discussion_before_lock": True,
            "conflict_of_interest_declared": True,
            "conflict_of_interest_note": None,
        },
        "timing": {"active_annotation_seconds": 12, "pause_seconds": 0, "discussion_seconds": None},
    }


@pytest.fixture
def wb(tmp_path):
    texts = {"CAL-A-SRC": TEXT_A, "CAL-B-SRC": TEXT_B}
    return P03Workbench(
        tmp_path / "wb.sqlite3",
        [A, B],
        {"GOLD-001"},
        source_loader=lambda r: texts[r["candidate_id"]],
    )


def test_source_hash_mismatch_blocks(tmp_path):
    x = rec("BAD", "A", "expected")
    w = P03Workbench(tmp_path / "x.sqlite3", [x], set(), source_loader=lambda r: "different")
    with pytest.raises(SourceHashMismatch):
        w.source("BAD")


def test_gold100_access_denied_and_audited(wb):
    with pytest.raises(AccessDenied):
        wb.source("GOLD-001")
    assert wb.verify_audit_chain()


def test_span_roundtrip_is_stable(wb):
    src = wb.source("CAL-A-SRC")
    assert src["tokens"][1]["text"] == "beta"
    span = wb.bind_span("CAL-A-SRC", 1, 4, ["EU-1"])
    assert span["exact_text"] == "beta gamma delta"
    assert span["start_token"] == 1 and span["end_token"] == 4
    assert span["source_text_sha256"] == sha256_text(TEXT_A)


def test_peer_hidden_until_both_locks_and_locked_record_immutable(wb):
    p = payload()
    wb.save_draft("CAL-A-SRC", "A", "expert-a", p)
    wb.lock("CAL-A-SRC", "A", "expert-a")
    with pytest.raises(AccessDenied):
        wb.peer_record("CAL-A-SRC", "A")
    with pytest.raises(LockedRecordError):
        wb.save_draft("CAL-A-SRC", "A", "expert-a", p)
    wb.save_draft("CAL-A-SRC", "B", "expert-b", p)
    wb.lock("CAL-A-SRC", "B", "expert-b")
    peer = wb.peer_record("CAL-A-SRC", "A")
    assert peer["status"] == "FIRST_PASS_LOCKED"
    assert wb.discussion_allowed("CAL-A-SRC") is True


def test_lock_requires_all_independence_attestations(wb):
    p = payload()
    p["independence_attestation"]["no_AB_outputs_seen"] = False
    wb.save_draft("CAL-A-SRC", "A", "expert-a", p)
    with pytest.raises(InvalidState):
        wb.lock("CAL-A-SRC", "A", "expert-a")


def test_round_b_discussion_requires_metric_freeze(wb):
    p = payload()
    for role in ("A", "B"):
        wb.save_draft("CAL-B-SRC", role, f"expert-{role.lower()}", p)
        wb.lock("CAL-B-SRC", role, f"expert-{role.lower()}")
    assert wb.pair_locked("CAL-B-SRC")
    assert wb.discussion_allowed("CAL-B-SRC") is False
    wb.freeze_round_b_metric("a" * 64)
    assert wb.discussion_allowed("CAL-B-SRC") is True


def test_export_contains_hash_and_hash_chained_audit(wb):
    p = payload()
    wb.source("CAL-A-SRC", role="A", pseudonym="expert-a")
    wb.save_draft("CAL-A-SRC", "A", "expert-a", p)
    locked = wb.lock("CAL-A-SRC", "A", "expert-a")
    exported = wb.export_record("CAL-A-SRC", "A")
    assert exported["record"]["record_sha256"] == locked["first_pass_lock"]["canonical_record_sha256"]
    assert exported["record"]["payload"]["source_binding"]["exact_source_text_sha256"] == sha256_text(TEXT_A)
    assert exported["audit_events"]
    assert wb.verify_audit_chain()


def test_tokenizer_half_open_contract():
    t = "a  bb\nccc"
    toks = tokenize(t)
    assert [x["text"] for x in toks] == ["a", "bb", "ccc"]
    span = bind_span(t, sha256_text(t), 1, 3, [])
    assert span["exact_text"] == "bb\nccc"


def test_repository_manifests_load_without_gold_leakage(tmp_path):
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    w = P03Workbench.from_repo(root, tmp_path / "repo.sqlite3", source_loader=lambda r: "")
    assert len(w.records) == 24
    assert len(w.gold100_ids) == 100
    assert not (set(w.records) & w.gold100_ids)
