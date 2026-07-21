# SOSOVE SKU Board

商品、设计、任务、广告分析、素材投放和 AI 生图的一体化运营面板。

## 本地启动

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r sku_board\requirements.txt
.\.venv\Scripts\python -m sku_board.server --host 127.0.0.1 --port 8793
```

打开 `http://127.0.0.1:8793/`。

## VPS Docker 部署

```bash
git clone https://github.com/OWNER/sosove-sku-board.git
cd sosove-sku-board
cp .env.example .env
nano .env
docker compose up -d --build
```

面板地址：`http://VPS_IP:8793/`

首次部署请至少在 `.env` 设置：

```dotenv
SKU_BOARD_ADMIN_PASSWORD=替换为强密码
SKU_BOARD_CREDENTIAL_ENCRYPTION_KEY=替换为32位以上随机字符串
```

`data/` 是持久化目录，包含账号、产品、任务、广告配置、生成图片和会话数据；升级前备份：

```bash
tar -czf sku-board-data-$(date +%F).tar.gz data
```

更新部署：

```bash
bash scripts/deploy-update.sh
```

## HTTPS / 域名

Nginx 示例在 `deploy/nginx/sosove-sku-board.conf`。替换域名后启用配置并申请证书：

```bash
sudo cp deploy/nginx/sosove-sku-board.conf /etc/nginx/sites-available/sosove-sku-board
sudo ln -s /etc/nginx/sites-available/sosove-sku-board /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d panel.example.com
```

启用 HTTPS 后把 `.env` 中 `SKU_BOARD_SECURE_COOKIE=1`，并将 `SKU_BOARD_PUBLIC_URL`、`META_OAUTH_REDIRECT_URI` 设置为正式域名。

## 健康检查

```bash
curl http://127.0.0.1:8793/api/health
docker compose logs -f --tail=100
```
