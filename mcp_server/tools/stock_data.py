class StockDataTool:
    def run(self, context, inputs):
        # 模拟返回股票价格
        symbol = inputs.get('symbol', '600519')
        return {
            'outputs': {
                'symbol': symbol,
                'price': 1800.00,
                'pe': 25.0
            }
        } 