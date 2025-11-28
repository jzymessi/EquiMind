"""
定时检查提醒脚本
每隔一段时间检查所有用户的提醒，触发时通过 Telegram 发送通知
"""
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到 sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcp_server.alert_manager import alert_manager
from mcp_server.telegram_bot import send_telegram_message

def check_all_alerts():
    """检查所有用户的提醒"""
    alert_dir = Path("data/alerts")
    
    if not alert_dir.exists():
        print("[Info] 提醒目录不存在")
        return
    
    # 遍历所有用户的提醒文件
    for alert_file in alert_dir.glob("*.json"):
        user_id = alert_file.stem
        
        try:
            # 检查该用户的提醒
            triggered = alert_manager.check_alerts(user_id)
            
            if triggered:
                print(f"[Alert] 用户 {user_id} 有 {len(triggered)} 个提醒被触发")
                
                # 发送 Telegram 通知
                message = f"🔔 **提醒通知**\n\n"
                
                for alert in triggered:
                    trigger_msg = alert.get("trigger_message", "提醒已触发")
                    message += f"• {trigger_msg}\n"
                
                message += f"\n共 {len(triggered)} 个提醒已触发"
                
                # 如果 user_id 是 Telegram chat_id，直接发送
                # 否则发送到默认 chat_id
                try:
                    chat_id = user_id if user_id.isdigit() else os.getenv("TELEGRAM_CHAT_ID")
                    if chat_id:
                        send_telegram_message(message, chat_id=chat_id)
                        print(f"[Success] 已发送提醒通知到 {chat_id}")
                except Exception as e:
                    print(f"[Error] 发送 Telegram 通知失败: {str(e)}")
        
        except Exception as e:
            print(f"[Error] 检查用户 {user_id} 的提醒时出错: {str(e)}")

def main():
    """主循环"""
    print("[Start] 提醒检查服务已启动")
    print(f"[Info] 检查间隔: 5 分钟")
    
    while True:
        try:
            print(f"\n[Check] {time.strftime('%Y-%m-%d %H:%M:%S')} 开始检查提醒...")
            check_all_alerts()
            print("[Done] 检查完成")
        except Exception as e:
            print(f"[Error] 检查过程出错: {str(e)}")
        
        # 等待 5 分钟
        time.sleep(300)

if __name__ == "__main__":
    main()
