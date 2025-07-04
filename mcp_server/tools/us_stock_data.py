import yfinance as yf
from mcp_server.base_tool import BaseTool

class USStockDataTool(BaseTool):
    def run(self, context, inputs):
        symbol = inputs.get('symbol', 'AAPL')
        try:
            ticker = yf.Ticker(symbol)
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
        except Exception as e:
            return {'outputs': {'error': str(e)}} 