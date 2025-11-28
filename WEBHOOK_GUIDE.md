# Telegram Webhook 部署指南

## 📋 目录

1. [Webhook vs Polling](#webhook-vs-polling)
2. [前置要求](#前置要求)
3. [快速开始](#快速开始)
4. [生产环境部署](#生产环境部署)
5. [故障排查](#故障排查)

## Webhook vs Polling

| 特性 | Polling（轮询） | Webhook（推送） |
|------|----------------|----------------|
| **实时性** | 延迟0.5-30秒 | 即时（毫秒级） ✅ |
| **服务器负载** | 持续请求 | 按需处理 ✅ |
| **网络消耗** | 高（持续连接） | 低（仅接收消息） ✅ |
| **部署要求** | 无需公网IP ✅ | 需要公网IP/域名 |
| **HTTPS要求** | 不需要 ✅ | 必须 |

**推荐场景：**
- 🏠 **开发/测试**: 使用 Polling
- 🌐 **生产环境**: 使用 Webhook（有公网IP/域名）

## 前置要求

### 1. 公网访问
- ✅ 公网 IP 地址
- ✅ 或域名（推荐）
- ✅ 防火墙开放端口（如 8000 或 443）

### 2. HTTPS 证书
Telegram **强制要求** Webhook 使用 HTTPS。有以下选择：

#### 选项A：使用 Nginx + Let's Encrypt（推荐）
```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取免费 SSL 证书
sudo certbot --nginx -d your-domain.com
```

#### 选项B：使用 Cloudflare
- 将域名托管到 Cloudflare
- 自动获得免费 SSL 证书
- 额外获得 CDN 加速

#### 选项C：自签名证书（仅测试）
```bash
openssl req -newkey rsa:2048 -sha256 -nodes -keyout private.key -x509 -days 365 -out cert.pem
```

## 快速开始

### 步骤1：启动 Webhook 服务器

```bash
cd /home/leo/EquiMind
source .venv/bin/activate

# 开发模式
python scripts/telegram_webhook.py

# 或生产模式（推荐）
uvicorn scripts.telegram_webhook:app --host 0.0.0.0 --port 8000
```

### 步骤2：设置 Webhook URL

```bash
# 设置 Webhook
python scripts/setup_webhook.py set https://your-domain.com/webhook/telegram

# 查看 Webhook 状态
python scripts/setup_webhook.py info

# 删除 Webhook（切换回 Polling）
python scripts/setup_webhook.py delete
```

### 步骤3：测试

在 Telegram 中发送消息：
```
/agent 生成 AAPL 价格走势图
```

查看服务器日志，应该看到：
```
INFO:     127.0.0.1:xxxxx - "POST /webhook/telegram HTTP/1.1" 200 OK
[Telegram] 收到消息: /agent 生成 AAPL 价格走势图 (来自: xxx / Leo)
```

## 生产环境部署

### 方案1：Nginx 反向代理（推荐）

#### 1. 安装 Nginx
```bash
sudo apt update
sudo apt install nginx
```

#### 2. 配置 Nginx
创建配置文件 `/etc/nginx/sites-available/equimind`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 证书（Let's Encrypt）
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL 配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 反向代理到 FastAPI
    location /webhook/telegram {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 健康检查
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

#### 3. 启用配置
```bash
sudo ln -s /etc/nginx/sites-available/equimind /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 4. 使用 systemd 管理服务
创建 `/etc/systemd/system/equimind-webhook.service`:

```ini
[Unit]
Description=EquiMind Telegram Webhook
After=network.target

[Service]
Type=simple
User=leo
WorkingDirectory=/home/leo/EquiMind
Environment="PATH=/home/leo/EquiMind/.venv/bin"
ExecStart=/home/leo/EquiMind/.venv/bin/uvicorn scripts.telegram_webhook:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable equimind-webhook
sudo systemctl start equimind-webhook
sudo systemctl status equimind-webhook
```

### 方案2：Docker 部署

#### 1. 创建 Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "scripts.telegram_webhook:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. 构建和运行
```bash
docker build -t equimind-webhook .
docker run -d -p 8000:8000 --env-file .env --name equimind equimind-webhook
```

### 方案3：Cloudflare Tunnel（无需公网IP）

如果没有公网IP，可以使用 Cloudflare Tunnel：

```bash
# 安装 cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# 登录
cloudflared tunnel login

# 创建隧道
cloudflared tunnel create equimind

# 配置路由
cloudflared tunnel route dns equimind your-domain.com

# 运行隧道
cloudflared tunnel --url http://localhost:8000 run equimind
```

## 故障排查

### 问题1：Webhook 设置失败

**错误信息**: `Bad Request: bad webhook: HTTPS url must be provided for webhook`

**解决方案**: 
- 确保 URL 以 `https://` 开头
- 不能使用 `http://`

### 问题2：Webhook 无法访问

**错误信息**: `Bad Request: bad webhook: Failed to resolve host`

**解决方案**:
1. 检查域名 DNS 解析是否正确
2. 确保防火墙开放端口
3. 测试服务器是否可访问：
   ```bash
   curl https://your-domain.com/webhook/telegram
   ```

### 问题3：SSL 证书错误

**错误信息**: `Bad Request: bad webhook: Wrong response from the webhook: 526`

**解决方案**:
1. 检查 SSL 证书是否有效
2. 确保证书链完整
3. 测试 SSL：
   ```bash
   curl -v https://your-domain.com/webhook/telegram
   ```

### 问题4：消息未收到

**检查步骤**:

1. 查看 Webhook 状态
   ```bash
   python scripts/setup_webhook.py info
   ```

2. 检查待处理消息数
   - 如果 `pending_update_count > 0`，说明有消息堆积

3. 查看服务器日志
   ```bash
   # systemd 服务
   sudo journalctl -u equimind-webhook -f
   
   # Docker
   docker logs -f equimind
   ```

4. 测试端点
   ```bash
   curl -X POST https://your-domain.com/webhook/telegram \
     -H "Content-Type: application/json" \
     -d '{"update_id": 1, "message": {"text": "test"}}'
   ```

### 问题5：切换回 Polling 模式

如果 Webhook 有问题，可以临时切换回 Polling：

```bash
# 删除 Webhook
python scripts/setup_webhook.py delete

# 启动 Polling
python scripts/telegram_polling.py
```

## 监控和日志

### 查看 Webhook 信息
```bash
python scripts/setup_webhook.py info
```

输出示例：
```
✅ Webhook 已设置
   URL: https://your-domain.com/webhook/telegram
   待处理消息: 0
   最后错误: 无
```

### 实时日志
```bash
# 开发模式
python scripts/telegram_webhook.py

# 生产模式（systemd）
sudo journalctl -u equimind-webhook -f
```

## 性能优化

### 1. 使用多进程
```bash
uvicorn scripts.telegram_webhook:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

### 2. 启用 HTTP/2
在 Nginx 配置中已启用 `http2`

### 3. 设置连接池
Telegram 默认最多 40 个并发连接

## 安全建议

1. **验证请求来源**（可选）
   - Telegram 的 IP 范围：`149.154.160.0/20` 和 `91.108.4.0/22`

2. **使用环境变量**
   - 不要在代码中硬编码 Token

3. **限流保护**
   - 使用 Nginx 限流模块

4. **日志脱敏**
   - 不要记录敏感信息

## 总结

### Polling 模式（当前）
```bash
python scripts/telegram_polling.py
```

### Webhook 模式（推荐）
```bash
# 1. 启动服务
uvicorn scripts.telegram_webhook:app --host 0.0.0.0 --port 8000

# 2. 设置 Webhook
python scripts/setup_webhook.py set https://your-domain.com/webhook/telegram

# 3. 测试
python scripts/setup_webhook.py info
```

### 切换模式
```bash
# Webhook → Polling
python scripts/setup_webhook.py delete
python scripts/telegram_polling.py

# Polling → Webhook
# 停止 polling 脚本（Ctrl+C）
python scripts/setup_webhook.py set https://your-domain.com/webhook/telegram
```

---

**需要帮助？** 查看 [Telegram Bot API 文档](https://core.telegram.org/bots/api#setwebhook)
