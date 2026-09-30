from pathlib import Path
import json
import yaml


ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT / "paper_c" / "P0"


def load_yaml(name):
    return yaml.safe_load((P0 / name).read_text(encoding="utf-8"))


def test_paper_c_baseline_namespace_is_frozen():
    data = load_yaml("AB0_AB6_Baseline_Contract_v0.1.yaml")
    ids = [item["id"] for item in data["baselines"]]
    assert ids == ["AB0", "AB1", "AB2", "AB3", "AB4", "AB5", "AB6"]
    assert data["fairness_contract"]["same_foundation_model_AB1_AB6"] is True
    assert data["fairness_contract"]["hidden_gold_visible_during_run"] is False


def test_gold100_exact_slot_count_and_blocks():
    data = json.loads(
        (P0 / "Gold100_Source_Slot_Manifest_v0.1.json").read_text(encoding="utf-8")
    )
    slots = data["slots"]
    assert len(slots) == 100
    assert len({x["slot_id"] for x in slots}) == 100
    assert sum(x["block"] == "core" for x in slots) == 80
    assert sum(x["block"] == "stress" for x in slots) == 20
    assert sum(
        x["domain_target"] == "nutrition_metabolic_cardiometabolic"
        for x in slots
    ) == 80
    assert sum(
        x["domain_target"] == "external_biomedical_or_public_health"
        for x in slots
    ) == 20


def test_gold100_contract_excludes_batch001_from_confirmation():
    data = load_yaml("Gold100_Corpus_Contract_v0.1.yaml")
    exclusion = data["development_exclusion"]
    assert exclusion["corpus"] == "Batch001"
    assert exclusion["source_count"] == 20
    assert exclusion["confirmatory_use"] == "prohibited"
    assert data["confirmatory_corpus"]["source_count"] == 100
    assert data["sampling"]["random_seed"] == 20260930


def test_endpoint_contract_freezes_cser_and_human_burden_gate():
    data = load_yaml("Endpoint_Statistical_Contract_v0.1.yaml")
    assert data["primary_endpoint"]["id"] == "CSER"
    gate = data["co_primary_publication_gate_for_AB6"]
    assert gate["safety_noninferiority"]["absolute_margin"] == 0.02
    assert gate["absolute_safety_ceiling"]["CSER_max_point_estimate"] == 0.05
    assert gate["human_burden_superiority"]["HBR_min_point_estimate"] == 0.30
    assert gate["success_requires_all"] is True
    assert data["statistics"]["bootstrap_resamples"] == 10000


def test_publication_kill_registry_is_nontrivial_and_covers_core_failures():
    data = load_yaml("Publication_Kill_Test_Registry_v0.1.yaml")
    tests = data["kill_tests"]
    assert len(tests) >= 14
    ids = {x["id"] for x in tests}
    assert {"K01", "K02", "K03", "K04", "K05", "K07", "K08", "K12", "K14"} <= ids


def test_confirmatory_blindness_and_no_posthoc_adaptation_are_frozen():
    baselines = load_yaml("AB0_AB6_Baseline_Contract_v0.1.yaml")
    assert baselines["prohibited_shortcuts"]
    assert "using_hidden_gold_to_route_or_repair" in baselines["prohibited_shortcuts"]
    assert "changing_prompts_after_Gold100_results_are_seen" in baselines["prohibited_shortcuts"]
    kills = load_yaml("Publication_Kill_Test_Registry_v0.1.yaml")
    by_id = {x["id"]: x for x in kills["kill_tests"]}
    assert "invalidate_confirmatory_model_accuracy_claim" in by_id["K12"]["consequence"]
    assert "invalidate_confirmatory_claim" in by_id["K14"]["consequence"]


def test_paper_c_p0_execution_pack_is_complete():
    required = [
        "P0_Execution_Report.md",
        "Paper_C_P0_Scientific_Evidence_Production_Study_v0.1.md",
        "Literature_Positioning_v0.1.md",
        "AB0_AB6_Baseline_Contract_v0.1.yaml",
        "Gold100_Corpus_Contract_v0.1.yaml",
        "Gold100_Source_Slot_Manifest_v0.1.json",
        "Endpoint_Statistical_Contract_v0.1.yaml",
        "Publication_Kill_Test_Registry_v0.1.yaml",
    ]
    assert all((P0 / name).exists() for name in required)
