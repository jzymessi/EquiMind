#!/usr/bin/env python3
"""
Telegram Webhook 服务器
使用 FastAPI 接收 Telegram 的消息推送

部署要求：
1. 有公网 IP 或域名
2. 支持 HTTPS（Telegram 要求）
3. 设置 Webhook URL
"""
import sys
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import uvicorn

# 加载环境变量
load_dotenv()

# 添加项目根目录到 sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcp_server.telegram_bot import handle_telegram_update, _get_bot_token

app = FastAPI(title="EquiMind Telegram Webhook")


@app.get("/")
async def root():
    """健康检查端点"""
    return {
        "status": "ok",
        "service": "EquiMind Telegram Webhook",
        "message": "Webhook server is running"
    }


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """
    接收 Telegram 的 Webhook 推送
    
    Telegram 会将消息 POST 到这个端点
    """
    try:
        # 获取请求体
        update = await request.json()
        
        # 处理更新
        result = handle_telegram_update(update)
        
        if result.get("success"):
            return {"ok": True}
        else:
            print(f"[Webhook] 处理失败: {result.get('error')}")
            return {"ok": False, "error": result.get("error")}
            
    except Exception as e:
        print(f"[Webhook] 异常: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/webhook/info")
async def webhook_info():
    """查看当前 Webhook 配置信息"""
    import requests
    
    token = _get_bot_token()
    if not token:
        return {"error": "TELEGRAM_BOT_TOKEN 未配置"}
    
    try:
        resp = requests.get(
            f"https://api.telegram.org/bot{token}/getWebhookInfo",
            timeout=10
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("=" * 60)
    print("  EquiMind Telegram Webhook 服务器")
    print("=" * 60)
    print()
    print("📡 Webhook 端点: http://your-domain.com/webhook/telegram")
    print("🔍 健康检查: http://localhost:8000/")
    print("ℹ️  Webhook 信息: http://localhost:8000/webhook/info")
    print()
    print("⚠️  注意事项：")
    print("1. Telegram 要求使用 HTTPS")
    print("2. 需要先设置 Webhook URL（见下方命令）")
    print("3. 确保防火墙开放端口")
    print()
    print("=" * 60)
    
    # 启动服务器
    # 生产环境建议使用: uvicorn telegram_webhook:app --host 0.0.0.0 --port 8000
    uvicorn.run(
        app,
        host="0.0.0.0",  # 监听所有网络接口
        port=8000,
        log_level="info"
    )
