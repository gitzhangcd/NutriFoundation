# 按需证据核查
用户已确认：阅读中逐条显示证据状态；核查打开侧边面板；提交前进入独立核查视图。
侧边面板展示判断、完整引文、来源单元与三个独立状态：原文范围、判断关联、PDF 定位。未核验 PDF 不显示成功。判断改动后的旧绑定提示重新确认。缺证据提示待补充，但不新增科研冻结门禁。
回看原文关闭面板并定位来源，保留草稿。沿用任务权限、服务端校验及 19 字段契约。此次同步现有 GitHub PR #23，不自动部署阿里云。

## Sites reference fidelity correction
The prior iteration updated review only and left the citation interaction unchanged. This correction replaces inline dropdown/direct binding with a floating citation action and a side confirmation tab. Full quote, character count, sentence/paragraph adjustment, source highlight, translation alignment warning and table context are explicit. Invalid cross-unit or cross-cell selections clear the cached quote; manual edits require re-location. Binding requires a saved concrete statement, and success reports source/judgment/PDF independently. Linked evidence and judgment editing have separate tab entries. Submission review remains a separate screen.

Intentional difference: no destructive unlink is provided because the formal server stores immutable audited bindings. Missing links and stale statements remain explicit. Synthetic source remains non-citable, unlike the demonstration-only prototype's local mock evidence. Sites is not modified. This correction is deployed to the existing Aliyun synthetic staging at the user's request.
