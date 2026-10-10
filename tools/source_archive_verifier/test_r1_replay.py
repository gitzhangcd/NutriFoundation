#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_r1_replay.py - R1.2 规范核验器与负向控制自动化单元测试套件

【核心测试原则】
1. 生产与测试 100% 共享调用 evaluate_pdf_identity_canonical()，绝不在测试端另写简化逻辑。
2. 覆盖针对 RA-01 ~ RA-04 的 6 类核心负向与阳性基准用例 (NC-01 ~ NC-06)。
3. 覆盖分块流式哈希计算、损坏 PDF 异常处理与文本规范化。
"""

import inspect
import unittest
import os
import sys
import tempfile
import hashlib
from pathlib import Path
import fitz  # PyMuPDF

# 确保能导入生产模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from tools.source_archive_verifier import r1_independent_replay_verifier as prod
from tools.source_archive_verifier.r1_independent_replay_verifier import (
    evaluate_pdf_identity_canonical,
    calculate_sha256,
    normalize_text_canonical,
    normalize_title_canonical
)

TARGET_TITLE = "Long Term Dietary Intervention for Diabetes Remission in Adults"
TARGET_DOI = "10.1001/jama.2026.target777"


class TestR1_2_CanonicalValidator(unittest.TestCase):

    def assert_mechanism(self, res, verdict, status, rule):
        self.assertEqual(res["identity_verdict"], verdict)
        self.assertEqual(res["observed_identity_verdict"], verdict)
        self.assertEqual(res["identity_status"], status)
        self.assertEqual(res["match_rule"], rule)
        anchor = res["proof_anchor"]
        self.assertIsInstance(anchor, dict)
        self.assertIn("page", anchor)
        self.assertIn("literal_text", anchor)
        self.assertTrue("char_span" in anchor or "bbox" in anchor)

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_mock_pdf(self, filename: str, pages: list[str]) -> Path:
        pdf_path = Path(self.temp_dir.name) / filename
        doc = fitz.open()
        for p_txt in pages:
            page = doc.new_page()
            page.insert_text((50, 72), p_txt)
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def test_nc01_doi_in_references_only(self):
        """NC-01: 第一页为无关论文，仅在末尾参考文献引用了目标 DOI -> 生产必须 HOLD"""
        pdf_path = self._create_mock_pdf("nc01.pdf", [
            "Effects of Vitamin D on Bone Mineral Density in Postmenopausal Women\nAuthors: Jane Doe, et al.\nIntroduction...\n",
            "Methods: Cohort study...\nResults: BMD increased...\nReferences:\n1. Target Diabetes Trial. JAMA. doi: 10.1001/jama.2026.target01\n"
        ])

        res = evaluate_pdf_identity_canonical(
            pdf_path=pdf_path,
            expected_title="Randomized Trial of Very Low Carbohydrate Diet on Diabetes Remission",
            expected_doi="10.1001/jama.2026.target01",
            expected_pmid="12345678"
        )
        self.assertEqual(res["identity_verdict"], "HOLD")
        self.assertEqual(res["identity_status"], "DOI_IN_REFERENCES_ONLY")
        self.assertIn("DOI_FOUND_ONLY_IN_BIBLIOGRAPHY", res["conflict_features"])

    def test_nc02_dispersed_keywords_rejected(self):
        """NC-02: 术语表中分散包含目标标题的单词，无连贯标题短语 -> 生产必须 HOLD"""
        pdf_path = self._create_mock_pdf("nc02.pdf", [
            "Glossary of Nutritional Terms:\n- Effects: physiological consequences.\n- Dietary: relating to food consumption.\n- Interventions: clinical trials.\n- Adults: aged over 18.\n- Metabolic: biochemical pathways.\n- Syndrome: cluster of conditions.\n- Randomized: assigned by chance.\n"
        ])

        res = evaluate_pdf_identity_canonical(
            pdf_path=pdf_path,
            expected_title="Effects of dietary interventions in adults with metabolic syndrome: a randomized trial",
            expected_doi="10.1001/jama.2026.target02",
            expected_pmid="23456789"
        )
        self.assertEqual(res["identity_verdict"], "HOLD")
        self.assertEqual(res["identity_status"], "DISPERSED_KEYWORDS_REJECTED")
        self.assertIn("TITLE_PHRASE_NOT_COHERENT", res["conflict_features"])

    def test_nc03_cand090_wrong_pdf_rejected(self):
        """NC-03: 给 CAND-G100-090 提供无关 PDF，验证是否取消了代码硬编码放行 -> 生产必须 HOLD"""
        pdf_path = self._create_mock_pdf("nc03.pdf", [
            "Cardiology Update 2026: Surgical Treatment of Aortic Valve Stenosis\nAuthors: Heart Team\nNo nutrition content here.\n"
        ])

        res = evaluate_pdf_identity_canonical(
            pdf_path=pdf_path,
            expected_title="Effects of time-restricted eating and low-carbohydrate diet on psychosocial health and appetite in individuals with metabolic syndrome",
            expected_doi="10.1016/j.clnu.2024.08.029",
            expected_pmid="39226719",
            source_id="CAND-G100-090"  # 即使传入目标 SourceID，若 PDF 内容不对，也绝不能放行！
        )
        self.assertEqual(res["identity_verdict"], "HOLD")
        self.assertNotEqual(res["identity_verdict"], "CONFIRMED")
        self.assertNotEqual(res["identity_verdict"], "PASS")

    def test_nc04_true_positive_grounded(self):
        """NC-04: 真实题录与正文头部连续标题和 DOI 协同吻合 -> 生产允许 CONFIRMED"""
        pdf_path = self._create_mock_pdf("nc04.pdf", [
            "Original Investigation | Diabetes\nLow-Carbohydrate Dietary Intervention on Glycemic Control in Adults\ndoi: 10.1001/jama.2026.valid04\nPMID: 34567890\nAbstract: We conducted a randomized clinical trial..."
        ])

        res = evaluate_pdf_identity_canonical(
            pdf_path=pdf_path,
            expected_title="Low-Carbohydrate Dietary Intervention on Glycemic Control in Adults",
            expected_doi="10.1001/jama.2026.valid04",
            expected_pmid="34567890"
        )
        self.assertEqual(res["identity_verdict"], "CONFIRMED")
        self.assertIn("CONFIRMED", res["identity_status"])

    def test_nc05_doi_title_conflict_rejected(self):
        """NC-05: PDF 真实 DOI 属于文章 A，而预期标题属于文章 B -> 生产必须 HOLD"""
        pdf_path = self._create_mock_pdf("nc05.pdf", [
            "Cardiovascular Outcomes in Multiethnic Study of Atherosclerosis\ndoi: 10.1016/j.jacadv.2025.conf05\nAbstract: In this cohort study of cardiovascular disease..."
        ])

        res = evaluate_pdf_identity_canonical(
            pdf_path=pdf_path,
            expected_title="Association of ultra-processed food consumption with all cause mortality: BMJ cohort",
            expected_doi="10.1136/bmj.2023.other",
            expected_pmid="45678901"
        )
        self.assertEqual(res["identity_verdict"], "HOLD")
        self.assertEqual(res["identity_status"], "CONFLICTING_DOI_DETECTED")
        self.assert_mechanism(
            res,
            "HOLD",
            "CONFLICTING_DOI_DETECTED",
            "COVER_DOI_CONFLICTS_WITH_EXPECTED_DOI",
        )

    def test_nc06_no_doi_valid_source_grounded(self):
        """NC-06: 缺少 DOI 但在首页具有 100% 连续标题短语和明确元数据 -> 生产允许 CONFIRMED"""
        pdf_path = self._create_mock_pdf("nc06.pdf", [
            "Chinese Dietary Guidelines 2022 Summary Report and Clinical Recommendations\nPMID: 99887766\nNational Health Commission Publication\nFull text..."
        ])

        res = evaluate_pdf_identity_canonical(
            pdf_path=pdf_path,
            expected_title="Chinese Dietary Guidelines 2022 Summary Report and Clinical Recommendations",
            expected_doi="",  # 无 DOI
            expected_pmid="99887766"
        )
        self.assertEqual(res["identity_verdict"], "CONFIRMED")
        self.assertEqual(res["identity_status"], "CONFIRMED_TITLE_NO_DOI_REQUIRED")

    def test_sha256_calculation(self):
        """测试流式 SHA256 计算精准性"""
        test_file = Path(self.temp_dir.name) / "test_sha.bin"
        content = b"NutriFoundation Canonical Replay 20261010" * 512
        with open(test_file, "wb") as f:
            f.write(content)

        exp_h = hashlib.sha256(content).hexdigest()
        obs_h = calculate_sha256(test_file)
        self.assertEqual(obs_h, exp_h)

    def test_corrupted_pdf_handling(self):
        """测试语法错误损坏 PDF 的容错处理"""
        corrupted_file = Path(self.temp_dir.name) / "corrupted.pdf"
        with open(corrupted_file, "wb") as f:
            f.write(b"%PDF-1.4\nInvalid broken syntax bytes")

        res = evaluate_pdf_identity_canonical(
            pdf_path=corrupted_file,
            expected_title="Any Title",
            expected_doi="10.1234/test",
            expected_pmid="123"
        )
        self.assertEqual(res["identity_verdict"], "HOLD")
        self.assertEqual(res["identity_status"], "CONTAINER_ERROR")

    def test_normalization_helpers(self):
        """测试文本与标题标准化函数鲁棒性"""
        raw = "Effects   of  time-restricted \n eating   and  low-carbohydrate  diet"
        norm = normalize_title_canonical(raw)
        self.assertEqual(norm, "effects of time restricted eating and low carbohydrate diet")


class TestR1_3_AdversarialMechanisms(unittest.TestCase):
    """机制级对抗测试。断言 verdict + identity_status + match_rule + proof_anchor。"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _pdf(self, name: str, pages: list[str]) -> Path:
        pdf_path = Path(self.temp_dir.name) / name
        doc = fitz.open()
        for text in pages:
            page = doc.new_page()
            page.insert_text((30, 72), text, fontsize=9)
        doc.save(str(pdf_path))
        doc.close()
        return pdf_path

    def assert_mechanism(self, res, verdict, status, rule):
        self.assertEqual(res["identity_verdict"], verdict)
        self.assertEqual(res["observed_identity_verdict"], verdict)
        self.assertEqual(res["identity_status"], status)
        self.assertEqual(res["match_rule"], rule)
        anchor = res["proof_anchor"]
        self.assertIsInstance(anchor, dict)
        self.assertGreaterEqual(anchor["page"], 1)
        self.assertIsInstance(anchor["literal_text"], str)
        self.assertTrue(anchor["literal_text"])
        self.assertIn("char_span", anchor)
        self.assertEqual(len(anchor["char_span"]), 2)
        self.assertIn("bbox", anchor)

    def test_at01_references_contain_full_title_and_doi(self):
        pdf = self._pdf("at01.pdf", [
            "Unrelated Article on Tree Physiology\n"
            "Authors: Botanical Research Group\n"
            "Abstract: Plants absorb sunlight.\n"
            "References:\n"
            "1. Long Term Dietary Intervention for Diabetes Remission in Adults\n"
            "doi: 10.1001/jama.2026.target777\n"
        ])
        res = evaluate_pdf_identity_canonical(pdf, TARGET_TITLE, TARGET_DOI, "")
        self.assert_mechanism(
            res, "HOLD", "REFERENCE_REGION_NOT_DOCUMENT_IDENTITY",
            "TITLE_AND_DOI_IN_REFERENCES_ONLY",
        )
        self.assertEqual(res["proof_anchor"]["region"], "REFERENCES")

    def test_at02_prefix_six_words_divergent_title(self):
        pdf = self._pdf("at02.pdf", [
            "Original Study\n"
            "Long Term Dietary Intervention for Diabetes Remission in Fishes\n"
            "DOI: 10.9999/fish.2026.001\n"
        ])
        res = evaluate_pdf_identity_canonical(pdf, TARGET_TITLE, TARGET_DOI, "")
        self.assert_mechanism(
            res, "HOLD", "TITLE_PREFIX_ONLY_DIVERGENT",
            "PREFIX_MATCH_DOES_NOT_CONFIRM_FULL_TITLE",
        )
        self.assertNotEqual(res["identity_verdict"], "CONFIRMED")

    def test_at03_correct_pdf_not_mismatched_by_source_id(self):
        pdf = self._pdf("at03.pdf", [
            "Original Investigation\n"
            "Long Term Dietary Intervention for Diabetes Remission in Adults\n"
            "doi: 10.1001/jama.2026.target777\n"
            "Abstract: A randomized dietary intervention.\n"
        ])
        res = evaluate_pdf_identity_canonical(
            pdf, TARGET_TITLE, TARGET_DOI, "", source_id="CAND-G100-010"
        )
        self.assert_mechanism(
            res, "CONFIRMED", "CONFIRMED_TITLE_AND_DOI_GROUNDED",
            "FULL_TITLE_AND_DOI_IN_ARTICLE_IDENTITY_REGION",
        )
        self.assertFalse(res["administrative_hold"]["active"])
        self.assertNotEqual(res["identity_status"], "ASSET_MISMATCH_GOV_GUIDELINE")
        hold = prod.resolve_administrative_hold(
            source_id="CAND-G100-010",
            observed_asset_sha256=calculate_sha256(pdf),
        )
        self.assertFalse(hold["active"])
        self.assertEqual(hold["reason"], "ASSET_HASH_DOES_NOT_MATCH_QUARANTINE_ENTRY")

    def test_at04_known_hold_source_id_uses_file_content(self):
        pdf = self._pdf("at04.pdf", [
            "Unrelated Article in Clinical Genetics\n"
            "DOI: 10.1000/irrelevant.2026.1\n"
        ])
        res = evaluate_pdf_identity_canonical(
            pdf, TARGET_TITLE, TARGET_DOI, "", source_id="CAND-G100-020"
        )
        self.assertEqual(res["identity_verdict"], "HOLD")
        self.assertNotEqual(res["identity_status"], "VERSION_VARIANT_REVIEW")
        self.assertNotIn("Prediabetes Lifestyle Intervention Study", res["literal_text"])
        self.assertNotIn("PLIS", res.get("reason", ""))
        self.assertFalse(res["administrative_hold"]["active"])
        self.assertIn(res["match_rule"], {
            "COVER_DOI_CONFLICTS_WITH_EXPECTED_DOI",
            "DISPERSED_KEYWORDS_REJECTED",
            "PREFIX_MATCH_DOES_NOT_CONFIRM_FULL_TITLE",
        })
        anchor = res["proof_anchor"]
        self.assertGreaterEqual(anchor["page"], 1)
        replay = prod.replay_proof_anchor(pdf, anchor)
        self.assertTrue(replay["ok"])

    def test_at05_same_page_references_title_and_doi(self):
        pdf = self._pdf("at05.pdf", [
            "Study of Oceanic Ecosystems\n"
            "References:\n"
            "1. Long Term Dietary Intervention for Diabetes Remission in Adults\n"
            "doi: 10.1001/jama.2026.target777\n"
        ])
        res = evaluate_pdf_identity_canonical(pdf, TARGET_TITLE, TARGET_DOI, "")
        self.assert_mechanism(
            res, "HOLD", "REFERENCE_REGION_NOT_DOCUMENT_IDENTITY",
            "TITLE_AND_DOI_IN_REFERENCES_ONLY",
        )

    def test_at06_front_matter_full_title_and_doi(self):
        pdf = self._pdf("at06.pdf", [
            "Original Investigation\n"
            "Long Term Dietary Intervention for Diabetes Remission in Adults\n"
            "doi: 10.1001/jama.2026.target777\n"
            "Authors: Nutrition Trial Group\n"
            "Abstract: Adults with diabetes were enrolled.\n"
        ])
        res = evaluate_pdf_identity_canonical(pdf, TARGET_TITLE, TARGET_DOI, "")
        self.assert_mechanism(
            res, "CONFIRMED", "CONFIRMED_TITLE_AND_DOI_GROUNDED",
            "FULL_TITLE_AND_DOI_IN_ARTICLE_IDENTITY_REGION",
        )
        self.assertEqual(res["proof_anchor"]["region"], "FRONT_MATTER")
        self.assertTrue(prod.replay_proof_anchor(pdf, res["proof_anchor"])["ok"])

    def test_at07_no_doi_guideline_secondary_credentials(self):
        pdf = self._pdf("at07.pdf", [
            "National Health Commission\n"
            "Chinese Adult Weight Management Guideline\n"
            "Version 2.1\n"
            "Publication date: 2024 March\n"
            "PMID: 88776655\n"
            "Abstract: This guideline states assessment prerequisites.\n"
        ])
        res = evaluate_pdf_identity_canonical(
            pdf,
            "Chinese Adult Weight Management Guideline",
            "",
            "88776655",
            expected_date="2024 March",
            expected_publisher="National Health Commission",
        )
        self.assert_mechanism(
            res, "CONFIRMED", "CONFIRMED_TITLE_NO_DOI_REQUIRED",
            "NO_DOI_SECONDARY_CREDENTIAL_POLICY",
        )
        self.assertEqual(res["policy_id"], "NO_DOI_REQUIRES_TWO_SECONDARY_CREDENTIALS_V1")
        self.assertGreaterEqual(len(res["secondary_credentials"]), 2)

    def test_at08_cover_doi_conflicts_with_expected(self):
        pdf = self._pdf("at08.pdf", [
            "Long Term Dietary Intervention for Diabetes Remission in Adults\n"
            "doi: 10.9999/conflict.2026.1\n"
            "Abstract: A different version identifier is printed on the cover.\n"
        ])
        res = evaluate_pdf_identity_canonical(pdf, TARGET_TITLE, TARGET_DOI, "")
        self.assertIn(res["identity_verdict"], {"HOLD", "MISMATCH"})
        self.assertEqual(res["identity_status"], "COVER_DOI_CONFLICT")
        self.assertEqual(res["match_rule"], "COVER_DOI_CONFLICTS_WITH_EXPECTED_DOI")
        self.assertIn("10.9999/conflict.2026.1", res["proof_anchor"]["literal_text"].lower())
        self.assertTrue(prod.replay_proof_anchor(pdf, res["proof_anchor"])["ok"])

    def test_at09_channel_string_without_download_log_is_not_verified(self):
        res = prod.evaluate_acquisition_provenance(
            reported_channel="AUTHENTICATED_CHROME_BROWSER",
            download_log=None,
            observed_asset_sha256="abc123",
        )
        self.assertNotEqual(res["acquisition_provenance"], "VERIFIED")
        self.assertIn(res["acquisition_provenance"], {"EVIDENCE_PENDING", "UNVERIFIED"})
        self.assertIn("ACQUISITION_CHANNEL_IS_NOT_PROVENANCE", res["triggered_rules"])

    def test_at10_truncated_or_cover_only_is_not_complete(self):
        cases = [
            ("cover.pdf", ["Cover page only\nDietary Guidelines cover sheet\n"]),
            ("trunc.pdf", [
                "Methods and results begin here.\n",
                "The article text is truncated before the bibliography.\n",
            ]),
            ("missing.pdf", ["Weight management review.\nPage 1 of 12\nOnly the cover was captured.\n"]),
        ]
        for name, pages in cases:
            pdf = self._pdf(name, pages)
            res = prod.evaluate_content_completeness(pdf)
            self.assertNotEqual(res["content_completeness"], "COMPLETE", msg=name)
            self.assertIn(res["content_completeness"], {"PARTIAL", "NOT_ASSESSED", "UNRESOLVED"})
            self.assertTrue(res["completeness_scope"])
            self.assertTrue(res["evidence"])

    def test_at11_anchor_round_trip_and_mutation(self):
        pdf = self._pdf("at11.pdf", [
            "Original Investigation\n"
            "Long Term Dietary Intervention for Diabetes Remission in Adults\n"
            "doi: 10.1001/jama.2026.target777\n"
            "Abstract: Round trip anchor check.\n"
        ])
        res = evaluate_pdf_identity_canonical(pdf, TARGET_TITLE, TARGET_DOI, "")
        self.assertEqual(res["identity_verdict"], "CONFIRMED")
        replay = prod.replay_proof_anchor(pdf, res["proof_anchor"])
        self.assertTrue(replay["ok"])
        self.assertEqual(replay["observed_literal_text"], res["proof_anchor"]["literal_text"])
        mutated = self._pdf("at11_mut.pdf", [
            "Original Investigation\n"
            "Short Unrelated Title About Ocean Currents\n"
            "doi: 10.1000/other\n"
        ])
        mutated_replay = prod.replay_proof_anchor(mutated, res["proof_anchor"])
        self.assertFalse(mutated_replay["ok"])

    def test_source_id_does_not_decide_verdict(self):
        src = inspect.getsource(prod)
        self.assertNotIn('source_id == "CAND-G100-010"', src)
        self.assertNotIn('source_id == "CAND-G100-019"', src)
        self.assertNotIn('source_id == "SUPP-G1-017"', src)
        self.assertNotIn('source_id == "CAND-G100-020"', src)
        self.assertNotIn('source_id == "CAND-G100-014"', src)

    def test_g0_duplicate_doi_with_relationship_is_not_unconditional_failure(self):
        records = [
            {"source_id": "A", "identifiers": {"doi": "10.1000/dup.1", "pmid": "1"}, "title": "Correction notice"},
            {"source_id": "B", "identifiers": {"doi": "10.1000/dup.1", "pmid": "2"}, "title": "Corrected article"},
            {"source_id": "C", "identifiers": {"doi": "10.1000/unique.1", "pmid": "3"}, "title": "Other"},
        ]
        relationships = [{
            "doi": "10.1000/dup.1",
            "relation": "correction",
            "members": ["A", "B"],
        }]
        res = prod.evaluate_manifest_integrity(records, research_relationships=relationships)
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(res["research_relationships"][0]["relation"], "correction")
        self.assertEqual(res["duplicate_doi_unconditional_anomalies"], [])

    def test_g0_duplicate_doi_without_relationship_holds(self):
        records = [
            {"source_id": "A", "identifiers": {"doi": "10.1000/dup.2", "pmid": "11"}, "title": "One"},
            {"source_id": "B", "identifiers": {"doi": "10.1000/dup.2", "pmid": "12"}, "title": "Two"},
        ]
        res = prod.evaluate_manifest_integrity(records, research_relationships=[])
        self.assertEqual(res["verdict"], "HOLD")
        self.assertTrue(any(r["rule_id"] == "G0_DUPLICATE_DOI_RELATIONSHIP_UNSTATED" for r in res["triggered_rules"]))

    def test_body_citation_of_full_title_is_not_confirmed(self):
        pdf = self._pdf("cite.pdf", [
            "Ocean Nutrient Transport\n"
            "doi: 10.2000/ocean.1\n"
            "Abstract: This paper studies kelp.\n"
            "Introduction: As reported in Long Term Dietary Intervention for Diabetes Remission in Adults, adults changed diet.\n"
        ])
        res = evaluate_pdf_identity_canonical(pdf, TARGET_TITLE, TARGET_DOI, "")
        self.assertEqual(res["identity_verdict"], "HOLD")
        self.assertNotEqual(res["identity_verdict"], "CONFIRMED")


if __name__ == "__main__":
    unittest.main()
