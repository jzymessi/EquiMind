"""
漏斗选股策略 - 纯策略逻辑，不依赖数据获取
"""
from typing import Dict, Any, List
from dataclasses import dataclass
from ..data_providers.stock_data_provider import StockDataProvider, StockBasicInfo, FinancialData
from ..data_providers.technical_data_provider import TechnicalDataProvider, TechnicalIndicators

@dataclass
class StrategyResult:
    """策略分析结果"""
    symbol: str
    action: str  # 'buy', 'sell', 'hold', 'skip'
    confidence: float  # 0-1
    reason: str
    details: Dict[str, Any]

class FunnelStrategy:
    """三张王牌 + 两根线漏斗策略"""
    
    def __init__(self):
        self.stock_provider = StockDataProvider()
        self.tech_provider = TechnicalDataProvider()
        
        # 策略参数
        self.min_revenue_growth = 18.0
        self.min_earnings_growth = 18.0
        self.min_price = 10.0
        self.min_market_cap = 20e9
        self.rsi_range = (38, 55)
        self.sma50_tolerance = 0.08  # 8%
    
    def analyze_single(self, symbol: str) -> StrategyResult:
        """分析单只股票"""
        # 1. 获取基础信息
        basic_info = self.stock_provider.get_basic_info(symbol)
        if not basic_info:
            return StrategyResult(
                symbol=symbol,
                action='skip',
                confidence=0.0,
                reason='无法获取基础数据',
                details={}
            )
        
        # 2. 基础筛选
        if basic_info.price < self.min_price or basic_info.market_cap < self.min_market_cap:
            return StrategyResult(
                symbol=symbol,
                action='skip',
                confidence=0.0,
                reason=f'仙股或市值过小 (价格: ${basic_info.price:.2f}, 市值: {basic_info.market_cap/1e9:.1f}B)',
                details={'price': basic_info.price, 'market_cap': basic_info.market_cap}
            )
        
        # 3. 获取财务数据
        financial_data = self.stock_provider.get_financial_data(symbol)
        if not financial_data:
            return StrategyResult(
                symbol=symbol,
                action='skip',
                confidence=0.0,
                reason='财务数据不足',
                details={'price': basic_info.price}
            )
        
        # 4. 三张王牌检查
        moat_result = self._check_three_cards(financial_data)
        if not moat_result['pass']:
            return StrategyResult(
                symbol=symbol,
                action='hold',
                confidence=0.3,
                reason=f"未过三张王牌: {moat_result['reason']}",
                details={
                    'price': basic_info.price,
                    'revenue_growth': financial_data.revenue_growth,
                    'earnings_growth': financial_data.earnings_growth,
                    'fcf_positive': financial_data.fcf_positive,
                    'fcf_growth': financial_data.fcf_growth
                }
            )
        
        # 5. 获取技术指标
        hist_data = self.stock_provider.get_historical_data(symbol)
        if hist_data is None:
            return StrategyResult(
                symbol=symbol,
                action='hold',
                confidence=0.5,
                reason='基本面优秀，但无法获取技术数据',
                details={'price': basic_info.price}
            )
        
        tech_indicators = self.tech_provider.get_technical_indicators(hist_data)
        if not tech_indicators:
            return StrategyResult(
                symbol=symbol,
                action='hold',
                confidence=0.5,
                reason='基本面优秀，但技术指标计算失败',
                details={'price': basic_info.price}
            )
        
        # 6. 两根线择时
        timing_result = self._check_timing(tech_indicators)
        
        return self._generate_final_result(symbol, basic_info, financial_data, tech_indicators, timing_result)
    
    def scan_all(self, tickers: List[str]) -> List[StrategyResult]:
        """扫描股票池"""
        results = []
        for ticker in tickers:
            result = self.analyze_single(ticker)
            results.append(result)
        
        # 按买入信号和置信度排序
        buy_signals = [r for r in results if r.action == 'buy']
        buy_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return buy_signals[:5] if buy_signals else results[:5]
    
    def _check_three_cards(self, financial_data: FinancialData) -> Dict[str, Any]:
        """检查三张王牌"""
        reasons = []
        
        # 增长引擎
        moat_pass = (
            financial_data.revenue_growth > self.min_revenue_growth and 
            financial_data.earnings_growth > self.min_earnings_growth
        )
        
        if financial_data.revenue_growth <= self.min_revenue_growth:
            reasons.append(f"营收增长{financial_data.revenue_growth:.1f}%<{self.min_revenue_growth}%")
        if financial_data.earnings_growth <= self.min_earnings_growth:
            reasons.append(f"EPS增长{financial_data.earnings_growth:.1f}%<{self.min_earnings_growth}%")
        
        # 现金流
        blood_pass = financial_data.fcf_positive and financial_data.fcf_growth
        if not financial_data.fcf_positive:
            reasons.append("自由现金流为负")
        elif not financial_data.fcf_growth:
            reasons.append("自由现金流未增长")
        
        return {
            'pass': moat_pass and blood_pass,
            'moat_pass': moat_pass,
            'blood_pass': blood_pass,
            'reason': ", ".join(reasons) if reasons else "三张王牌全过"
        }
    
    def _check_timing(self, indicators: TechnicalIndicators) -> Dict[str, Any]:
        """检查两根线择时"""
        trend_pass = indicators.price > indicators.sma200
        timing_pass = (
            0.92 * indicators.sma50 <= indicators.price <= 1.08 * indicators.sma50
        ) and (self.rsi_range[0] <= indicators.rsi <= self.rsi_range[1])
        
        return {
            'trend_pass': trend_pass,
            'timing_pass': timing_pass,
            'rsi': indicators.rsi,
            'sma50_distance': (indicators.price / indicators.sma50 - 1) * 100
        }
    
    def _generate_final_result(self, symbol: str, basic_info: StockBasicInfo, 
                             financial_data: FinancialData, tech_indicators: TechnicalIndicators,
                             timing_result: Dict[str, Any]) -> StrategyResult:
        """生成最终结果"""
        price = basic_info.price
        
        if timing_result['trend_pass'] and timing_result['timing_pass']:
            return StrategyResult(
                symbol=symbol,
                action='buy',
                confidence=0.9,
                reason=f"🟢 强烈推荐买入！RSI: {timing_result['rsi']:.1f}, 距50SMA: {timing_result['sma50_distance']:.1f}%, 超200SMA。三张王牌全过，技术面处于黄金买点。",
                details={
                    'price': price,
                    'rsi': timing_result['rsi'],
                    'sma50_distance': timing_result['sma50_distance']
                }
            )
        elif not timing_result['trend_pass']:
            return StrategyResult(
                symbol=symbol,
                action='sell',
                confidence=0.8,
                reason=f"🔴 建议卖出防御。趋势破坏（低于200日均线）。RSI: {timing_result['rsi']:.1f}",
                details={
                    'price': price,
                    'rsi': timing_result['rsi']
                }
            )
        else:
            return StrategyResult(
                symbol=symbol,
                action='hold',
                confidence=0.6,
                reason=f"🟡 观望为主。基本面优秀但非黄金买点。RSI: {timing_result['rsi']:.1f}（理想区间: {self.rsi_range[0]}-{self.rsi_range[1]}）。",
                details={
                    'price': price,
                    'rsi': timing_result['rsi']
                }
            )
