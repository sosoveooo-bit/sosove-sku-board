# 对话创作室编译运行环境修复

**Goal:** 消除8795错误解释器缺少cryptography导致的本地编译故障，完整方案可只重编译而不重复调用AI。

**Architecture:** start.ps1固定workspace/.venv/Scripts/python.exe，启动前server.py --check-compiler验证；健康检查报告编译依赖可用状态和是否项目venv。实际编译异常按依赖缺失、字段校验、内部错误分类，日志记录traceback和错误编号，不向网页泄漏未知异常正文。

新增studio-compile仅本地确定性编译路由：先向8793验证当前账号权限，校验模式、页数、完整七层方案、市场和尺寸，保留原文编译。不转发策划或生图请求。前端按钮独立重试，成功后由用户点击生图。

**Validation:** 在实际项目虚拟环境运行完整测试及--check-compiler；真实编译器14页泰国fixture编译；依赖错误分型、未知错误内容保护；编译路由认证和不调用AI。保留8793和节点配置，仅空闲时重启8795。
