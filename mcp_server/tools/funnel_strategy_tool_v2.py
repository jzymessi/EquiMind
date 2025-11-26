"""
重构后的漏斗策略工具 - 使用分层架构
"""
from langchain.tools import BaseTool
from typing import List, Dict, Any
from .strategies.funnel_strategy import FunnelStrategy

# 扩展白名单（行业龙头）
MOAT_TICKERS = [
    "NVDA", "AMD", "TSM", "ASML", "AVGO", "QCOM",  # 半导体
    "MSFT", "AMZN", "GOOGL", "META", "ORCL", "SNOW", "CRM",  # 云/AI
    "AAPL", "TSLA", "MCD", "SBUX", "KO", "JNJ", "PG", "COST", "WMT", "HD",  # 消费/现金牛
    "V", "MA", "PYPL", "SOFI"  # 金融
]

class FunnelStrategyToolV2(BaseTool):
    name = "funnel_stock_strategy_v2"
    description = "执行'三张王牌 + 两根线'漏斗选股策略（重构版）。输入：mode ('scan' 全扫描, 'check' 单股如 NVDA), symbol (可选)。输出：详细的买/卖/观望建议。"

    def __init__(self):
        super().__init__()
        # 使用 object.__setattr__ 绕过 Pydantic 限制
        object.__setattr__(self, 'strategy', FunnelStrategy())

    def _run(self, mode: str = "scan", symbol: str = None) -> str:
        try:
            # 懒加载策略对象
            if not hasattr(self, 'strategy'):
                object.__setattr__(self, 'strategy', FunnelStrategy())
                
            if mode == "check" and symbol:
                result = self.strategy.analyze_single(symbol.upper())
                return self._format_single_result(result)
            else:
                results = self.strategy.scan_all(MOAT_TICKERS)
                return self._format_scan_results(results)
        except Exception as e:
            return f"执行错误：{str(e)}"

    def _format_single_result(self, result) -> str:
        """格式化单股分析结果"""
        price_info = f"${result.details.get('price', 0):.2f}" if 'price' in result.details else ""
        
        if result.action == 'skip':
            return f"{result.symbol} {price_info}: ⚪ {result.reason}"
        
        return f"{result.symbol} {price_info}: {result.reason}"

    def _format_scan_results(self, results) -> str:
        """格式化扫描结果"""
        if not results:
            return "今日无黄金买点，建议持现金。"
        
        buy_signals = [r for r in results if r.action == 'buy']
        if buy_signals:
            lines = [f"🎯 发现 {len(buy_signals)} 个黄金买点：\n"]
            for i, result in enumerate(buy_signals, 1):
                lines.append(f"{i}. {self._format_single_result(result)}")
            return "\n".join(lines)
        else:
            lines = [f"📊 扫描完成，暂无买入信号。前5个观察标的：\n"]
            for i, result in enumerate(results[:5], 1):
                lines.append(f"{i}. {self._format_single_result(result)}")
            return "\n".join(lines)

    def _arun(self, **kwargs):
        raise NotImplementedError("异步暂不支持")
