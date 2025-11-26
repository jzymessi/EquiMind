"""
股票数据提供者 - 负责获取股票的基础数据和财务数据
"""
import yfinance as yf
import pandas as pd
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass
class StockBasicInfo:
    """股票基础信息"""
    symbol: str
    price: float
    market_cap: float
    currency: str
    
@dataclass
class FinancialData:
    """财务数据"""
    revenue_series: pd.Series
    earnings_series: pd.Series
    fcf_series: pd.Series
    revenue_growth: float
    earnings_growth: float
    fcf_positive: bool
    fcf_growth: bool

class StockDataProvider:
    """股票数据提供者"""
    
    def get_basic_info(self, symbol: str) -> Optional[StockBasicInfo]:
        """获取股票基础信息"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if hist.empty:
                return None
                
            info = ticker.info
            price = hist['Close'].iloc[-1]
            market_cap = info.get('marketCap', 0)
            
            return StockBasicInfo(
                symbol=symbol,
                price=float(price),
                market_cap=market_cap,
                currency=info.get('currency', 'USD')
            )
        except Exception as e:
            print(f"获取 {symbol} 基础信息失败: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
        """获取历史价格数据"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            return hist if not hist.empty else None
        except Exception as e:
            print(f"获取 {symbol} 历史数据失败: {e}")
            return None
    
    def get_financial_data(self, symbol: str) -> Optional[FinancialData]:
        """获取财务数据并计算增长率"""
        try:
            ticker = yf.Ticker(symbol)
            
            # 获取财务报表
            quarterly_fin = ticker.quarterly_financials
            quarterly_earn = ticker.quarterly_earnings
            quarterly_cf = ticker.quarterly_cashflow
            
            # 安全检查和数据提取
            revenue_series = self._extract_series(quarterly_fin, 'Total Revenue', symbol)
            if revenue_series is None:
                return None
                
            earnings_series = self._extract_earnings_series(ticker, quarterly_earn, symbol)
            if earnings_series is None:
                return None
                
            fcf_series = self._extract_series(quarterly_cf, 'Free Cash Flow', symbol)
            if fcf_series is None:
                return None
            
            # 计算增长率
            revenue_growth = self._calc_growth(revenue_series.iloc[:2])
            earnings_growth = self._calc_growth(earnings_series.iloc[:2])
            
            # 现金流分析
            fcf_positive = fcf_series.iloc[0] > 0  # 最新季度为正
            fcf_growth = fcf_series.pct_change().iloc[1] > 0 if len(fcf_series) > 1 else False
            
            return FinancialData(
                revenue_series=revenue_series,
                earnings_series=earnings_series,
                fcf_series=fcf_series,
                revenue_growth=revenue_growth,
                earnings_growth=earnings_growth,
                fcf_positive=fcf_positive,
                fcf_growth=fcf_growth
            )
            
        except Exception as e:
            print(f"获取 {symbol} 财务数据失败: {e}")
            return None
    
    def _extract_series(self, dataframe, field_name: str, symbol: str) -> Optional[pd.Series]:
        """安全提取数据序列"""
        if dataframe is None or dataframe.empty or field_name not in dataframe.index:
            print(f"{symbol}: 缺失 {field_name} 数据")
            return None
            
        series = dataframe.loc[field_name].dropna()
        if len(series) < 2:
            print(f"{symbol}: {field_name} 数据不足(<2季度)")
            return None
            
        return series
    
    def _extract_earnings_series(self, ticker, quarterly_earn, symbol: str) -> Optional[pd.Series]:
        """提取盈利数据，兼容新旧API"""
        # 尝试从 quarterly_earnings 获取
        if quarterly_earn is not None and not quarterly_earn.empty and 'Earnings' in quarterly_earn.columns:
            series = quarterly_earn['Earnings'].dropna()
            if len(series) >= 2:
                return series
        
        # 尝试从 income_stmt 获取净利润
        try:
            income_stmt = ticker.quarterly_income_stmt
            if income_stmt is not None and not income_stmt.empty and 'Net Income' in income_stmt.index:
                series = income_stmt.loc['Net Income'].dropna()
                if len(series) >= 2:
                    return series
        except:
            pass
            
        print(f"{symbol}: 无法获取盈利数据")
        return None
    
    def _calc_growth(self, series: pd.Series) -> float:
        """计算增长率"""
        if len(series) < 2 or series.iloc[-1] == 0:
            return -999
        # yfinance 财务数据：iloc[0] 是最新季度，iloc[-1] 是最老季度
        return (series.iloc[0] / series.iloc[-1] - 1) * 100
