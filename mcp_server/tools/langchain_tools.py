import pandas as pd
import requests
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from config import ALPHAVANTAGE_API_KEY
from langchain.tools import BaseTool
import yfinance as yf

# S&P500部分科技股列表
SP500_TECH_SYMBOLS = [
    "AAPL", "MSFT", "GOOG", "NVDA", "AMD"
]

def fetch_daily(symbol: str) -> Optional[pd.DataFrame]:
    """用 yfinance 获取股票日线数据，兼容多重列名"""
    try:
        df = yf.download(symbol, period="3mo", interval="1d", progress=False)
        print(f"{symbol} 原始列名: {df.columns}")
        if df is None or df.empty:
            print(f"{symbol} yfinance: empty DataFrame")
            return None
        # 如果是 MultiIndex，扁平化为单层
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        print(f"{symbol} 扁平化后列名: {df.columns}")
        df = df.reset_index()
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
        df.index = pd.Index([d.normalize() if isinstance(d, pd.Timestamp) else pd.to_datetime(d).normalize() for d in df.index])
        # 检查必要列
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"{symbol} 缺少必要列: {missing_columns}")
            return None
        print(f"{symbol} 所有必要列都存在")
        return df
    except Exception as e:
        print(f"{symbol} yfinance error: {e}")
        return None

def fetch_overview(symbol: str) -> Optional[Dict]:
    """用 yfinance 获取公司基本面信息"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return info if info else None
    except Exception as e:
        print(f"{symbol} yfinance overview error: {e}")
        return None

def calc_return(df: pd.DataFrame, days: int = 5) -> Optional[float]:
    """计算涨幅"""
    if len(df) < days:
        return None
    return (df['Close'].iloc[-1] - df['Close'].iloc[-days]) / df['Close'].iloc[-days]

class SmartStockScreeningInput(BaseModel):
    symbols: Optional[List[str]] = Field(
        default=None, 
        description="股票代码列表，为空时使用默认科技股池"
    )
    top_n: int = Field(
        default=5, 
        description="返回前N只股票"
    )

class SmartStockScreeningTool(BaseTool):
    name: str = "smart_stock_screening"
    description: str = "根据市盈率、涨幅、行业等因子智能筛选适合投资的美股，特别关注科技行业"
    args_schema: type = SmartStockScreeningInput
    
    def _run(self, symbols: Optional[List[str]] = None, top_n: int = 5) -> Dict[str, Any]:
        """智能股票筛选"""
        # 默认用S&P500科技股池
        symbols = symbols or SP500_TECH_SYMBOLS
        results = []
        
        for symbol in symbols:
            print(f"正在处理股票: {symbol}")
            df = fetch_daily(symbol)
            print(f"{symbol} fetch_daily 结果: {df is not None}")
            overview = fetch_overview(symbol)
            print(f"{symbol}: df={df is not None}, overview={overview is not None}")
            if df is None or overview is None:
                print(f"{symbol} 数据获取失败，跳过")
                continue
            # index 归一化安全处理，确保与 USStockDataTool 一致
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            df.index = pd.Index([d.normalize() if isinstance(d, pd.Timestamp) else pd.to_datetime(d).normalize() for d in df.index])
            print(f"{symbol} overview: {overview}")
            sector = overview.get('sector', '')
            if 'Technology' not in sector:
                print(f"{symbol} 非科技行业 (sector={sector})，跳过")
                continue  # 只选科技行业
            industry = overview.get('industry', '')
            print(f"{symbol}: sector={sector}, industry={industry}")
            try:
                pe = float(overview.get('trailingPE', 0))
            except:
                pe = 0
            ret_5d = calc_return(df, 5)
            # 打分：PE越低越好，涨幅越高越好
            pe_score = 1/pe if pe > 0 else 0
            ret_score = ret_5d if ret_5d is not None else 0
            score = pe_score * 0.5 + ret_score * 0.5
            results.append({
                "symbol": symbol,
                "score": round(score, 4),
                "pe": pe,
                "industry": industry,
                "ret_5d": round(ret_5d * 100, 2) if ret_5d is not None else None,
                "price": round(df["Close"].iloc[-1], 2)
            })
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_n]
        return {"stocks": results}

class USStockDataInput(BaseModel):
    symbol: str = Field(description="股票代码")
    data_type: str = Field(
        default="current",
        description="数据类型：current(当前价格), history(历史价格), kline(K线), change(涨跌幅)"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="开始日期 (YYYY-MM-DD)"
    )
    end_date: Optional[str] = Field(
        default=None,
        description="结束日期 (YYYY-MM-DD)"
    )

class USStockDataTool(BaseTool):
    name: str = "us_stock_data"
    description: str = "获取美股实时行情数据，包括当前价格、历史价格、K线数据和涨跌幅"
    args_schema: type = USStockDataInput
    
    def _run(self, symbol: str, data_type: str = "current", 
              start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """获取美股数据"""
        df = fetch_daily(symbol)
        if df is None:
            return {"error": f"无法获取 {symbol} 的数据"}
        # index 归一化安全处理
        print(f"df: {df}")
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        # 用 map 方式归一化，兼容所有 index 类型
        df.index = pd.Index([d.normalize() if isinstance(d, pd.Timestamp) else pd.to_datetime(d).normalize() for d in df.index])
        print(f"df.index: {df.index}")
        print(f"data_type: {data_type}")
        if data_type == "current":
            return {
                "symbol": symbol,
                "price": round(float(df["Close"].iloc[-1]), 2),
                "volume": int(df["Volume"].iloc[-1]),
                "date": pd.to_datetime(df.index[-1]).strftime("%Y-%m-%d")
            }
        elif data_type == "history":
            if start_date and end_date:
                start_dt = pd.to_datetime(start_date).normalize()
                end_dt = pd.to_datetime(end_date).normalize()
                # 使用 .loc 切片方式，完全避免标签不匹配问题
                try:
                    df_filtered = df.loc[start_dt:end_dt]
                except Exception:
                    # 如果切片失败，回退到全量数据
                    df_filtered = df
            else:
                df_filtered = df.tail(10)  # 默认最近10天
            history = {}
            for idx, row in df_filtered.iterrows():
                if isinstance(idx, pd.Timestamp):
                    date_str = idx.strftime("%Y-%m-%d")
                else:
                    date_str = str(idx)
                history[date_str] = {
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"])
                }
            return {"symbol": symbol, "history": history}
        elif data_type == "change":
            if start_date and end_date:
                start_dt = pd.to_datetime(start_date).normalize()
                end_dt = pd.to_datetime(end_date).normalize()
                # 使用 .loc 切片方式，完全避免标签不匹配问题
                try:
                    df_filtered = df.loc[start_dt:end_dt]
                    if not df_filtered.empty:
                        start_price = float(df_filtered.iloc[0]["Close"])
                        end_price = float(df_filtered.iloc[-1]["Close"])
                    else:
                        # 区间无数据，回退到全量首末
                        start_price = float(df["Close"].iloc[0])
                        end_price = float(df["Close"].iloc[-1])
                except Exception:
                    # 如果切片失败，回退到全量首末
                    start_price = float(df["Close"].iloc[0])
                    end_price = float(df["Close"].iloc[-1])
            else:
                if len(df) < 6:
                    return {"error": f"{symbol} 数据不足，无法计算涨跌幅"}
                start_price = float(df["Close"].iloc[-6])  # 5天前
                end_price = float(df["Close"].iloc[-1])
            pct_change = ((end_price - start_price) / start_price) * 100
            return {
                "symbol": symbol,
                "start_price": round(start_price, 2),
                "end_price": round(end_price, 2),
                "pct_change": round(pct_change, 2)
            }
        else:
            return {"error": f"不支持的数据类型: {data_type}"} 