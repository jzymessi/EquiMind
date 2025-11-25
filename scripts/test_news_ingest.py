#!/usr/bin/env python3
"""
测试新闻抓取功能
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from mcp_server.news_ingestor import ingest_once
from mcp_server.state_store import read_latest_news

def main():
    print("=" * 60)
    print("开始测试新闻抓取功能...")
    print("=" * 60)
    
    # 1. 测试新闻抓取
    print("\n【步骤 1】调用 ingest_once() 抓取新闻...")
    try:
        collected = ingest_once()
        print(f"✅ 成功抓取 {len(collected)} 条新闻")
        
        # 显示前 3 条新闻样本
        if collected:
            print("\n【新闻样本】前 3 条：")
            for i, item in enumerate(collected[:3], 1):
                print(f"\n{i}. {item['title'][:60]}...")
                print(f"   来源: {item['source']}")
                print(f"   链接: {item['links'][0][:50]}...")
                print(f"   发布时间: {item['published_at']}")
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 2. 测试从存储读取
    print("\n" + "=" * 60)
    print("【步骤 2】从 state_store 读取最新新闻...")
    try:
        latest = read_latest_news(limit=5)
        print(f"✅ 从存储读取到 {len(latest)} 条新闻")
        
        if latest:
            print("\n【存储中的新闻】最新 5 条：")
            for i, item in enumerate(latest, 1):
                print(f"{i}. {item['title'][:60]}... ({item['source']})")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()
