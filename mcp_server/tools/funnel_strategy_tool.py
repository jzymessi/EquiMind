# mcp_server/tools/funnel_strategy_tool.py
import yfinance as yf
import pandas_ta as ta
import pandas as pd
from langchain.tools import BaseTool
from typing import List, Dict, Any

# 扩展白名单（行业龙头，基于您的例子）
MOAT_TICKERS = {
    "NVDA", "AMD", "TSM", "ASML", "AVGO", "QCOM",  # 半导体
    "MSFT", "AMZN", "GOOGL", "META", "ORCL", "SNOW", "CRM",  # 云/AI
    "AAPL", "TSLA", "MCD", "SBUX", "KO", "JNJ", "PG", "COST", "WMT", "HD",  # 消费/现金牛
    "V", "MA", "PYPL", "SOFI"  # 金融
}

class FunnelStrategyTool(BaseTool):
    name = "funnel_stock_strategy"
    description = "执行‘三张王牌 + 两根线 + 两个理由’漏斗：数据用 yfinance 免费获取，计算营收/EPS/FCF/RSI/SMA。输入：mode ('scan' 全扫描, 'check' 单股如 NVDA), symbol (可选)。输出：买/卖信号。"

    def _run(self, mode: str = "scan", symbol: str = None) -> str:
        try:
            if mode == "check" and symbol:
                return self._check_single(symbol)
            else:
                return self._scan_all()
        except Exception as e:
            return f"执行错误：{str(e)}"

    def _scan_all(self) -> str:
        candidates = []
        for sym in MOAT_TICKERS:
            result = self._check_single(sym)
            if "买入" in result:
                candidates.append(result)
        if not candidates:
            return "今日无黄金买点，建议持现金。"
        # 按 RSI 排序
        candidates.sort(key=lambda x: float(x.split("RSI: ")[1].split()[0]))
        return "\n".join(candidates[:5])

    def _check_single(self, symbol: str) -> str:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2y")
        if hist.empty or len(hist) < 250:
            return f"{symbol}: 数据不足，跳过。"

        info = ticker.info
        price = hist['Close'].iloc[-1]
        if price < 10 or info.get('marketCap', 0) < 20e9:
            return f"{symbol}: 仙股，排除。"

        # ===== 第一步：三张王牌（用 yfinance 财务数据）=====
        quarterly_fin = ticker.quarterly_financials
        quarterly_earn = ticker.quarterly_earnings
        quarterly_cf = ticker.quarterly_cashflow

        # 增长引擎：营收/EPS 近两季 >18%
        rev_growth = self._calc_growth(quarterly_fin.loc['Total Revenue'].iloc[:2])
        eps_growth = self._calc_growth(quarterly_earn['Earnings'].iloc[:2])
        moat_pass = rev_growth > 18 and eps_growth > 18

        # 自由现金流：正且增长
        fcf = quarterly_cf.loc['Free Cash Flow'].iloc[:4]
        fcf_positive = fcf.iloc[-1] > 0
        fcf_growth = fcf.pct_change().iloc[-1] > 0 if len(fcf) > 1 else False
        blood_pass = fcf_positive and fcf_growth

        if not (moat_pass and blood_pass):
            return f"{symbol}: 未过三张王牌 (营收↑{rev_growth:.1f}%, EPS↑{eps_growth:.1f}%, FCF正? {fcf_positive})"

        # ===== 第二步：两根线择时（pandas_ta 计算）=====
        sma200 = ta.sma(hist['Close'], length=200).iloc[-1]
        sma50 = ta.sma(hist['Close'], length=50).iloc[-1]
        rsi = ta.rsi(hist['Close'], length=14).iloc[-1]

        trend_pass = price > sma200  # 牛市
        timing_pass = (0.92 * sma50 <= price <= 1.08 * sma50) and (38 <= rsi <= 55)

        if trend_pass and timing_pass:
            return f"{symbol} ${price:.2f}: 买入！RSI: {rsi:.1f}, 距50SMA: {(price/sma50-1)*100:.1f}%, >200SMA: 是。三张王牌全过。"
        elif not trend_pass:
            return f"{symbol}: 趋势破坏 (<200SMA)，卖出防御。"
        else:
            return f"{symbol}: 好股但非黄金时点 (RSI {rsi:.1f} 非40-50) ，观望。"

    def _calc_growth(self, series: pd.Series) -> float:
        if len(series) < 2 or series.iloc[-1] == 0:
            return -999
        # yfinance 财务数据：iloc[0] 是最新季度，iloc[-1] 是最老季度
        # 计算从老到新的增长率：(最新 / 最老 - 1) * 100
        return (series.iloc[0] / series.iloc[-1] - 1) * 100

    def _arun(self, **kwargs):
        raise NotImplementedError("异步暂不支持")