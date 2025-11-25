import os
from datetime import datetime
from typing import List, Dict
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .news_ingestor import ingest_once
from .telegram_bot import get_default_chat_id, send_telegram_message
from .state_store import get_alert_rules, read_latest_news, get_watchlist

scheduler = AsyncIOScheduler()


def _format_digest(news_items: List[Dict], max_items: int = 10) -> str:
    """格式化新闻摘要为推送文本"""
    if not news_items:
        return "今日暂无重要新闻"
    
    lines = [f"📰 今日新闻摘要（共 {len(news_items)} 条）\n"]
    for i, item in enumerate(news_items[:max_items], 1):
        title = item.get("title", "")[:80]
        source = item.get("source", "unknown")
        lines.append(f"{i}. {title} ({source})")
    
    if len(news_items) > max_items:
        lines.append(f"\n... 还有 {len(news_items) - max_items} 条新闻，请查看事件中心")
    
    return "\n".join(lines)


async def job_auto_ingest_news():
    """定时自动拉取新闻任务"""
    print(f"[定时任务] {datetime.now()} 开始自动拉取新闻...")
    try:
        items = ingest_once()
        print(f"[定时任务] 拉取完成，共 {len(items)} 条新闻")
    except Exception as e:
        print(f"[定时任务] 拉取失败: {e}")


async def job_morning_digest():
    """晨报推送任务"""
    print(f"[定时任务] {datetime.now()} 发送晨报...")
    try:
        # 获取最近24小时的新闻
        news_items = read_latest_news(limit=20)
        # 过滤最近24小时
        cutoff = datetime.utcnow().timestamp() - 86400
        recent = [
            item for item in news_items
            if item.get("published_at") and 
            datetime.fromisoformat(item["published_at"].replace("Z", "+00:00")).timestamp() > cutoff
        ]
        
        if recent:
            body = _format_digest(recent, max_items=10)
            digest_text = f"🌅 EquiMind 晨报\n\n{body}"
            chat_id = get_default_chat_id()
            if not chat_id:
                print("[定时任务] 未配置 TELEGRAM_CHAT_ID，跳过晨报推送")
                return
            result = send_telegram_message(chat_id, digest_text)
            if result.get("success"):
                print(f"[定时任务] 晨报已通过 Telegram 发送，包含 {len(recent)} 条新闻")
            else:
                print(f"[定时任务] 晨报发送失败: {result.get('error')}")
        else:
            print(f"[定时任务] 晨报：无新新闻，跳过推送")
    except Exception as e:
        print(f"[定时任务] 晨报发送失败: {e}")


async def job_evening_digest():
    """晚报推送任务"""
    print(f"[定时任务] {datetime.now()} 发送晚报...")
    try:
        # 获取最近12小时的新闻
        news_items = read_latest_news(limit=20)
        # 过滤最近12小时
        cutoff = datetime.utcnow().timestamp() - 43200
        recent = [
            item for item in news_items
            if item.get("published_at") and 
            datetime.fromisoformat(item["published_at"].replace("Z", "+00:00")).timestamp() > cutoff
        ]
        
        if recent:
            body = _format_digest(recent, max_items=10)
            digest_text = f"🌙 EquiMind 晚报\n\n{body}"
            chat_id = get_default_chat_id()
            if not chat_id:
                print("[定时任务] 未配置 TELEGRAM_CHAT_ID，跳过晚报推送")
                return
            result = send_telegram_message(chat_id, digest_text)
            if result.get("success"):
                print(f"[定时任务] 晚报已通过 Telegram 发送，包含 {len(recent)} 条新闻")
            else:
                print(f"[定时任务] 晚报发送失败: {result.get('error')}")
        else:
            print(f"[定时任务] 晚报：无新新闻，跳过推送")
    except Exception as e:
        print(f"[定时任务] 晚报发送失败: {e}")


def start_scheduler():
    """启动所有定时任务"""
    rules = get_alert_rules()
    
    # 自动拉取新闻（每 N 分钟）
    poll_interval = int(os.getenv("NEWS_POLL_INTERVAL_MIN", "10"))
    scheduler.add_job(
        job_auto_ingest_news,
        trigger=IntervalTrigger(minutes=poll_interval),
        id="auto_ingest_news",
        replace_existing=True,
    )
    print(f"[定时任务] 已启动自动拉取新闻任务（每 {poll_interval} 分钟）")
    
    # 晨报（固定时间）
    morning_time = rules.get("morning_digest_time", "08:30")
    hour, minute = map(int, morning_time.split(":"))
    scheduler.add_job(
        job_morning_digest,
        trigger=CronTrigger(hour=hour, minute=minute),
        id="morning_digest",
        replace_existing=True,
    )
    print(f"[定时任务] 已启动晨报任务（每天 {morning_time}）")
    
    # 晚报（固定时间）
    evening_time = rules.get("evening_digest_time", "20:00")
    hour, minute = map(int, evening_time.split(":"))
    scheduler.add_job(
        job_evening_digest,
        trigger=CronTrigger(hour=hour, minute=minute),
        id="evening_digest",
        replace_existing=True,
    )
    print(f"[定时任务] 已启动晚报任务（每天 {evening_time}）")
    
    scheduler.start()
    print("[定时任务] 所有定时任务已启动")


def stop_scheduler():
    """停止定时任务"""
    scheduler.shutdown()
    print("[定时任务] 定时任务已停止")

