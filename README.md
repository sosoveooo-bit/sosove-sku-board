# SOSOVE SKU Board

商品、设计、任务、广告分析、素材投放与 AI 生图的一体化运营面板。

[English](#english) | 简体中文

## 功能

- 商品与 SKU 看板：筛选、负责人、优先级、利润与止损状态。
- 设计与素材流程：设计任务、素材缺口、翻新记录、投放反馈。
- Meta 广告：广告账户与系统凭证管理、数据拉取、素材投放草稿。
- AI 生图工作台：参考图角色、导演分镜、套装生成、失败重试、取消与恢复。
- 多平台套图：日本落地页、Amazon A+、乐天、COD 国家专区与 COD 详情图。
- 对话创作室：复用面板账号、模型和生成引擎，支持提示词编译与任务历史。
- 可选集成：Shopline 商品导入、GA4、OpenAI 兼容导演接口和远程生图节点。

## 本地启动

需要 Python 3.11 或更高版本。

```powershell
git clone https://github.com/sosoveooo-bit/sosove-sku-board.git
cd sosove-sku-board
python -m venv .venv
.\.venv\Scripts\pip install -r sku_board\requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python -m sku_board.server --host 127.0.0.1 --port 8793
```

打开 `http://127.0.0.1:8793/`。首次启动会生成运行数据目录和初始面板数据。

Linux 或 macOS：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r sku_board/requirements.txt
cp .env.example .env
python -m sku_board.server --host 127.0.0.1 --port 8793
```

## 对话创作室

仓库包含 `cod-chat-studio/`，它复用 8793 的账号、模型与生成引擎。完成根目录依赖安装并启动 8793 后运行：

```powershell
.\cod-chat-studio\start.ps1
```

支持 COD 国家专区、COD 详情图、日本 25 图、多市场生成、缺页续写、取消任务与历史管理。

## Docker 部署

```bash
git clone https://github.com/sosoveooo-bit/sosove-sku-board.git
cd sosove-sku-board
cp .env.example .env
```

首次部署至少设置：

```dotenv
SKU_BOARD_ADMIN_PASSWORD=replace-with-a-strong-password
SKU_BOARD_CREDENTIAL_ENCRYPTION_KEY=replace-with-a-random-string-of-32-or-more-characters
```

然后启动：

```bash
docker compose up -d --build
```

面板地址为 `http://VPS_IP:8793/`。持久化数据位于 `data/`，升级前请备份：

```bash
tar -czf sku-board-data-$(date +%F).tar.gz data
```

更新代码后可执行：

```bash
bash scripts/deploy-update.sh
```

## 配置与安全

所有密钥只应保存在本机 `.env` 或面板的加密凭证存储中，不要提交到 Git。常用配置项包括：

- `SKU_BOARD_ADMIN_PASSWORD`、`SKU_BOARD_CREDENTIAL_ENCRYPTION_KEY`：面板登录和凭证加密。
- `CHATGPT2API_NODES_JSON`、`ACORE_IMAGE_*`：远程生图节点。
- `AI_DIRECTOR_*`：OpenAI 兼容导演模型。
- `META_*`、`FB_*`：Meta OAuth、公共主页和广告投放。
- `SHOPLINE_*`、`GA4_*`：Shopline 商品与 GA4 数据。

完整字段见 [`.env.example`](.env.example)。未配置外部服务时，面板仍可启动，但对应集成不可用。

`.gitignore` 默认排除 `.env`、运行数据库、日志、上传文件、生成图片和导出数据。部署时请使用独立密钥，并限制面板端口的公网访问。

## HTTPS

Nginx 示例位于 `deploy/nginx/sosove-sku-board.conf`。替换域名后启用配置并申请证书：

```bash
sudo cp deploy/nginx/sosove-sku-board.conf /etc/nginx/sites-available/sosove-sku-board
sudo ln -s /etc/nginx/sites-available/sosove-sku-board /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d panel.example.com
```

启用 HTTPS 后，把 `.env` 中的 `SKU_BOARD_SECURE_COOKIE=1`，并将 `SKU_BOARD_PUBLIC_URL` 与 `META_OAUTH_REDIRECT_URI` 设置为正式域名。

## 健康检查

```bash
curl http://127.0.0.1:8793/api/health
docker compose logs -f --tail=100
```

## 测试

```bash
python -m unittest discover -s sku_board/tests -p "test_*.py"
node --check sku_board/static/app.js
```

部分集成测试需要本机环境变量或远端服务；未配置时应跳过对应测试，而不是提交真实凭证。

## 开源边界

本仓库只包含面板源码、测试和部署模板，不包含任何账号凭证、客户商品数据、生成结果或私有素材。接入第三方平台时，请自行确认平台条款、广告政策和素材授权。

## License

[MIT](LICENSE)

---

## English

SOSOVE SKU Board is a self-hosted operations panel for product and SKU tracking, design tasks, Meta ad operations, creative material management, and multi-platform AI image generation.

The repository includes the main panel, the COD chat studio, platform-specific image suite workflows, tests, Docker deployment files, and an example environment file. It does not include credentials, customer data, uploaded media, generated images, or local runtime state.

Quick start:

```bash
git clone https://github.com/sosoveooo-bit/sosove-sku-board.git
cd sosove-sku-board
python -m venv .venv
source .venv/bin/activate
pip install -r sku_board/requirements.txt
cp .env.example .env
python -m sku_board.server --host 127.0.0.1 --port 8793
```

Configure secrets in `.env` and review the service-specific settings before exposing the panel to the public internet. The project is released under the MIT License.
