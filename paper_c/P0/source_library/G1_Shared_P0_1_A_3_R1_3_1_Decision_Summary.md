# G1-Shared R1.3.1 Article Identity Block 与 12 源恢复

基线提交 `dd936ac7f9475eea2f22432ffaf3fb78741b5219`。冻结运行 `G1S-133-R1-3-TRUTHFULNESS-20261010T075311Z` 未改写。

## 身份块

生产函数 `evaluate_pdf_identity_canonical` 只在文章自身的 ArticleIdentityBlock 内同时接受完整标题和 DOI。目录页、编辑社论引用、以及标题与 DOI 不在同一身份块时，不再返回 `CONFIRMED`。

合成测试：补丁前 3 项对抗测试失败（均为 `CONFIRMED`），补丁后与原有 24 项机制测试一起为 28 项，退出码 0。测试调用同一生产函数。GitHub Actions job `verifier-unittest` 单独运行这组测试。

对 R1.3 的 86 条 `CONFIRMED` 重测：80 条仍为 `CONFIRMED`，5 条改为 `HOLD`（同一身份块内出现另一 DOI），1 条改为 `PROBABLE`（标题与 DOI 在同一页但距离超过 6000 字符）。25 条边界抽查的状态没有变化。

原先 34 条 `COMPLETE` 在新输出中记为 `PARTIAL_COMPLETENESS_EVIDENCE` / `BODY_BIBLIOGRAPHY_OBSERVED`。这只表示观察到参考文献标题，不表示逐页全文、表格或补充材料已核验。R1.3 原标签留在冻结目录。

## 12 源恢复

起点是 R1.3 `14_NDF_D1_case_specific_release_candidate.json` 的 12 条。历史下载日志没有 URL、HTTP 证据和记录签名，全部标为 `HISTORICAL_ACQUISITION_UNPROVEN`。未回填旧时间或旧签名。

`RELEASE_FOR_EXTRACTION`：2。

- `CAND-G100-004`：Nature CC BY 4.0 PDF，新文件与库内 PDF 字节相同，身份块 `AIB-p1-0`，标题锚点与 DOI 锚点回放成功。
- `CAND-G100-033`：Springer CC BY 4.0 PDF，新文件与库内 PDF 字节相同，身份块 `AIB-p1-0`，两项锚点回放成功。

这两条允许内部分层抽取。Expert Gold 未授予。CC BY 是出版商许可证记录，不是本项目的临床有效性结论。

其余 10 条保持 `HOLD`：

- 合法 OA/CC 地址存在，但本次客户端未拿到 PDF：`CAND-G100-095`、`096`、`005`、`046`、`048`、`055`。
- 没有公开全文许可：`CAND-G100-002`、`047`、`051`、`064`。`CAND-G100-047` 同时缺少可比较的版本日期。

本地证据目录：`/Users/zhangcd/Codes/Ai-Nutri/data/g1_source_library/verification_runs/G1S-R131-IDENTITY-BLOCK-D1-RECOVERY-20261010T101500Z`。
