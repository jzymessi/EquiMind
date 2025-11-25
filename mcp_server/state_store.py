import json
import os
from typing import Any, Dict, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

WATCHLIST_FILE = os.path.join(DATA_DIR, "watchlist.json")
ALERT_RULES_FILE = os.path.join(DATA_DIR, "alert_rules.json")
NEWS_EVENTS_FILE = os.path.join(DATA_DIR, "news_events.jsonl")


def _read_json(path: str, default: Any):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _write_json(path: str, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_watchlist() -> List[str]:
    return _read_json(WATCHLIST_FILE, [])


def set_watchlist(symbols: List[str]) -> List[str]:
    unique = sorted(list({s.upper() for s in symbols if isinstance(s, str) and s.strip()}))
    _write_json(WATCHLIST_FILE, unique)
    return unique


def get_alert_rules() -> Dict[str, Any]:
    default_rules = {
        "price_change_pct_normal": 3.0,
        "price_change_pct_severe": 5.0,
        "quiet_hours": os.getenv("NOTIFY_QUIET_HOURS", "23:00-07:00"),
        "cooldown_min": int(os.getenv("NOTIFY_COOLDOWN_MIN", "30")),
        "morning_digest_time": os.getenv("MORNING_DIGEST_TIME", "08:30"),
        "evening_digest_time": os.getenv("EVENING_DIGEST_TIME", "20:00"),
    }
    rules = _read_json(ALERT_RULES_FILE, {})
    return {**default_rules, **rules}


def set_alert_rules(rules: Dict[str, Any]) -> Dict[str, Any]:
    current = _read_json(ALERT_RULES_FILE, {})
    current.update(rules or {})
    _write_json(ALERT_RULES_FILE, current)
    return get_alert_rules()


def append_news_event(event: Dict[str, Any]) -> None:
    with open(NEWS_EVENTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def read_latest_news(limit: int = 50) -> List[Dict[str, Any]]:
    if not os.path.exists(NEWS_EVENTS_FILE):
        return []
    items: List[Dict[str, Any]] = []
    with open(NEWS_EVENTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    items.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    return items[:limit]


