# 对话创作室三模式接入实施计划

**Goal:** 在 8795 添加日本产品落地页25图和 COD详情图，保留原 COD 国家专区与 8793 引擎。

**Architecture:** workflow.js 定义白名单模式、参数校验和默认值；app.js 使用会话 suiteKey 构造策划与生成请求。旧会话缺少 suiteKey 时按原 COD 国家专区解释。有内容的会话切换时新建对话，保留旧记录。server.py 使用现有代理，无需新增接口。

**Tech Stack:** 原生 JavaScript、IndexedDB、Python unittest、Node VM fixtures。

## 步骤与验收

1. workflow.js / test_workflow.cjs：先写模式路由测试；验证日本固定25页/JP/1500x2000，详情12/16/20/22页，COD旧会话14页兼容；非法页数明确提示。
2. index.html / workflow.css / app.js：新增模式选择器及帮助文字；历史展示模式；fresh、form、infer、plan、export 全链路传递模式；忙碌时禁止切换；已编辑会话保留后新建。
3. plan_preview.py 现有编译保持通用；test_plan_preview.py 对三模式使用原引擎验证 key/count/size 合同，mock 验证编译路由及不使用首图位图。
4. 测试策划、生成、续写、重试请求的 suiteKey、页数和尺寸一致；错模式响应在采纳前停止。运行全部 Python/Node 测试与 JS 语法检查。
5. 仅重启 8795，检查本地和公网资源、会话接口；不提交付费 AI 任务。文档记录新增模式和固定参数。

不改 8793 源码、模型和生图节点配置；不触发真实生图计费；不提交工作区其他改动。
