# Facebook Ads Monitor

独立的 Meta 广告监控面板：读取拉取好的广告报表，汇总账户、系列、广告组和素材
层级的花费与转化，给出放量 / 降预算 / 查承接的判断，并支持批量暂停与复制系列。

它是 `sku_board` 的可选依赖。缺失时主面板照常启动，只是 Meta 广告相关功能不可用。

## 数据来源

本模块不直接调用 Meta API 拉数据。它读取一份已拉取好的报表目录，结构如下：

```
reports/fb_pull_report/<report_name>/
├── summary.json
├── account_summary.csv
├── findings.csv
└── act_<account_id>/
    ├── account.csv
    ├── campaign.csv
    ├── adset.csv
    └── ad.csv
```

拉取动作交给外部脚本，通过环境变量指定：

| 变量 | 说明 | 默认值 |
| --- | --- | --- |
| `FB_ADS_REPORT_ROOT` | 报表根目录 | `facebook_ads_monitor/reports/fb_pull_report` |
| `FB_ADS_PULL_SCRIPT` | 拉取脚本路径 | `<FB_ADS_SKILL_ROOT>/scripts/fb_pull_report.py` |
| `FB_ADS_SKILL_ROOT` | 拉取脚本的工作目录 | 仓库根目录 |
| `FB_ADS_TOKEN_PATH` | 访问令牌文件 | `facebook_ads_monitor/fb_token.txt` |
| `FB_ADS_PULL_TIMEOUT_SECONDS` | 单次拉取超时 | `1800` |

令牌文件接受三种写法：纯文本令牌、`{"access_token": "..."}`、或
`?access_token=...` 查询串。

## 启动

```bash
python -m facebook_ads_monitor.server --host 127.0.0.1 --port 8790
```

打开 `http://127.0.0.1:8790/`。接口：

| 方法与路径 | 说明 |
| --- | --- |
| `GET /api/health` | 健康检查 |
| `GET /api/metrics` | 面板数据，支持 `report`、`range`、`refresh` 参数 |
| `POST /api/campaigns/pause` | 暂停系列，需 `confirm: "PAUSE_CAMPAIGNS"` |
| `POST /api/campaigns/copy` | 复制系列，需 `confirm: "COPY_CAMPAIGNS"` |

## 安全说明

- 令牌只从文件读取，不写入报表、日志或接口响应。
- 错误信息经 `redact_token_text()` 处理后再对外返回，会抹掉 `access_token`
  的值以及裸的 `EAA…` 令牌。
- 暂停和复制属于破坏性操作，必须显式传入确认字符串；单次批量上限分别为
  20 个和 10 个系列。
- 面板没有内置鉴权，请只监听回环地址或置于反向代理之后。

## 测试

```bash
python -m unittest discover -s facebook_ads_monitor/tests -t . -p "test_*.py"
```

测试全部离线运行，报表夹具写入临时目录，不会访问网络或真实报表。
