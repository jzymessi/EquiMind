import yfinance as yf
from mcp_server.base_tool import BaseTool
from datetime import datetime

class USStockDataTool(BaseTool):
    def run(self, context, inputs):
        symbol = inputs.get('symbol', 'AAPL')
        query_type = inputs.get('type', 'current')  # current/history/kline/change
        start = inputs.get('start')
        end = inputs.get('end')
        interval = inputs.get('interval', '1d')
        try:
            ticker = yf.Ticker(symbol)
            if query_type == 'current':
                price = ticker.info.get('regularMarketPrice')
                name = ticker.info.get('shortName')
                currency = ticker.info.get('currency')
                return {
                    'outputs': {
                        'symbol': symbol,
                        'name': name,
                        'price': price,
                        'currency': currency
                    }
                }
            elif query_type == 'history':
                # 获取历史收盘价序列
                if not start or not end:
                    return {'outputs': {'error': 'history 查询需提供 start 和 end 日期'}}
                hist = ticker.history(start=start, end=end, interval=interval)
                close_series = hist['Close'].to_dict()
                return {
                    'outputs': {
                        'symbol': symbol,
                        'history_close': close_series
                    }
                }
            elif query_type == 'kline':
                # 获取K线数据
                if not start or not end:
                    return {'outputs': {'error': 'kline 查询需提供 start 和 end 日期'}}
                hist = ticker.history(start=start, end=end, interval=interval)
                kline = hist[['Open', 'High', 'Low', 'Close', 'Volume']].reset_index().to_dict(orient='records')
                return {
                    'outputs': {
                        'symbol': symbol,
                        'kline': kline
                    }
                }
            elif query_type == 'change':
                # 计算区间涨跌幅
                if not start or not end:
                    return {'outputs': {'error': 'change 查询需提供 start 和 end 日期'}}
                hist = ticker.history(start=start, end=end, interval=interval)
                if hist.empty:
                    return {'outputs': {'error': '无历史数据'}}
                start_price = hist['Close'].iloc[0]
                end_price = hist['Close'].iloc[-1]
                pct_change = (end_price - start_price) / start_price * 100
                return {
                    'outputs': {
                        'symbol': symbol,
                        'start_price': float(start_price),
                        'end_price': float(end_price),
                        'pct_change': pct_change
                    }
                }
            else:
                return {'outputs': {'error': f'不支持的 type: {query_type}'}}
        except Exception as e:
            return {'outputs': {'error': str(e)}} 