import pandas as pd
import matplotlib.pyplot as plt
from mcp_server.tools.langchain_tools import fetch_overview, SP500_TECH_SYMBOLS
import numpy as np

def zscore_normalize(series):
    mean = series.mean()
    std = series.std()
    z = (series - mean) / (std if std > 0 else 1)
    return 1 / (1 + np.exp(-z))

def quantile_score(series, q=5, reverse=False):
    bins = pd.qcut(series.rank(method='first'), q=q, labels=False, duplicates='drop')
    if reverse:
        score = (q - bins - 1) / (q - 1)
    else:
        score = bins / (q - 1)
    return score

def batch_score(df, factor_config):
    score_df = df.copy()
    total_weight = 0
    for factor, cfg in factor_config.items():
        method = cfg.get('method', 'zscore')
        weight = cfg.get('weight', 1)
        reverse = cfg.get('reverse', False)
        kwargs = cfg.get('kwargs', {})
        if method == 'zscore':
            score = zscore_normalize(score_df[factor])
        elif method == 'quantile':
            score = quantile_score(score_df[factor], reverse=reverse, **kwargs)
        else:
            raise ValueError("method must be 'zscore' or 'quantile'")
        score_df[f"{factor}_score"] = score * weight
        total_weight += weight
    score_cols = [f"{f}_score" for f in factor_config]
    score_df['total_score'] = score_df[score_cols].sum(axis=1) / total_weight
    return score_df

# 1. 批量抓取科技股池的因子数据
print("正在批量抓取科技股池因子数据...")
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
df = pd.DataFrame(data)
# 只要求pe和revenue_growth必须有，其他缺失用0填充
df = df.dropna(subset=['pe', 'revenue_growth'])
df = df.fillna(0)
print(f"有效股票数: {len(df)}")

# 2. 配置评分参数（可根据实际调整）
factor_config = {
    'pe': {'method': 'quantile', 'weight': 0.15, 'reverse': True, 'kwargs': {'q': 5}},
    'peg': {'method': 'quantile', 'weight': 0.15, 'reverse': True, 'kwargs': {'q': 5}},
    'revenue_growth': {'method': 'zscore', 'weight': 0.2, 'reverse': False},
    'profit_margin': {'method': 'zscore', 'weight': 0.15, 'reverse': False},
    'roe': {'method': 'zscore', 'weight': 0.1, 'reverse': False},
    'dividend_yield': {'method': 'zscore', 'weight': 0.1, 'reverse': False},
    'beta': {'method': 'quantile', 'weight': 0.15, 'reverse': True, 'kwargs': {'q': 5}},
}

# 3. 归一化打分
result_df = batch_score(df, factor_config)

# 4. 输出高分股票
print("\n高分科技股TOP10:")
print(result_df[['symbol', 'total_score'] + [f'{f}_score' for f in factor_config]].sort_values('total_score', ascending=False).head(10))

# 5. 分数分布直方图
plt.figure(figsize=(8,4))
result_df['total_score'].hist(bins=20)
plt.title('Score Distribution')
plt.xlabel('Score')
plt.ylabel('Count')
plt.show() 
plt.savefig('score_dist.png')