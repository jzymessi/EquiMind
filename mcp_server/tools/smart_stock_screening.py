import pandas as pd
import requests
from config import ALPHAVANTAGE_API_KEY

# AlphaVantage 日线行情获取

def fetch_daily(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}&outputsize=compact"
    resp = requests.get(url)
    data = resp.json()
    if "Time Series (Daily)" not in data:
        return None
    df = pd.DataFrame(data["Time Series (Daily)"]).T
    df = df.rename(columns=lambda x: x.split(". ")[1])
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    return df

def get_current_price(symbol):
    df = fetch_daily(symbol)
    if df is not None:
        return df["close"].iloc[-1]
    return None

class SmartStockScreeningTool:
    def run(self, context, inputs):
        symbols = inputs.get("symbols", ["AAPL", "MSFT", "GOOG", "AMZN", "META"])
        factors = inputs.get("factors", {"close": 1.0})
        top_n = inputs.get("top_n", 3)
        results = []
        for symbol in symbols:
            df = fetch_daily(symbol)
            if df is None:
                continue
            score = 0
            for factor, weight in factors.items():
                if factor in df.columns:
                    score += df[factor].iloc[-1] * weight
            results.append({"symbol": symbol, "score": score, "price": df["close"].iloc[-1]})
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_n]
        return {"outputs": {"stocks": results}} 