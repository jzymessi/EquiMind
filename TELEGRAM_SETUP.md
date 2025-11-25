# Telegram 机器人配置指南

## 1. 创建 Bot
1. 打开 Telegram，搜索 `@BotFather`。
2. 发送 `/newbot`，依次输入机器人的显示名称与用户名（用户名需以 `bot` 结尾）。
3. BotFather 会返回 `HTTP API token`，即 `TELEGRAM_BOT_TOKEN`，请妥善保存。

## 2. 配置 EquiMind 环境变量
在项目根目录的 `.env` 中加入：

```bash
TELEGRAM_BOT_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789  # 可选，定时推送目标
```

- `TELEGRAM_CHAT_ID` 可以是个人、群组或频道的 ID：
  - 个人：让机器人与个人对话后，通过日志查看 `chat_id`；
  - 群组：将机器人拉入群组，在群里发送任意消息并查看日志中的 `chat_id`；
  - 频道：需要将机器人设置为管理员后才能发送消息。

## 3. 设置 Webhook（推荐）
EquiMind 提供 `/telegram/webhook` 用于实时接收消息。部署后执行：

```bash
curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/telegram/webhook"}'
```

- 本地开发可使用 `ngrok` 暴露接口：
  ```bash
  ngrok http 8000
  # 假设得到地址 https://xxxx.ngrok.io
  curl -X POST "https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://xxxx.ngrok.io/telegram/webhook"}'
  ```
- 如需取消 Webhook，可调用 `deleteWebhook`。

## 4. 测试机器人
1. 启动 EquiMind 后端：
   ```bash
   uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000
   ```
2. 在 Telegram 中与机器人对话，发送如 “帮我推荐 5 个值得关注的美股”。
3. 后端日志中可见：
   ```
   [Telegram] 收到消息: ...
   [Telegram] 已回复消息到 ...
   ```

## 5. 定时推送
- `mcp_server/scheduler.py` 会读取 `TELEGRAM_CHAT_ID`，在指定时间推送晨报、晚报。
- 可在 `state_store` 中调整 `morning_digest_time` / `evening_digest_time`，或直接在 `.env` 中设置默认值。

## 6. 常见问题
- **机器人无响应？**
  - 确认 Webhook 指向的地址可访问；
  - 检查后端日志是否收到更新；
  - 确保 `.env` 中的 `TELEGRAM_BOT_TOKEN` 正确。
- **群组内无法回复？**
  - 确保机器人已被添加到群组；
  - 对于私有群组，可在群内发送消息并在日志中查看 `chat_id`。
- **想使用轮询模式？**
  - 可编写脚本定期调用 `getUpdates` 接口，或在自行部署的 Worker 中实现。


