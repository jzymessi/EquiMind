# mcp_server/tools/stock_funnel_strategy.py
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from typing import List, Dict, Any
from langchain.tools import BaseTool

# 手动维护的行业龙头白名单（后续可以扩展为自动判断）
MOAT_TICKERS = {
    # 半导体/显卡
    "NVDA", "AMD", "TSM", "ASML", "AVGO", "QCOM",
    # 云计算/大模型
    "MSFT", "AMZN", "GOOGL", "META", "ORCL", "SNOW", "CRM",
    # 消费/奢侈品
    "AAPL", "LVMUY", "HIMS", "TSLA", "MCD", "SBUX", "KO",
    # 支付/金融科技
    "V", "MA", "PYPL", "SOFI",
    # 其他现金奶牛
    "JNJ", "PG", "COST", "WMT", "HD"
}

class FunnelStrategyTool(BaseTool):
    name = "three_kings_two_lines_strategy"
    description = "执行‘三张王牌 + 两根线 + 两个理由’漏斗选股系统，返回今日可扣扳机的股票列表（免费 yfinance 实现）"

    def _run(self, market: str = "US") -> str:
        candidates = []
        total = len(MOAT_TICKERS)
        
        for i, symbol in enumerate(MOAT_TICKERS, 1):
            try:
                print(f"[{i}/{total}] 扫描 {symbol}...")
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="2y")
                if hist.empty or len(hist) < 250:
                    continue
                    
                info = ticker.info
                price = hist['Close'].iloc[-1]
                if price < 10 or info.get('marketCap', 0) < 20e9:
                    continue  # 排除仙股

                # ===== 第一步：三张王牌 =====
                # 1. 护城河 → 白名单已保证
                # 2. 增长引擎
                revenue_growth = self._get_growth_rate(ticker.quarterly_financials, "Total Revenue")
                eps_growth = self._get_growth_rate(ticker.quarterly_earnings, "Earnings")
                if not (revenue_growth > 18 and eps_growth > 18):
                    continue

                # 3. 自由现金流（血）
                fcf = ticker.quarterly_cashflow.loc["Free Cash Flow"].iloc[:4]  # 最近4季
                if fcf.iloc[-1] <= 0 or fcf.pct_change().iloc[-1] < 0:
                    continue

                # ===== 第二步：两根线择时 =====
                sma200 = hist['Close'].rolling(200).mean().iloc[-1]
                sma50 = hist['Close'].rolling(50).mean().iloc[-1]
                rsi = ta.rsi(hist['Close'], length=14).iloc[-1]

                if not (price > sma200):  # 必须在牛市区域
                    continue
                if not (38 <= rsi <= 55):  # 回调但不过度超卖
                    continue
                if not (0.92 * sma50 <= price <= 1.08 * sma50):  # 回踩50日线 ±8%
                    continue

                # ===== 全部通过！=====
                candidates.append({
                    "symbol": symbol,
                    "price": round(price, 2),
                    "rsi": round(rsi, 1),
                    "distance_to_50sma": round((price / sma50 - 1) * 100, 1),
                    "revenue_growth": round(revenue_growth, 1),
                    "eps_growth": round(eps_growth, 1),
                    "reason": "三张王牌全满足 + 牛市回调至50日线 + RSI黄金区"
                })
            except Exception as e:
                continue

        if not candidates:
            return "今日无完全符合‘三张王牌 + 两根线’黄金买点的股票，保持现金是最优解。"
        
        # 按 RSI 从低到高排序（越低越好）
        candidates.sort(key=lambda x: x["rsi"])
        result = "今日可扣扳机的股票（严格漏斗系统）:\n\n"
        for c in candidates[:5]:
            result += f"• {c['symbol']}  ${c['price']}  RSI {c['rsi']}  距50日线 {c['distance_to_50sma']}%  营收↑{c['revenue_growth']}%  EPS↑{c['eps_growth']}%\n  → {c['reason']}\n\n"
        return result

    def _get_growth_rate(self, df, column) -> float:
        if df is None or column not in df.index:
            return -999
        recent = df.loc[column].iloc[:2]  # 最近两季
        if len(recent) < 2 or recent.iloc[1] == 0:
            return -999
        return (recent.iloc[0] / recent.iloc[1] - 1) * 100

    def _arun(self, **kwargs):
        raise NotImplementedError