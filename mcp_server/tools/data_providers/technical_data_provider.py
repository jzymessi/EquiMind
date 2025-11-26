"""
技术指标数据提供者
"""
import pandas as pd
import pandas_ta as ta
from typing import Optional, Dict
from dataclasses import dataclass

@dataclass
class TechnicalIndicators:
    """技术指标数据"""
    sma200: float
    sma50: float
    rsi: float
    price: float
    
    def is_valid(self) -> bool:
        """检查指标是否有效"""
        return not (pd.isna(self.sma200) or pd.isna(self.sma50) or pd.isna(self.rsi))

class TechnicalDataProvider:
    """技术指标数据提供者"""
    
    def get_technical_indicators(self, hist_data: pd.DataFrame) -> Optional[TechnicalIndicators]:
        """计算技术指标"""
        try:
            if hist_data is None or hist_data.empty or len(hist_data) < 250:
                return None
                
            price = hist_data['Close'].iloc[-1]
            
            # 计算技术指标
            sma200 = ta.sma(hist_data['Close'], length=200).iloc[-1]
            sma50 = ta.sma(hist_data['Close'], length=50).iloc[-1]
            rsi = ta.rsi(hist_data['Close'], length=14).iloc[-1]
            
            indicators = TechnicalIndicators(
                sma200=sma200,
                sma50=sma50,
                rsi=rsi,
                price=price
            )
            
            return indicators if indicators.is_valid() else None
            
        except Exception as e:
            print(f"技术指标计算失败: {e}")
            return None
    
    def analyze_trend(self, indicators: TechnicalIndicators) -> Dict[str, bool]:
        """分析趋势"""
        return {
            'trend_pass': indicators.price > indicators.sma200,  # 牛市
            'timing_pass': (
                0.92 * indicators.sma50 <= indicators.price <= 1.08 * indicators.sma50
            ) and (38 <= indicators.rsi <= 55)
        }
