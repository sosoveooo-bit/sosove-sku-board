"""Classify upstream failures without another model call or exposing configuration."""
def describe(error):
    message = str(error or '').lower()
    if not message:
        return None
    # A model chain may contain several errors; surface all applicable remedies.
    actions, codes = [], []
    for code, markers, action in (
        ('product_identity', ('产品身份待确认',),
         '旧版确认暂停步骤已移除，点击继续策划即可复用已保存分析；已有图片保留。'),
        ('billing', ('http 402', 'payment required', 'insufficient_quota', 'insufficient balance'),
         '导演接口返回计费或额度错误（如 HTTP 402）。请检查导演服务余额、套餐和 API Key 额度，或切换可用导演节点；已完成策划保留，恢复后继续缺失页，不必新建套图。'),
        ('output_limit', ('输出达到长度上限',), '模型输出触及长度上限。规划已按小批保存并自动缩批；单页仍超限时请检查导演接口输出额度，继续时只处理缺失页。'),
        ('structured_output', ('json', '空正文'), '导演回复格式异常，已做有限格式重试；保留已完成阶段，继续时只处理缺失阶段。'),
        ('model_route', ('unknown provider', 'model not found'), '检查导演节点的模型名称与供应商路由，选择该接口实际支持的模型。'),
        ('rate_limit', ('429', 'cooling down', 'usage_limit_reached'), '上游凭据处于限流或冷却状态，等待恢复或切换可用节点后继续。'),
        ('connection', ('timed out', 'timeout', 'sslerror', 'sslwantwrite', 'connection aborted', 'stream disconnected', '上传超时', '接口传输未完成', '建立连接超时'), '请求连接、上传或响应中断；检查导演接口连通性后继续，已完成阶段会复用。'),
    ):
        if any(marker in message for marker in markers):
            codes.append(code)
            actions.append(action)
    return {'codes': codes or ['planning'], 'actions': actions or ['查看下方具体原因，修正相关设置或页面设计后继续策划。'],
            'automaticRetry': False}
