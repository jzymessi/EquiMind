#!/usr/bin/env python3
"""
设置 Telegram Webhook

使用方法：
1. 设置 Webhook: python setup_webhook.py set https://your-domain.com/webhook/telegram
2. 查看 Webhook: python setup_webhook.py info
3. 删除 Webhook: python setup_webhook.py delete
"""
import sys
from pathlib import Path
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcp_server.telegram_bot import _get_bot_token

TELEGRAM_API_BASE = "https://api.telegram.org"


def get_webhook_info(token: str):
    """获取当前 Webhook 配置"""
    url = f"{TELEGRAM_API_BASE}/bot{token}/getWebhookInfo"
    resp = requests.get(url, timeout=10)
    return resp.json()


def set_webhook(token: str, webhook_url: str):
    """设置 Webhook URL"""
    url = f"{TELEGRAM_API_BASE}/bot{token}/setWebhook"
    
    # Webhook 配置参数
    payload = {
        "url": webhook_url,
        "max_connections": 40,  # 最大并发连接数
        "drop_pending_updates": True,  # 删除旧的未处理消息
    }
    
    resp = requests.post(url, json=payload, timeout=10)
    return resp.json()


def delete_webhook(token: str):
    """删除 Webhook（切换回 Polling 模式）"""
    url = f"{TELEGRAM_API_BASE}/bot{token}/deleteWebhook"
    payload = {"drop_pending_updates": True}
    resp = requests.post(url, json=payload, timeout=10)
    return resp.json()


def main():
    token = _get_bot_token()
    if not token:
        print("❌ 错误: TELEGRAM_BOT_TOKEN 未配置")
        print("请在 .env 文件中设置 TELEGRAM_BOT_TOKEN")
        return
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print(f"  {sys.argv[0]} set <webhook_url>   # 设置 Webhook")
        print(f"  {sys.argv[0]} info                # 查看 Webhook 信息")
        print(f"  {sys.argv[0]} delete              # 删除 Webhook")
        print()
        print("示例:")
        print(f"  {sys.argv[0]} set https://your-domain.com/webhook/telegram")
        return
    
    command = sys.argv[1].lower()
    
    if command == "info":
        print("📡 正在查询 Webhook 信息...\n")
        result = get_webhook_info(token)
        
        if result.get("ok"):
            info = result.get("result", {})
            url = info.get("url", "")
            
            if url:
                print("✅ Webhook 已设置")
                print(f"   URL: {url}")
                print(f"   待处理消息: {info.get('pending_update_count', 0)}")
                print(f"   最后错误: {info.get('last_error_message', '无')}")
                if info.get("last_error_date"):
                    from datetime import datetime
                    error_time = datetime.fromtimestamp(info.get("last_error_date"))
                    print(f"   错误时间: {error_time}")
            else:
                print("ℹ️  Webhook 未设置（当前使用 Polling 模式）")
        else:
            print(f"❌ 查询失败: {result.get('description')}")
    
    elif command == "set":
        if len(sys.argv) < 3:
            print("❌ 错误: 请提供 Webhook URL")
            print(f"使用方法: {sys.argv[0]} set <webhook_url>")
            return
        
        webhook_url = sys.argv[2]
        
        # 验证 URL
        if not webhook_url.startswith("https://"):
            print("❌ 错误: Telegram 要求使用 HTTPS")
            print("   Webhook URL 必须以 https:// 开头")
            return
        
        print(f"📡 正在设置 Webhook: {webhook_url}\n")
        result = set_webhook(token, webhook_url)
        
        if result.get("ok"):
            print("✅ Webhook 设置成功！")
            print()
            print("接下来的步骤：")
            print("1. 启动 Webhook 服务器:")
            print("   python scripts/telegram_webhook.py")
            print()
            print("2. 或使用 uvicorn（生产环境）:")
            print("   uvicorn scripts.telegram_webhook:app --host 0.0.0.0 --port 8000")
            print()
            print("3. 在 Telegram 中发送消息测试")
            print()
            print("4. 查看 Webhook 状态:")
            print(f"   python {sys.argv[0]} info")
        else:
            print(f"❌ 设置失败: {result.get('description')}")
    
    elif command == "delete":
        print("🗑️  正在删除 Webhook...\n")
        result = delete_webhook(token)
        
        if result.get("ok"):
            print("✅ Webhook 已删除")
            print()
            print("现在可以切换回 Polling 模式:")
            print("   python scripts/telegram_polling.py")
        else:
            print(f"❌ 删除失败: {result.get('description')}")
    
    else:
        print(f"❌ 未知命令: {command}")
        print("支持的命令: info, set, delete")


if __name__ == "__main__":
    main()
