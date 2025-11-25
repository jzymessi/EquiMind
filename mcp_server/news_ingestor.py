import hashlib
import os
from datetime import datetime, timezone
from typing import Dict, List

import feedparser
import requests

from .state_store import append_news_event


DEFAULT_SOURCES = {
    "yahoo": "https://finance.yahoo.com/news/rssindex",
    "nasdaq": "https://www.nasdaq.com/feed/rssoutbound",
    "seekingalpha": "https://seekingalpha.com/market_currents.xml",
    "sec": "https://www.sec.gov/news/pressreleases.rss",
}


def _parse_sources_from_env() -> Dict[str, str]:
    env_val = os.getenv("NEWS_RSS_SOURCES", "yahoo,nasdaq,seekingalpha,sec")
    selected = [s.strip().lower() for s in env_val.split(",") if s.strip()]
    return {k: v for k, v in DEFAULT_SOURCES.items() if k in selected}


def _dedup_key(title: str, link: str) -> str:
    raw = f"{title.strip()}|{link.strip()}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def ingest_once() -> List[Dict]:
    sources = _parse_sources_from_env()
    collected: List[Dict] = []

    for source_name, url in sources.items():
        print(f"[新闻拉取] 正在处理源: {source_name} ({url})")
        try:
            # 使用 requests 获取 RSS，设置超时和代理控制
            # 如果环境有代理问题，可以设置 NO_PROXY 或使用 requests 的 proxies 参数
            response = requests.get(url, timeout=10, proxies={"http": None, "https": None})
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except requests.exceptions.Timeout:
            print(f"[新闻拉取] 超时: {source_name}")
            continue
        except requests.exceptions.RequestException as e:
            print(f"[新闻拉取] 请求失败 {source_name}: {e}")
            continue
        except Exception as e:
            print(f"[新闻拉取] 解析失败 {source_name}: {e}")
            continue
        
        print(f"[新闻拉取] {source_name} 获取到 {len(feed.entries)} 条条目")
        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue
            published = entry.get("published", "") or entry.get("updated", "")
            try:
                # Normalize to ISO8601
                published_dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat() if hasattr(entry, "published_parsed") else datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
            except Exception:
                published_dt = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

            dedup = _dedup_key(title, link)
            event = {
                "title": title,
                "summary": entry.get("summary", "")[:500],
                "links": [link],
                "source": source_name,
                "published_at": published_dt,
                "tickers": [],  # 可后续通过简单规则或实体识别填充
                "event_type": "news",
                "severity": "normal",
                "heat_score": 1,
                "impact_summary": "",
                "confidence": 0.5,
                "dedup_key": dedup,
            }
            append_news_event(event)
            collected.append(event)
    
    print(f"[新闻拉取] 完成，共收集 {len(collected)} 条新闻")
    return collected


