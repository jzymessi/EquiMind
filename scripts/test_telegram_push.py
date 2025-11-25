#!/usr/bin/env python3
"""
立即测试 Telegram 推送功能（晨报/晚报）
"""
import sys
import os
import asyncio

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from mcp_server.news_ingestor import ingest_once
from mcp_server.scheduler import job_morning_digest, job_evening_digest, _format_digest
from mcp_server.state_store import read_latest_news
from mcp_server.telegram_bot import send_telegram_message, get_default_chat_id

async def test_immediate_push():
    print("=" * 60)
    print("立即测试 Telegram 推送功能")
    print("=" * 60)
    
    # 1. 检查 Telegram 配置
    chat_id = get_default_chat_id()
    if not chat_id:
        print("❌ 错误：未配置 TELEGRAM_CHAT_ID")
        print("请在 .env 中设置 TELEGRAM_CHAT_ID")
        return
    
    print(f"✅ Telegram Chat ID: {chat_id}")
    
    # 2. 测试基础消息推送
    print("\n【测试 1】发送测试消息...")
    test_msg = "🧪 EquiMind 推送功能测试\n\n这是一条测试消息，用于验证 Telegram 推送是否正常工作。"
    result = send_telegram_message(chat_id, test_msg)
    
    if result.get("success"):
        print("✅ 测试消息发送成功！请检查你的 Telegram")
    else:
        print(f"❌ 测试消息发送失败: {result.get('error')}")
        return
    
    # 3. 抓取新闻
    print("\n【测试 2】抓取最新新闻...")
    try:
        collected = ingest_once()
        print(f"✅ 成功抓取 {len(collected)} 条新闻")
    except Exception as e:
        print(f"❌ 新闻抓取失败: {e}")
        collected = []
    
    # 4. 测试晨报推送
    print("\n【测试 3】发送晨报格式推送...")
    await job_morning_digest()
    
    # 等待 2 秒
    await asyncio.sleep(2)
    
    # 5. 测试晚报推送
    print("\n【测试 4】发送晚报格式推送...")
    await job_evening_digest()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！请检查你的 Telegram 是否收到：")
    print("   1. 测试消息")
    print("   2. 晨报推送")
    print("   3. 晚报推送")
    print("=" * 60)

def test_news_format():
    """测试新闻格式化（不发送）"""
    print("\n【额外测试】新闻格式化预览...")
    try:
        news_items = read_latest_news(limit=10)
        if news_items:
            formatted = _format_digest(news_items, max_items=5)
            print("\n" + "=" * 60)
            print("【晨报预览】")
            print("=" * 60)
            print(f"🌅 EquiMind 晨报\n\n{formatted}")
            print("=" * 60)
        else:
            print("⚠️  当前没有新闻数据，请先运行新闻抓取")
    except Exception as e:
        print(f"❌ 格式化失败: {e}")

if __name__ == "__main__":
    # 先预览格式
    test_news_format()
    
    print("\n\n是否立即发送推送到 Telegram？")
    print("按 Enter 继续，Ctrl+C 取消...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n已取消")
        sys.exit(0)
    
    # 执行推送测试
    asyncio.run(test_immediate_push())
