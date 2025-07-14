import pandas as pd
from mcp_server.tools.langchain_tools import fetch_overview, SP500_TECH_SYMBOLS
import time

print("批量抓取科技股池因子数据...")
data = []
for symbol in SP500_TECH_SYMBOLS:
    info = fetch_overview(symbol)
    if info:
        data.append({
            'symbol': symbol,
            'pe': info.get('trailingPE', None),
            'peg': info.get('pegRatio', None),
            'revenue_growth': info.get('revenueGrowth', None),
            'profit_margin': info.get('profitMargins', None),
            'roe': info.get('returnOnEquity', None),
            'dividend_yield': info.get('dividendYield', None),
            'beta': info.get('beta', None),
        })
    time.sleep(1)  # 防止被限流

df = pd.DataFrame(data)
df.to_csv('data/tech_fundamentals.csv', index=False)
print("科技股池因子数据已保存到 data/tech_fundamentals.csv") 