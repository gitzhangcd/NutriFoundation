# WB-P0.2-C0｜页面契约与合成交互原型

本包依赖 `Workbench System Master v0.2`。此阶段仅用合成数据验证页面结构，不作医学科学结论或正式 Pre-AI 事务声明。

## 使用

直接在浏览器打开 `prototype/index.html`；所有内容均为本地演示，不会向服务器上传专家数据。

## 验证

```bash
python tests/validate_c0.py
python tests/browser_smoke.py
```

后者依赖 Playwright 和 Chromium，若浏览器不在 `/usr/bin/chromium`，需调整脚本的路径。

## 不同于正式实现

- 只做交互原型；页面完整性不等于字段覆盖完整。
- 本地原型没有 API/身份/多用户持久化，`Draft` 仅会话级模拟。
- R0/R1/R2 的实际敏感内容必须由未来服务端投影隔离；本演示的合成数据防漏检查不能替代这一点。
- B1 已验证的 PDF.js 阅读能力尚未集成到此 C0 原型，后续 C1 执行。