# HOLD 与例外

`RELEASE_FOR_EXTRACTION` 只允许内部候选抽取。本试点没有授予 Expert Gold，也没有把两条来源合成一个证据体。

## 仍为 HOLD 的来源

人工下载任务，公开地址有记录但本次没有拿到 PDF：`CAND-G100-095`、`096`、`005`、`046`、`048`、`055`。

本次 Europe PMC / Crossref 没有找到符合规则的公开 PDF 入口：`CAND-G100-002`、`047`、`051`、`064`。这个记录的名称是 `NO_QUALIFYING_OA_ROUTE_FOUND_THIS_RUN`。它表示本轮工具没有找到合格公开路线，不表示机构订阅、作者授权文本或其他合法渠道都不存在。

## 两条已抽取来源

L1 与 L2 见 `Evidence_Qualification_Gates.json`。L3 与 L4 保持 `HOLD_HUMAN_REVIEW_REQUIRED`。`QUALIFIED_FOR_SPECIFIC_QUESTION` 为 0。ScientificReferenceState 只有 DRAFT。

重新获取时间是 2026-10-10，晚于证据 cutoff `2026-10-07`。该时间是获取事件，不是论文发表日期，也不是历史可获得时间。

图 1 的文本层把 “Allocated to eTRF” 出现了两次，并且没有 “Allocated to control” 字符串。正文写明三个组。这记为文本层风险，不改写原图。
