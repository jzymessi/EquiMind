import asyncio
from pathlib import Path
import sys

from dotenv import load_dotenv

# 确保项目根目录在 sys.path 中
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# 加载 .env 环境变量（包括 TELEGRAM_CHAT_ID、NEWS_* 等）
load_dotenv()

from mcp_server.scheduler import start_scheduler  # noqa: E402


def main() -> None:
    """独立运行的定时任务进程，用于晨报/晚报推送等。

    说明：
    - 使用 AsyncIOScheduler，需要一个事件循环常驻运行；
    - 原来由 FastAPI/uvicorn 提供事件循环，现在在这里手动创建。
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 启动所有定时任务（新闻抓取 + 晨报 + 晚报）
    start_scheduler()

    try:
        # 让事件循环一直运行，直到手动 Ctrl+C
        loop.run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
