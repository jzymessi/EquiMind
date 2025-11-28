import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# 先加载 .env 中的环境变量，确保本地 LLM 与 Telegram 配置生效
load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcp_server.telegram_bot import handle_telegram_update, _get_bot_token

TELEGRAM_API_BASE = "https://api.telegram.org"


def fetch_updates(token: str, offset: int | None) -> dict:
    params = {"timeout": 30}
    if offset is not None:
        params["offset"] = offset
    resp = requests.get(
        f"{TELEGRAM_API_BASE}/bot{token}/getUpdates",
        params=params,
        timeout=35,
    )
    # 检查HTTP响应状态码
    resp.raise_for_status() 
    return resp.json()


def main():
    token = _get_bot_token()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 未配置")

    offset = None
    while True:
        try:
            data = fetch_updates(token, offset)
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                result = handle_telegram_update(update)
                if not result.get("success", True):
                    print(f"[Polling] 处理失败: {result.get('error')}")
        except requests.RequestException as exc:
            print(f"[Polling] 网络错误: {exc}")
            time.sleep(5)
        except Exception as exc:
            print(f"[Polling] 未知错误: {exc}")
            time.sleep(1)

        # 可以视情况加一点休眠避免过于频繁
        time.sleep(0.5)


if __name__ == "__main__":
    main()