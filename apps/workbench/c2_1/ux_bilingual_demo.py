"""Self-authored, entirely SYNTHETIC bilingual reading UX exercise.

This is not part of the authorized NDS R1 source packet; no real-paper claims,
clinical decisions, Gold labels, AI candidate judgments or patient data.
Its content is generated internally rather than model-translated full text.
It is intentionally NOT eligible for SourceAnchor/PDF citation endpoints.
"""
from __future__ import annotations
from hashlib import sha256
import json

SECTIONS = [
 ("SECTION","A synthetic research reading exercise","一份虚构的科研阅读练习"),
 ("PARAGRAPH","All participants and measurements in this training document are fictional. This document tests bilingual reading, tables and source navigation; it is not a scientific study.","本文中的所有参与者及测量值均为虚构，仅用于测试双语阅读、表格和章节导航，不是真实科学研究。"),
 ("SECTION","Background","研究背景"),
 ("PARAGRAPH","A fictional research team compared two entirely synthetic education sessions. The purpose was to test whether readers can distinguish group descriptions from measured outcomes.","某虚构研究团队比较了两种完全合成的教育课程。本文旨在测试读者能否区分分组描述与观察结果。"),
 ("SECTION","Methods","研究方法"),
 ("PARAGRAPH","The simulated dataset includes 120 fictional records. Group A contains 60 records and Group B contains 60 records. No actual person was enrolled.","模拟数据集包含 120 条虚构记录。A 组有 60 条记录，B 组有 60 条记录。不存在真实受试者招募。"),
 ("TABLE","| Characteristic | Group A | Group B |\n|:---|---:|---:|\n| Records | 60 | 60 |\n| Baseline score | 25 | 25 |\n| Follow-up complete | 48 | 45 |",
          "| 特征 | A 组 | B 组 |\n|:---|---:|---:|\n| 记录数 | 60 | 60 |\n| 基线得分 | 25 | 25 |\n| 完成随访数 | 48 | 45 |"),
 ("PARAGRAPH","The primary endpoint was a fictional score at week 8. The exercise was not powered for clinical inference; the sample sizes are instructional values.","主要终点为第 8 周的一项虚构得分。本练习不用于临床推断；样本量仅为教学数值。"),
 ("SECTION","Results","研究结果"),
 ("TABLE","| Outcome | Group A | Group B |\n|:---|---:|---:|\n| Mean score, week 8 | 31 | 29 |\n| Missing records | 12 | 15 |",
          "| 结果 | A 组 | B 组 |\n|:---|---:|---:|\n| 第 8 周平均得分 | 31 | 29 |\n| 缺失记录数 | 12 | 15 |"),
 ("PARAGRAPH","The fictional mean scores were 31 and 29 at week 8. Because follow-up was incomplete, these numbers alone cannot establish a causal intervention effect.","第 8 周，两组虚构平均得分分别为 31 和 29。由于随访数据不完整，仅凭这些数字无法确定干预的因果作用。"),
 ("PARAGRAPH","This paragraph deliberately contains a long sentence so that the reader can practice selecting a shorter, unique source span when a PDF locator would otherwise fail.","该段落有意采用较长的句子，供用户练习在 PDF 定位失败时选择更短且唯一的原文范围。"),
 ("SECTION","Limitations","研究局限性"),
 ("PARAGRAPH","All records were invented; there is no randomization receipt, ethics protocol, or underlying patient record. Results must never be interpreted as clinical evidence.","全部记录均为编造数据；不存在真实随机化记录、伦理方案或患者原始资料。不得把结果解释为临床科学证据。"),
 ("SECTION","Conclusion","结论"),
 ("PARAGRAPH","A complete bilingual reading experience is possible with qualified structure, but scientific evidence still requires an independently verified original source.","具备合格结构的数据能够呈现完整的双语阅读体验，但科学证据仍必须依赖经过独立核实的原始来源。"),
]

def projection() -> dict:
    units=[{"unit_id":f"DEMO-{i:03d}","type":kind,"english":en,"chinese":zh}
           for i,(kind,en,zh) in enumerate(SECTIONS,1)]
    raw=json.dumps(units,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")
    return {"document_id":"SYNTHETIC-BILINGUAL-UX-ONLY",
            "version":"WB-v0.3-P1-UX-DEMO-001","content_sha256":sha256(raw).hexdigest(),
            "coverage":{"units":len(units),"bilingual_units":len(units),"ratio":1.0},
            "source_kind":"SELF_AUTHORED_SYNTHETIC_UX_DEMO",
            "source_anchor_eligible":False,"pdf_available":False,
            "scientific_capture":False,"units":units}
