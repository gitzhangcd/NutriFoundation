#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_r1_replay.py - R1.2 规范核验器与负向控制自动化单元测试套件

【核心测试原则】
1. 生产与测试 100% 共享调用 evaluate_pdf_identity_canonical()，绝不在测试端另写简化逻辑。
2. 覆盖针对 RA-01 ~ RA-04 的 6 类核心负向与阳性基准用例 (NC-01 ~ NC-06)。
3. 覆盖分块流式哈希计算、损坏 PDF 异常处理与文本规范化。
"""

import unittest
import os
import sys
import tempfile
import hashlib
from pathlib import Path
import fitz  # PyMuPDF

# 确保能导入生产模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from tools.source_archive_verifier.r1_independent_replay_verifier import (
    evaluate_pdf_identity_canonical,
    calculate_sha256,
    normalize_text_canonical,
    normalize_title_canonical
)


class TestR1_2_CanonicalValidator(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()
