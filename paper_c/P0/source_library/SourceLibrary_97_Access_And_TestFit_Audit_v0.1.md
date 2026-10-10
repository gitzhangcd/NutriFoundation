# G1-Shared｜排除无法访问三篇后的 97-source 测试目标审计

**审计日期**：2026-10-10。**权威来源**：既有 100-source 目录 + 100 PMID 的 PMC 版权筛查 + `First_100_Source_Pilot_Design_v0.1.md`。

> **研究判断：97 篇仍可用于来源目录、来源类型覆盖和小规模授权原文获取测试，但不能直接判定原定 100-source 或原始 G1 六类抽样规范已完成。**

## A. 用户实际无法访问的三篇

| 候选编号 | DOI / PMID | 原始目录中正确标题 | 原分层 | 原始 PMC 自动获取 |
|---|---|---|---|---|
| CAND-G100-008 | [10.7326/M22-1787](https://doi.org/10.7326/M22-1787) / [36508737](https://pubmed.ncbi.nlm.nih.gov/36508737/) | Effect of Calorie-Unrestricted Low-Carbohydrate, High-Fat Diet Versus High-Carbohydrate, Low-Fat Diet on Type 2 Diabetes and Nonalcoholic Fatty Liver Disease : A Randomized Controlled Trial. | Primary RCT | 未获支持 |
| CAND-G100-089 | [10.7326/ANNALS-25-00388](https://doi.org/10.7326/ANNALS-25-00388) / [40854218](https://pubmed.ncbi.nlm.nih.gov/40854218/) | Comparison of an Energy-Reduced Mediterranean Diet and Physical Activity Versus an Ad Libitum Mediterranean Diet in the Prevention of Type 2 Diabetes : A Secondary Analysis of a Randomized Controlled Trial. | StudyIdentity/companion | 未获支持 |
| CAND-G100-092 | [10.7326/M23-3132](https://doi.org/10.7326/M23-3132) / [38639542](https://pubmed.ncbi.nlm.nih.gov/38639542/) | Effect of Isocaloric, Time-Restricted Eating on Body Weight in Adults With Obesity : A Randomized Controlled Trial. | Potential conflict | 未获支持 |

**纠错**：089 是 *能量限制地中海饮食＋体力活动 vs 自由摄入地中海饮食* 的 T2D 预防次级分析，不是低脂饮食对照；092 是等热量限时进食对肥胖成人**体重**的影响，不是糖尿病血糖结局。保留 PubMed 原始题名，不沿用误记题名。

## B. 排除之后的来源统计

| 指标 | 结果 |
|---|---:|
| 剩余候选 PMID | **97** |
| 剩余 DOI | 96 |
| 有 PMCID | 58 |
| PMC 允许自动获取正文 | **51** |
| 不能通过现有 PMC 接口确认自动全文获取权限 | **46** |
| 真实原始 PDF / HTML / JATS 已归档 | **0 / 0 / 0** |
| 既有合法衍生 Markdown 正文 | 3 |
| 核心来源（Paper C 型分层） | **79** |
| 困难来源（Paper C 型分层） | **18** |

**统计口径**：`PMC allowed` 是可以调用 PMC 自动正文读取服务，不等于用户可下载出版社版 PDF，更不等于授权公共再发布或已归档。其余 46 篇为 PMC 通道不可确认，并不都已经验证“全球没有合法全文”。

### 11 类分层仍在，但精确配额不达标

| 现有分层 | 原 100-source 候选数 | 剩余篇数 | 其中 PMC 允许自动正文获取 |
|---|---:|---:|---:|
| Primary intervention (RCT等) | 28 | 27 | 17 |
| Primary observational (队列等) | 18 | 18 | 11 |
| Evidence synthesis (SR/Meta等) | 18 | 18 | 11 |
| Guideline / consensus (核心分层) | 12 | 12 | 3 |
| Companion / secondary (核心分层) | 4 | 4 | 2 |
| Correction / version updates | 6 | 6 | 2 |
| StudyIdentity / companion stress | 4 | 3 | 2 |
| Potential evidence conflict | 4 | 3 | 1 |
| Normative exception boundary | 2 | 2 | 1 |
| Temporal cutoff sensitivity | 2 | 2 | 1 |
| Incomplete or missing source | 2 | 2 | 0 |

被剔除后缺少：1 篇 primary_interventional、1 篇 study_identity_or_companion_dependency、1 篇 conflicting_evidence（**真正科学冲突仍需相同 PICO、时间及 estimand 判定**）。

## C. 科学测试目标判断

| 测试目标 | 97 篇可行性 | 说明 |
|---|---|---|
| 真实 PubMed 来源和 provenance 目录 | GO | 97 条有实际 PMID，保留原有 DOI/PMCID/名称 |
| 原始资料目录与保存契约 | GO | 可维护 97 条，并独立追踪 PDF、HTML、Markdown 文件状态 |
| 异质来源代表性 5-source 获取试点 | CONDITIONAL GO | 有足够的 RCT、队列、证据综合、指南和共识候选；优先从 51 条 PMC 支持读取的来源中选 |
| StudyIdentity/版本/更正困难来源存在性 | GO at catalogue | 11 类均有记录；具体试验/队列归并尚未完成 |
| 97 篇都形成合法可核验原始 PDF / HTML | NO-GO | 原始归档 0，且 46 条 PMC 自动获取权尚未确认 |
| 精确 80+20/11-分层的 100 个来源 | NO-GO | 97/100；三类各缺一 |
| 原始 G1 First100 六类来源设计 | NO-GO | 这批来源本来按 Paper C 型 80+20 分层，不按 G1 六类来源配额构造 |
| 500 EvidenceUnit / 300 ScientificClaim | NOT STARTED | 原始 G1 文件是期望产出，不是目录数乘法可以证明的已完成结果 |
| 确认性 Gold100 | NOT APPLICABLE | 目前 97 个源均已作为研究候选暴露，不能直接当作隐藏测试集 |

**原始 G1 First 100 目标**：指南 20、共识 10、Meta 25、系统综述 10、RCT 25、队列 10。当前 97 的 11 类分层无法被视为这一目标的已验证对应关系，若严格执行须重新按六类分类与配额抽样。

## D. 三篇同类替换候选：均已实际验证 PMC 正文可读取

| 替代原编号 | PMID / PMCID | 可用真实替代文献 | 角色与重要限制 |
|---|---|---|---|
| CAND-G100-008 | [34993571](https://pubmed.ncbi.nlm.nih.gov/34993571/) / [PMC8739348](https://pmc.ncbi.nlm.nih.gov/articles/PMC8739348/) | Dietary carbohydrate restriction augments weight loss-induced improvements in glycaemic control and liver fat in individuals with type 2 diabetes: a randomised controlled trial. | primary_interventional。Unlike calorie-unrestricted original, diet conditions use energy restriction; don't relabel as an equivalent clinical effect |
| CAND-G100-089 | [39723807](https://pubmed.ncbi.nlm.nih.gov/39723807/) / [PMC11771574](https://pmc.ncbi.nlm.nih.gov/articles/PMC11771574/) | Effect of an intensive lifestyle intervention on cystatin C-based kidney function in adults with overweight and obesity: From the PREDIMED-Plus trial. | study_identity_or_companion_dependency。Renal function not incident type 2 diabetes; valuable for study-family/companion dependency tests, not interchangeable outcomes |
| CAND-G100-092 | [36930148](https://pubmed.ncbi.nlm.nih.gov/36930148/) / [PMC10024204](https://pmc.ncbi.nlm.nih.gov/articles/PMC10024204/) | Effects of Time-Restricted Eating on Nonalcoholic Fatty Liver Disease: The TREATY-FLD Randomized Clinical Trial. | conflicting_evidence。Primary endpoint intrahepatic triglycerides in NAFLD and not isocaloric weight-loss obesity trial; cannot label as matched scientific conflict until PICO/estimand verified |

**三篇的 PMC 正文入口已分别实际调用验证可以读取，但没有下载并归档原始 PDF/HTML，也没有把它们写入权威 100-source Manifest；是否替代以源分层与研究问题匹配审核为准。**

## E. 剩余 97 篇逐条可用性清单

| 来源 ID | 初拟来源类型 | PubMed 原始题名 | PMID | PMC | PMC 正文获取 | Markdown |
|---|---|---|---|---|---|---|
| CAND-G100-001 | primary_interventional | [Time-Restricted Eating in Adults With Metabolic Syndrome : A Randomized Controlled Trial.](https://pubmed.ncbi.nlm.nih.gov/39348690/) | 39348690 | [PMC11929607](https://pmc.ncbi.nlm.nih.gov/articles/PMC11929607/) | 允许 | 未存 |
| CAND-G100-002 | primary_interventional | [Effects of Time-Restricted Eating on Weight Loss and Other Metabolic Parameters in Women and Men With Overweight and Obesity: The TREAT Randomized Clinical Trial.](https://pubmed.ncbi.nlm.nih.gov/32986097/) | 32986097 | [PMC7522780](https://pmc.ncbi.nlm.nih.gov/articles/PMC7522780/) | 其他渠道待核 | 未存 |
| CAND-G100-003 | primary_interventional | [Time-restricted eating with or without low-carbohydrate diet reduces visceral fat and improves metabolic syndrome: A randomized trial.](https://pubmed.ncbi.nlm.nih.gov/36220069/) | 36220069 | [PMC9589024](https://pmc.ncbi.nlm.nih.gov/articles/PMC9589024/) | 允许 | 未存 |
| CAND-G100-004 | primary_interventional | [Randomized controlled trial for time-restricted eating in healthy volunteers without obesity.](https://pubmed.ncbi.nlm.nih.gov/35194047/) | 35194047 | [PMC8864028](https://pmc.ncbi.nlm.nih.gov/articles/PMC8864028/) | 允许 | 衍生正文已存 |
| CAND-G100-005 | primary_interventional | [Effect of Time-Restricted Eating on Weight Loss in Adults With Type 2 Diabetes: A Randomized Clinical Trial.](https://pubmed.ncbi.nlm.nih.gov/37889487/) | 37889487 | [PMC10611992](https://pmc.ncbi.nlm.nih.gov/articles/PMC10611992/) | 允许 | 未存 |
| CAND-G100-006 | primary_interventional | [Effects of DASH diet with or without time-restricted eating in the management of stage 1 primary hypertension: a randomized controlled trial.](https://pubmed.ncbi.nlm.nih.gov/38886740/) | 38886740 | [PMC11181626](https://pmc.ncbi.nlm.nih.gov/articles/PMC11181626/) | 允许 | 未存 |
| CAND-G100-007 | primary_interventional | [Long-term secondary prevention of cardiovascular disease with a Mediterranean diet and a low-fat diet (CORDIOPREV): a randomised controlled trial.](https://pubmed.ncbi.nlm.nih.gov/35525255/) | 35525255 | — | 其他渠道待核 | 未存 |
| CAND-G100-009 | primary_interventional | [Effects of a low-carbohydrate diet on insulin-resistant dyslipoproteinemia-a randomized controlled feeding trial.](https://pubmed.ncbi.nlm.nih.gov/34582545/) | 34582545 | [PMC8755039](https://pmc.ncbi.nlm.nih.gov/articles/PMC8755039/) | 允许 | 未存 |
| CAND-G100-010 | primary_interventional | [Effects of a Low-Carbohydrate Dietary Intervention on Hemoglobin A1c: A Randomized Clinical Trial.](https://pubmed.ncbi.nlm.nih.gov/36287562/) | 36287562 | [PMC9606840](https://pmc.ncbi.nlm.nih.gov/articles/PMC9606840/) | 允许 | 未存 |
| CAND-G100-011 | primary_interventional | [Low-carbohydrate vegan diets in diabetes for weight loss and sustainability: a randomized controlled trial.](https://pubmed.ncbi.nlm.nih.gov/36156115/) | 36156115 | — | 其他渠道待核 | 未存 |
| CAND-G100-012 | primary_interventional | [The effect of dietary approaches to stop hypertension (DASH) diet on fatty liver and cardiovascular risk factors in subjects with metabolic syndrome: a randomized controlled trial.](https://pubmed.ncbi.nlm.nih.gov/39054440/) | 39054440 | [PMC11270781](https://pmc.ncbi.nlm.nih.gov/articles/PMC11270781/) | 允许 | 未存 |
| CAND-G100-013 | primary_interventional | [DASH vs. Mediterranean diet on a salt restriction background in adults with high normal blood pressure or grade 1 hypertension: A randomized controlled trial.](https://pubmed.ncbi.nlm.nih.gov/37625311/) | 37625311 | — | 其他渠道待核 | 未存 |
| CAND-G100-014 | primary_interventional | [Development of a Health Behavioral Digital Intervention for Patients With Hypertension Based on an Intelligent Health Promotion System and WeChat: Randomized Controlled Trial.](https://pubmed.ncbi.nlm.nih.gov/38578692/) | 38578692 | [PMC11031705](https://pmc.ncbi.nlm.nih.gov/articles/PMC11031705/) | 允许 | 未存 |
| CAND-G100-015 | primary_interventional | [Effect of a ketogenic diet versus Mediterranean diet on glycated hemoglobin in individuals with prediabetes and type 2 diabetes mellitus: The interventional Keto-Med randomized crossover trial.](https://pubmed.ncbi.nlm.nih.gov/35641199/) | 35641199 | [PMC9437985](https://pmc.ncbi.nlm.nih.gov/articles/PMC9437985/) | 允许 | 未存 |
| CAND-G100-016 | primary_interventional | [A Randomized Trial Comparing the Specific Carbohydrate Diet to a Mediterranean Diet in Adults With Crohn's Disease.](https://pubmed.ncbi.nlm.nih.gov/34052278/) | 34052278 | [PMC8396394](https://pmc.ncbi.nlm.nih.gov/articles/PMC8396394/) | 允许 | 未存 |
| CAND-G100-017 | primary_interventional | [Mediterranean Diet and Patients With Psoriasis: The MEDIPSO Randomized Clinical Trial.](https://pubmed.ncbi.nlm.nih.gov/40991259/) | 40991259 | [PMC12461594](https://pmc.ncbi.nlm.nih.gov/articles/PMC12461594/) | 其他渠道待核 | 未存 |
| CAND-G100-018 | primary_interventional | [Effect of green-Mediterranean diet on intrahepatic fat: the DIRECT PLUS randomised controlled trial.](https://pubmed.ncbi.nlm.nih.gov/33461965/) | 33461965 | [PMC8515100](https://pmc.ncbi.nlm.nih.gov/articles/PMC8515100/) | 允许 | 未存 |
| CAND-G100-019 | primary_interventional | [An AI-Powered Lifestyle Intervention vs Human Coaching in the Diabetes Prevention Program: A Randomized Clinical Trial.](https://pubmed.ncbi.nlm.nih.gov/41144242/) | 41144242 | [PMC12560030](https://pmc.ncbi.nlm.nih.gov/articles/PMC12560030/) | 其他渠道待核 | 未存 |
| CAND-G100-020 | primary_interventional | [Different Effects of Lifestyle Intervention in High- and Low-Risk Prediabetes: Results of the Randomized Controlled Prediabetes Lifestyle Intervention Study (PLIS).](https://pubmed.ncbi.nlm.nih.gov/34531293/) | 34531293 | — | 其他渠道待核 | 未存 |
| CAND-G100-021 | primary_interventional | [Effects of personalized diets by prediction of glycemic responses on glycemic control and metabolic health in newly diagnosed T2DM: a randomized dietary intervention pilot trial.](https://pubmed.ncbi.nlm.nih.gov/35135549/) | 35135549 | [PMC8826661](https://pmc.ncbi.nlm.nih.gov/articles/PMC8826661/) | 允许 | 未存 |
| CAND-G100-022 | primary_interventional | [The effect of daily protein supplementation, with or without resistance training for 1 year, on muscle size, strength, and function in healthy older adults: A randomized controlled trial.](https://pubmed.ncbi.nlm.nih.gov/33564844/) | 33564844 | — | 其他渠道待核 | 未存 |
| CAND-G100-023 | primary_interventional | [De-Training Effects Following Leucine-Enriched Whey Protein Supplementation and Resistance Training in Older Adults with Sarcopenia: A Randomized Controlled Trial with 24 Weeks of Follow-Up.](https://pubmed.ncbi.nlm.nih.gov/36437767/) | 36437767 | — | 其他渠道待核 | 未存 |
| CAND-G100-024 | primary_interventional | [The effects of whey, pea, and collagen protein supplementation beyond the recommended dietary allowance on integrated myofibrillar protein synthetic rates in older males: a randomized controlled trial.](https://pubmed.ncbi.nlm.nih.gov/38762187/) | 38762187 | [PMC11291473](https://pmc.ncbi.nlm.nih.gov/articles/PMC11291473/) | 允许 | 未存 |
| CAND-G100-025 | primary_interventional | [Effects of an Exercise and Nutritional Intervention on Circulating Biomarkers and Metabolomic Profiling During Adjuvant Treatment for Localized Breast Cancer: Results From the PASAPAS Feasibility Randomized Controlled Trial.](https://pubmed.ncbi.nlm.nih.gov/33655799/) | 33655799 | [PMC7934026](https://pmc.ncbi.nlm.nih.gov/articles/PMC7934026/) | 允许 | 未存 |
| CAND-G100-026 | primary_interventional | [Effect of Early Peripheral Parenteral Nutrition Support in an Enhanced Recovery Program for Colorectal Cancer Surgery: A Randomized Open Trial.](https://pubmed.ncbi.nlm.nih.gov/34441942/) | 34441942 | [PMC8396922](https://pmc.ncbi.nlm.nih.gov/articles/PMC8396922/) | 允许 | 未存 |
| CAND-G100-027 | primary_interventional | [A population health dietary intervention for African American adults with chronic kidney disease: The Fruit and Veggies for Kidney Health randomized study.](https://pubmed.ncbi.nlm.nih.gov/32090186/) | 32090186 | [PMC7026290](https://pmc.ncbi.nlm.nih.gov/articles/PMC7026290/) | 允许 | 未存 |
| CAND-G100-028 | primary_interventional | [Effect of essential amino acid кetoanalogues and protein restriction diet on morphogenetic proteins (FGF-23 and Кlotho) in 3b-4 stages chronic кidney disease patients: a randomized pilot study.](https://pubmed.ncbi.nlm.nih.gov/29948444/) | 29948444 | — | 其他渠道待核 | 未存 |
| CAND-G100-029 | primary_observational | [Ultra-processed food intake and risk of cardiovascular disease: prospective cohort study (NutriNet-Santé).](https://pubmed.ncbi.nlm.nih.gov/31142457/) | 31142457 | [PMC6538975](https://pmc.ncbi.nlm.nih.gov/articles/PMC6538975/) | 允许 | 未存 |
| CAND-G100-030 | primary_observational | [Ultra-Processed Food Consumption and Risk of Type 2 Diabetes: Three Large Prospective U.S. Cohort Studies.](https://pubmed.ncbi.nlm.nih.gov/36854188/) | 36854188 | [PMC10300524](https://pmc.ncbi.nlm.nih.gov/articles/PMC10300524/) | 其他渠道待核 | 未存 |
| CAND-G100-031 | primary_observational | [Consumption of ultra-processed foods and cancer risk: results from NutriNet-Santé prospective cohort.](https://pubmed.ncbi.nlm.nih.gov/29444771/) | 29444771 | [PMC5811844](https://pmc.ncbi.nlm.nih.gov/articles/PMC5811844/) | 允许 | 未存 |
| CAND-G100-032 | primary_observational | [Ultra-processed food consumption and type 2 diabetes incidence: A prospective cohort study.](https://pubmed.ncbi.nlm.nih.gov/33388205/) | 33388205 | — | 其他渠道待核 | 未存 |
| CAND-G100-033 | primary_observational | [Ultra-processed food consumption and risk of obesity: a prospective cohort study of UK Biobank.](https://pubmed.ncbi.nlm.nih.gov/33070213/) | 33070213 | [PMC8137628](https://pmc.ncbi.nlm.nih.gov/articles/PMC8137628/) | 允许 | 未存 |
| CAND-G100-034 | primary_observational | [Dietary protein intake in midlife in relation to healthy aging - results from the prospective Nurses' Health Study cohort.](https://pubmed.ncbi.nlm.nih.gov/38309825/) | 38309825 | [PMC10884611](https://pmc.ncbi.nlm.nih.gov/articles/PMC10884611/) | 允许 | 未存 |
| CAND-G100-035 | primary_observational | [Dietary protein intake and body composition, sarcopenia and sarcopenic obesity: A prospective population-based study.](https://pubmed.ncbi.nlm.nih.gov/40845421/) | 40845421 | — | 其他渠道待核 | 未存 |
| CAND-G100-036 | primary_observational | [Protein Intake and Risk of Falls: A Prospective Analysis in Older Adults.](https://pubmed.ncbi.nlm.nih.gov/30517767/) | 30517767 | — | 其他渠道待核 | 未存 |
| CAND-G100-037 | primary_observational | [Use of Insoluble Dietary Fiber and Probiotics for Bowel Preparation Before Colonoscopy: A Prospective Study.](https://pubmed.ncbi.nlm.nih.gov/35202009/) | 35202009 | [PMC8969843](https://pmc.ncbi.nlm.nih.gov/articles/PMC8969843/) | 允许 | 未存 |
| CAND-G100-038 | primary_observational | [Dietary fiber intake and mortality among survivors of liver cirrhosis: A prospective cohort study.](https://pubmed.ncbi.nlm.nih.gov/37251456/) | 37251456 | [PMC10220317](https://pmc.ncbi.nlm.nih.gov/articles/PMC10220317/) | 允许 | 未存 |
| CAND-G100-039 | primary_observational | [Maternal Dietary Fiber Intake During Lactation and Human Milk Oligosaccharide Fucosylation: a PRIMA Birth Cohort Study.](https://pubmed.ncbi.nlm.nih.gov/40583481/) | 40583481 | [PMC12538538](https://pmc.ncbi.nlm.nih.gov/articles/PMC12538538/) | 允许 | 未存 |
| CAND-G100-040 | primary_observational | [Sodium intake and urinary losses in children on dialysis: a European multicenter prospective study.](https://pubmed.ncbi.nlm.nih.gov/36988689/) | 36988689 | — | 其他渠道待核 | 未存 |
| CAND-G100-041 | primary_observational | [Multiple measurements of the urinary sodium-to-potassium ratio strongly related home hypertension: TMM Cohort Study.](https://pubmed.ncbi.nlm.nih.gov/31562419/) | 31562419 | [PMC8076007](https://pmc.ncbi.nlm.nih.gov/articles/PMC8076007/) | 允许 | 未存 |
| CAND-G100-042 | primary_observational | [Healthy dietary patterns, genetic risk, and gastrointestinal cancer incident risk: a large-scale prospective cohort study.](https://pubmed.ncbi.nlm.nih.gov/38042409/) | 38042409 | — | 其他渠道待核 | 未存 |
| CAND-G100-043 | primary_observational | [Plant-based dietary patterns and age-specific risk of multimorbidity of cancer and cardiometabolic diseases: a prospective analysis.](https://pubmed.ncbi.nlm.nih.gov/40845891/) | 40845891 | [PMC12408430](https://pmc.ncbi.nlm.nih.gov/articles/PMC12408430/) | 允许 | 未存 |
| CAND-G100-044 | primary_observational | [Inflammatory Dietary Patterns and Risk of Keratinocyte Cancers in Kidney Transplant Recipients: Prospective Cohort Study.](https://pubmed.ncbi.nlm.nih.gov/32966976/) | 32966976 | — | 其他渠道待核 | 未存 |
| CAND-G100-045 | primary_observational | [Mediterranean diet and associated metabolite signatures in relation to MASLD progression: A prospective cohort study.](https://pubmed.ncbi.nlm.nih.gov/40879470/) | 40879470 | [PMC12401285](https://pmc.ncbi.nlm.nih.gov/articles/PMC12401285/) | 允许 | 未存 |
| CAND-G100-046 | primary_observational | [Mediterranean Diet versus Very Low-Calorie Ketogenic Diet: Effects of Reaching 5% Body Weight Loss on Body Composition in Subjects with Overweight and with Obesity-A Cohort Study.](https://pubmed.ncbi.nlm.nih.gov/36293616/) | 36293616 | [PMC9603454](https://pmc.ncbi.nlm.nih.gov/articles/PMC9603454/) | 允许 | 未存 |
| CAND-G100-047 | evidence_synthesis | [Intermittent fasting and weight loss: Systematic review.](https://pubmed.ncbi.nlm.nih.gov/32060194/) | 32060194 | [PMC7021351](https://pmc.ncbi.nlm.nih.gov/articles/PMC7021351/) | 其他渠道待核 | 未存 |
| CAND-G100-048 | evidence_synthesis | [Intermittent fasting strategies and their effects on body weight and other cardiometabolic risk factors: systematic review and network meta-analysis of randomised clinical trials.](https://pubmed.ncbi.nlm.nih.gov/40533200/) | 40533200 | [PMC12175170](https://pmc.ncbi.nlm.nih.gov/articles/PMC12175170/) | 允许 | 未存 |
| CAND-G100-049 | evidence_synthesis | [Intermittent Fasting: Does It Affect Sports Performance? A Systematic Review.](https://pubmed.ncbi.nlm.nih.gov/38201996/) | 38201996 | [PMC10780856](https://pmc.ncbi.nlm.nih.gov/articles/PMC10780856/) | 允许 | 未存 |
| CAND-G100-050 | evidence_synthesis | [The effects of intermittent fasting on body composition and cardiometabolic health in adults with prediabetes or type 2 diabetes: A systematic review and meta-analysis.](https://pubmed.ncbi.nlm.nih.gov/38956175/) | 38956175 | — | 其他渠道待核 | 未存 |
| CAND-G100-051 | evidence_synthesis | [Dietary Approaches to Stop Hypertension (DASH) Diet and Blood Pressure Reduction in Adults with and without Hypertension: A Systematic Review and Meta-Analysis of Randomized Controlled Trials.](https://pubmed.ncbi.nlm.nih.gov/32330233/) | 32330233 | [PMC7490167](https://pmc.ncbi.nlm.nih.gov/articles/PMC7490167/) | 其他渠道待核 | 未存 |
| CAND-G100-052 | evidence_synthesis | [Adherence to the DASH Diet and Risk of Hypertension: A Systematic Review and Meta-Analysis.](https://pubmed.ncbi.nlm.nih.gov/37513679/) | 37513679 | [PMC10383418](https://pmc.ncbi.nlm.nih.gov/articles/PMC10383418/) | 允许 | 未存 |
| CAND-G100-053 | evidence_synthesis | [Mediterranean diet and female reproductive health over lifespan: a systematic review and meta-analysis.](https://pubmed.ncbi.nlm.nih.gov/37506751/) | 37506751 | — | 其他渠道待核 | 未存 |
| CAND-G100-054 | evidence_synthesis | [Effect of low glycaemic index or load dietary patterns on glycaemic control and cardiometabolic risk factors in diabetes: systematic review and meta-analysis of randomised controlled trials.](https://pubmed.ncbi.nlm.nih.gov/34348965/) | 34348965 | [PMC8336013](https://pmc.ncbi.nlm.nih.gov/articles/PMC8336013/) | 允许 | 未存 |
| CAND-G100-055 | evidence_synthesis | [Efficacy and safety of low and very low carbohydrate diets for type 2 diabetes remission: systematic review and meta-analysis of published and unpublished randomized trial data.](https://pubmed.ncbi.nlm.nih.gov/33441384/) | 33441384 | [PMC7804828](https://pmc.ncbi.nlm.nih.gov/articles/PMC7804828/) | 允许 | 未存 |
| CAND-G100-056 | evidence_synthesis | [Can Dietary Patterns Impact Fertility Outcomes? A Systematic Review and Meta-Analysis.](https://pubmed.ncbi.nlm.nih.gov/37299551/) | 37299551 | [PMC10255613](https://pmc.ncbi.nlm.nih.gov/articles/PMC10255613/) | 允许 | 未存 |
| CAND-G100-057 | evidence_synthesis | [The Role of Diet in Prognosis among Cancer Survivors: A Systematic Review and Meta-Analysis of Dietary Patterns and Diet Interventions.](https://pubmed.ncbi.nlm.nih.gov/35057525/) | 35057525 | [PMC8779048](https://pmc.ncbi.nlm.nih.gov/articles/PMC8779048/) | 允许 | 未存 |
| CAND-G100-058 | evidence_synthesis | [Systematic review and meta-analysis of protein intake to support muscle mass and function in healthy adults.](https://pubmed.ncbi.nlm.nih.gov/35187864/) | 35187864 | [PMC8978023](https://pmc.ncbi.nlm.nih.gov/articles/PMC8978023/) | 允许 | 未存 |
| CAND-G100-059 | evidence_synthesis | [Exercise for sarcopenia in older people: A systematic review and network meta-analysis.](https://pubmed.ncbi.nlm.nih.gov/37057640/) | 37057640 | [PMC10235889](https://pmc.ncbi.nlm.nih.gov/articles/PMC10235889/) | 允许 | 未存 |
| CAND-G100-060 | evidence_synthesis | [Effect of Plant Versus Animal Protein on Muscle Mass, Strength, Physical Performance, and Sarcopenia: A Systematic Review and Meta-analysis of Randomized Controlled Trials.](https://pubmed.ncbi.nlm.nih.gov/39813010/) | 39813010 | [PMC12166177](https://pmc.ncbi.nlm.nih.gov/articles/PMC12166177/) | 允许 | 未存 |
| CAND-G100-061 | evidence_synthesis | [Association of food groups and dietary pattern with breast cancer risk: A systematic review and meta-analysis.](https://pubmed.ncbi.nlm.nih.gov/36731160/) | 36731160 | — | 其他渠道待核 | 未存 |
| CAND-G100-062 | evidence_synthesis | [The effect of timing of enteral nutrition support on feeding outcomes and dysphagia in patients with head and neck cancer undergoing radiotherapy or chemoradiotherapy: A systematic review.](https://pubmed.ncbi.nlm.nih.gov/34330518/) | 34330518 | — | 其他渠道待核 | 未存 |
| CAND-G100-063 | evidence_synthesis | [Conversion of Urine Protein-Creatinine Ratio or Urine Dipstick Protein to Urine Albumin-Creatinine Ratio for Use in Chronic Kidney Disease Screening and Prognosis : An Individual Participant-Based Meta-analysis.](https://pubmed.ncbi.nlm.nih.gov/32658569/) | 32658569 | [PMC7780415](https://pmc.ncbi.nlm.nih.gov/articles/PMC7780415/) | 允许 | 未存 |
| CAND-G100-064 | evidence_synthesis | [Efficacy and safety of ketoanalogue supplementation combined with protein-restricted diets in advanced chronic kidney disease: a systematic review and meta-analysis.](https://pubmed.ncbi.nlm.nih.gov/39340710/) | 39340710 | — | 其他渠道待核 | 未存 |
| CAND-G100-065 | guideline_or_consensus | [ESPEN practical guideline: Clinical Nutrition in cancer.](https://pubmed.ncbi.nlm.nih.gov/33946039/) | 33946039 | — | 其他渠道待核 | 未存 |
| CAND-G100-066 | guideline_or_consensus | [ESPEN practical and partially revised guideline: Clinical nutrition in the intensive care unit.](https://pubmed.ncbi.nlm.nih.gov/37517372/) | 37517372 | — | 其他渠道待核 | 未存 |
| CAND-G100-067 | guideline_or_consensus | [ESPEN guideline on clinical nutrition in surgery - Update 2025.](https://pubmed.ncbi.nlm.nih.gov/40957230/) | 40957230 | — | 其他渠道待核 | 未存 |
| CAND-G100-068 | guideline_or_consensus | [ESPEN practical guideline on clinical nutrition in acute and chronic pancreatitis.](https://pubmed.ncbi.nlm.nih.gov/38169174/) | 38169174 | — | 其他渠道待核 | 未存 |
| CAND-G100-069 | guideline_or_consensus | [ESPEN guideline on hospital nutrition.](https://pubmed.ncbi.nlm.nih.gov/34742138/) | 34742138 | — | 其他渠道待核 | 未存 |
| CAND-G100-070 | guideline_or_consensus | [ESPEN micronutrient guideline.](https://pubmed.ncbi.nlm.nih.gov/35365361/) | 35365361 | — | 其他渠道待核 | 未存 |
| CAND-G100-071 | guideline_or_consensus | [Medical Nutrition Therapy Interventions Provided by Dietitians for Adult Overweight and Obesity Management: An Academy of Nutrition and Dietetics Evidence-Based Practice Guideline.](https://pubmed.ncbi.nlm.nih.gov/36462613/) | 36462613 | [PMC12646719](https://pmc.ncbi.nlm.nih.gov/articles/PMC12646719/) | 允许 | 未存 |
| CAND-G100-072 | guideline_or_consensus | [ESPEN practical guideline on ethical aspects of medical nutrition therapy.](https://pubmed.ncbi.nlm.nih.gov/41895152/) | 41895152 | — | 其他渠道待核 | 未存 |
| CAND-G100-073 | guideline_or_consensus | [ESPEN guideline on clinical nutrition in hospitalized patients with acute or chronic kidney disease.](https://pubmed.ncbi.nlm.nih.gov/33640205/) | 33640205 | — | 其他渠道待核 | 未存 |
| CAND-G100-074 | guideline_or_consensus | [ESPEN practical guideline on clinical nutrition in hospitalized patients with acute or chronic kidney disease.](https://pubmed.ncbi.nlm.nih.gov/39178492/) | 39178492 | — | 其他渠道待核 | 未存 |
| CAND-G100-075 | guideline_or_consensus | [Hyperglycaemic crises in adults with diabetes: a consensus report.](https://pubmed.ncbi.nlm.nih.gov/38907161/) | 38907161 | [PMC11343900](https://pmc.ncbi.nlm.nih.gov/articles/PMC11343900/) | 允许 | 衍生正文已存 |
| CAND-G100-076 | guideline_or_consensus | [Exercise/Physical Activity in Individuals with Type 2 Diabetes: A Consensus Statement from the American College of Sports Medicine.](https://pubmed.ncbi.nlm.nih.gov/35029593/) | 35029593 | [PMC8802999](https://pmc.ncbi.nlm.nih.gov/articles/PMC8802999/) | 允许 | 未存 |
| CAND-G100-077 | companion_or_secondary | [Safety of High-Dose Vitamin D Supplementation: Secondary Analysis of a Randomized Controlled Trial.](https://pubmed.ncbi.nlm.nih.gov/31746327/) | 31746327 | — | 其他渠道待核 | 未存 |
| CAND-G100-078 | companion_or_secondary | [Time-Restricted Eating and Sleep, Mood, and Quality of Life in Adults With Overweight or Obesity: A Secondary Analysis of a Randomized Clinical Trial.](https://pubmed.ncbi.nlm.nih.gov/40560588/) | 40560588 | [PMC12199060](https://pmc.ncbi.nlm.nih.gov/articles/PMC12199060/) | 允许 | 未存 |
| CAND-G100-079 | companion_or_secondary | [5-year follow-up of the randomised Diabetes Remission Clinical Trial (DiRECT) of continued support for weight loss maintenance in the UK: an extension study.](https://pubmed.ncbi.nlm.nih.gov/38423026/) | 38423026 | — | 其他渠道待核 | 未存 |
| CAND-G100-080 | companion_or_secondary | [Effects of 4:3 Intermittent Fasting on Eating Behaviors and Appetite Hormones: A Secondary Analysis of a 12-Month Behavioral Weight Loss Intervention.](https://pubmed.ncbi.nlm.nih.gov/40733010/) | 40733010 | [PMC12298406](https://pmc.ncbi.nlm.nih.gov/articles/PMC12298406/) | 允许 | 未存 |
| CAND-G100-081 | correction_republication_retraction_or_living_version | [Author Correction: Fasting mimicking diet cycles versus a Mediterranean diet and cardiometabolic risk in overweight and obese hypertensive subjects: a randomized clinical trial.](https://pubmed.ncbi.nlm.nih.gov/40987812/) | 40987812 | [PMC12457591](https://pmc.ncbi.nlm.nih.gov/articles/PMC12457591/) | 允许 | 衍生正文已存 |
| CAND-G100-082 | correction_republication_retraction_or_living_version | [Correction to: PKU dietary handbook to accompany PKU guidelines.](https://pubmed.ncbi.nlm.nih.gov/32873338/) | 32873338 | [PMC7465324](https://pmc.ncbi.nlm.nih.gov/articles/PMC7465324/) | 允许 | 未存 |
| CAND-G100-083 | correction_republication_retraction_or_living_version | [Correction to: Cardiovascular-Kidney-Metabolic Health: A Presidential Advisory From the American Heart Association.](https://pubmed.ncbi.nlm.nih.gov/38527138/) | 38527138 | — | 其他渠道待核 | 未存 |
| CAND-G100-084 | correction_republication_retraction_or_living_version | [Management of paediatric ulcerative colitis, part 2: Acute severe colitis-An updated evidence-based consensus guideline from the European Society of Paediatric Gastroenterology, Hepatology and Nutrition and the European Crohn's and Colitis Organization.](https://pubmed.ncbi.nlm.nih.gov/40528309/) | 40528309 | — | 其他渠道待核 | 未存 |
| CAND-G100-085 | correction_republication_retraction_or_living_version | [ESPEN guideline on chronic intestinal failure in adults - Update 2023.](https://pubmed.ncbi.nlm.nih.gov/37639741/) | 37639741 | — | 其他渠道待核 | 未存 |
| CAND-G100-086 | correction_republication_retraction_or_living_version | [The Medical Management of Paediatric Crohn's Disease: an ECCO-ESPGHAN Guideline Update.](https://pubmed.ncbi.nlm.nih.gov/33026087/) | 33026087 | — | 其他渠道待核 | 未存 |
| CAND-G100-087 | study_identity_or_companion_dependency | [Mediterranean diet as a strategy for preserving kidney function in patients with coronary heart disease with type 2 diabetes and obesity: a secondary analysis of CORDIOPREV randomized controlled trial.](https://pubmed.ncbi.nlm.nih.gov/38755195/) | 38755195 | [PMC11099022](https://pmc.ncbi.nlm.nih.gov/articles/PMC11099022/) | 允许 | 未存 |
| CAND-G100-088 | study_identity_or_companion_dependency | [Mediterranean Diet, Physical Activity, and Bone Health in Older Adults: A Secondary Analysis of a Randomized Clinical Trial.](https://pubmed.ncbi.nlm.nih.gov/40198072/) | 40198072 | [PMC11979728](https://pmc.ncbi.nlm.nih.gov/articles/PMC11979728/) | 允许 | 未存 |
| CAND-G100-090 | study_identity_or_companion_dependency | [Effects of time-restricted eating and low-carbohydrate diet on psychosocial health and appetite in individuals with metabolic syndrome: A secondary analysis of a randomized controlled trial.](https://pubmed.ncbi.nlm.nih.gov/39226719/) | 39226719 | — | 其他渠道待核 | 未存 |
| CAND-G100-091 | conflicting_evidence | [Calorie Restriction with or without Time-Restricted Eating in Weight Loss.](https://pubmed.ncbi.nlm.nih.gov/35443107/) | 35443107 | — | 其他渠道待核 | 未存 |
| CAND-G100-093 | conflicting_evidence | [Intermittent fasting plus early time-restricted eating versus calorie restriction and standard care in adults at risk of type 2 diabetes: a randomized controlled trial.](https://pubmed.ncbi.nlm.nih.gov/37024596/) | 37024596 | — | 其他渠道待核 | 未存 |
| CAND-G100-094 | conflicting_evidence | [A 5:2 Intermittent Fasting Meal Replacement Diet and Glycemic Control for Adults With Diabetes: The EARLY Randomized Clinical Trial.](https://pubmed.ncbi.nlm.nih.gov/38904963/) | 38904963 | [PMC11193124](https://pmc.ncbi.nlm.nih.gov/articles/PMC11193124/) | 允许 | 未存 |
| CAND-G100-095 | recommendation_exception_or_normative_boundary | [Definition and Diagnostic Criteria for Sarcopenic Obesity: ESPEN and EASO Consensus Statement.](https://pubmed.ncbi.nlm.nih.gov/35196654/) | 35196654 | [PMC9210010](https://pmc.ncbi.nlm.nih.gov/articles/PMC9210010/) | 其他渠道待核 | 未存 |
| CAND-G100-096 | recommendation_exception_or_normative_boundary | [Expert consensus statements and summary of proceedings from the International Safety and Quality of Parenteral Nutrition Summit.](https://pubmed.ncbi.nlm.nih.gov/38869255/) | 38869255 | [PMC11170495](https://pmc.ncbi.nlm.nih.gov/articles/PMC11170495/) | 允许 | 未存 |
| CAND-G100-097 | temporal_cutoff_sensitive | [ESPEN guideline on nutrition and hydration in dementia - Update 2024.](https://pubmed.ncbi.nlm.nih.gov/38772068/) | 38772068 | — | 其他渠道待核 | 未存 |
| CAND-G100-098 | temporal_cutoff_sensitive | [Management of paediatric ulcerative colitis, part 1: Ambulatory care-An updated evidence-based consensus guideline from the European Society of Paediatric Gastroenterology, Hepatology and Nutrition and the European Crohn's and Colitis Organisation.](https://pubmed.ncbi.nlm.nih.gov/40677018/) | 40677018 | [PMC12408984](https://pmc.ncbi.nlm.nih.gov/articles/PMC12408984/) | 允许 | 未存 |
| CAND-G100-099 | incomplete_or_missing_source_text | [Cardiometabolic health improvements upon dietary intervention are driven by tissue-specific insulin resistance phenotype: A precision nutrition trial.](https://pubmed.ncbi.nlm.nih.gov/36599304/) | 36599304 | — | 其他渠道待核 | 未存 |
| CAND-G100-100 | incomplete_or_missing_source_text | [Short-term intermittent fasting and energy restriction do not impair rates of muscle protein synthesis: A randomised, controlled dietary intervention.](https://pubmed.ncbi.nlm.nih.gov/39418832/) | 39418832 | — | 其他渠道待核 | 未存 |

## F. 实际执行建议

先用剩余 51 条支持 PMC 自动正文获取的候选完成**合法原始文档收集和文件入库冒烟测试**；对 46 条非 PMC 自动来源建出版社、学会、机构库及授权访问队列。单独保存每个真实 PDF/HTML/XML 的 SHA256、授权、来源 URL、版本与归档对象位置；Markdown 作为衍生格式另存。

若只需可行性验证：可使用当前 97 篇而不必人为凑齐 100。若要恢复现有 **80+20 分层**：需同类型替换三篇。若要严格执行原始 **G1 First100 六类抽样**：需要重新定样，三篇替换不能解决结构漂移。
