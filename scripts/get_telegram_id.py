import os
import time
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_chat_id():
    # 1. 检查 Token
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    # 简单的检查，防止用户忘记修改默认值
    if not token or "your_telegram_bot_token" in token:
        print("\n❌ 错误：检测到您尚未配置 TELEGRAM_BOT_TOKEN。")
        print("请先打开项目根目录下的 .env 文件，填入您从 @BotFather 获取的 Token。")
        print("格式示例：TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqRSTuvwXYZ\n")
        return

    print(f"🤖 正在使用 Token 连接 Telegram...")
    
    # 2. 验证 Bot 信息
    try:
        me_url = f"https://api.telegram.org/bot{token}/getMe"
        me_resp = requests.get(me_url, timeout=10)
        me_data = me_resp.json()
        
        if not me_data.get("ok"):
            print(f"❌ Token 无效或无法连接 Telegram 服务器。")
            print(f"错误信息: {me_data.get('description')}")
            return
            
        bot_username = me_data['result']['username']
        print(f"✅ 成功连接到机器人: @{bot_username}")
        print(f"\n👉 请现在打开 Telegram，搜索 @{bot_username}")
        print(f"👉 点击 'Start' 或给它发送一条任意消息（例如 'hello'）...")
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("请检查您的网络连接（是否需要代理？）。")
        return

    # 3. 轮询获取更新
    print("\n⏳ 正在等待您发送消息... (按 Ctrl+C 停止)")
    offset = 0
    while True:
        try:
            # 使用 getUpdates 接口获取最新消息
            updates_url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}"
            resp = requests.get(updates_url, timeout=10)
            data = resp.json()
            
            if data.get("ok"):
                results = data.get("result", [])
                for update in results:
                    # 更新 offset 以便下次只获取新消息
                    offset = update["update_id"] + 1
                    
                    message = update.get("message", {})
                    chat = message.get("chat", {})
                    chat_id = chat.get("id")
                    text = message.get("text", "")
                    username = message.get("from", {}).get("username", "unknown")
                    
                    if chat_id:
                        print("\n" + "="*40)
                        print(f"🎉 成功收到消息！")
                        print(f"👤 发送者: {username}")
                        print(f"📄 内容: {text}")
                        print(f"🆔 您的 Chat ID 是: {chat_id}")
                        print("="*40 + "\n")
                        print("✅ 下一步：")
                        print(f"1. 复制上面的数字 {chat_id}")
                        print("2. 打开 .env 文件")
                        print("3. 将其填入 TELEGRAM_CHAT_ID= 后面")
                        return # 找到后直接退出
            
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n已停止。")
            break
        except Exception as e:
            print(f"⚠️ 获取更新时出错: {e}")
            time.sleep(2)

if __name__ == "__main__":
    get_chat_id()
