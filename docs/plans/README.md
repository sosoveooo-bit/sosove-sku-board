# 设计与实施记录

本目录保存面板各功能模块的设计文档和实施记录，按日期命名。

这些文档是开发过程的原始记录，不是使用手册。它们用于说明某项功能为什么
这样实现、当时的约束是什么、以及哪些方案被否决过。阅读代码时如需了解背景，
可以从这里对应的日期文件入手。

## 阅读方式

- 文件名格式为 `YYYY-MM-DD-主题.md`，日期是开始该工作的日期。
- 文档写于实现当时，描述的是那一版的状态。后续改动可能已经覆盖其中结论，
  以当前代码为准。
- 部分文档开头带有当时使用的 AI 编码助手标记，属于历史记录，可以忽略。

## 主要主题

| 主题 | 相关文档 |
| --- | --- |
| COD 国家专区与详情图 | `2026-09-18-cod-all-main.md`、`2026-09-18-cod-commercial-design.md`、`2026-09-18-cod-visual-diversity.md`、`2026-09-18-cod-github-restore.md` |
| 日本落地页与 25 图 | `2026-08-01-jp-company-image-effect-v24.md`、`2026-08-03-jp-company-landing-v25-design.md`、`2026-09-07-jp25-online-photography.md` |
| AI 导演与策划预算 | `2026-09-12-cod-director-latency.md`、`2026-09-12-director-budget-continuation.md`、`2026-09-18-director-time-slices.md` |
| 提示词契约与文案保真 | `2026-08-14-verbatim-prompt-contract-design.md`、`2026-09-18-exact-copy-contract.md`、`2026-09-18-cod-artwork-language-boundary.md` |
| 对话创作室 | `2026-09-12-studio-history-menu.md`、`2026-09-12-studio-planning-speed.md`、`2026-09-13-studio-compiler-runtime.md` |
| 部署与安装 | `2026-09-09-nas-one-command-installer.md`、`2026-09-09-vps-latest-release.md` |
| 生图任务生命周期 | `2026-09-13-image-task-cancellation.md`、`2026-09-12-remove-generated-image-review.md` |
