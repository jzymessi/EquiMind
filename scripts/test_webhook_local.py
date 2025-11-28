#!/usr/bin/env python3
"""
本地测试 Webhook 服务器

在没有公网IP的情况下，测试 Webhook 服务器是否正常工作
"""
import requests
import json

def test_webhook_server():
    """测试本地 Webhook 服务器"""
    
    print("🧪 测试 Webhook 服务器\n")
    
    # 1. 测试健康检查
    print("1️⃣ 测试健康检查端点...")
    try:
        resp = requests.get("http://localhost:8000/", timeout=5)
        if resp.status_code == 200:
            print("   ✅ 健康检查通过")
            print(f"   响应: {resp.json()}")
        else:
            print(f"   ❌ 失败: HTTP {resp.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        print("   提示: 请先启动服务器: python scripts/telegram_webhook.py")
        return
    
    # 2. 测试 Webhook 端点（模拟消息）
    print("\n2️⃣ 测试 Webhook 端点...")
    
    # 模拟 Telegram 发送的消息
    fake_update = {
        "update_id": 999999,
        "message": {
            "message_id": 1,
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Test",
                "username": "test_user"
            },
            "chat": {
                "id": 123456789,
                "first_name": "Test",
                "username": "test_user",
                "type": "private"
            },
            "date": 1234567890,
            "text": "/start"
        }
    }
    
    try:
        resp = requests.post(
            "http://localhost:8000/webhook/telegram",
            json=fake_update,
            timeout=10
        )
        
        if resp.status_code == 200:
            print("   ✅ Webhook 端点正常")
            print(f"   响应: {resp.json()}")
        else:
            print(f"   ❌ 失败: HTTP {resp.status_code}")
            print(f"   响应: {resp.text}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    # 3. 测试 Webhook 信息端点
    print("\n3️⃣ 测试 Webhook 信息端点...")
    try:
        resp = requests.get("http://localhost:8000/webhook/info", timeout=5)
        if resp.status_code == 200:
            print("   ✅ Webhook 信息端点正常")
            info = resp.json()
            if info.get("result"):
                webhook_url = info["result"].get("url", "")
                if webhook_url:
                    print(f"   当前 Webhook: {webhook_url}")
                else:
                    print("   当前未设置 Webhook（使用 Polling 模式）")
        else:
            print(f"   ❌ 失败: HTTP {resp.status_code}")
    except Exception as e:
        print(f"   ❌ 错误: {e}")
    
    print("\n" + "="*60)
    print("✅ 本地测试完成")
    print("\n下一步:")
    print("1. 如果有公网IP/域名，使用:")
    print("   python scripts/setup_webhook.py set https://your-domain.com/webhook/telegram")
    print()
    print("2. 如果没有公网IP，继续使用 Polling:")
    print("   python scripts/telegram_polling.py")
    print("="*60)


if __name__ == "__main__":
    test_webhook_server()
