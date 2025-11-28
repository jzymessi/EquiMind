"""
可视化图表工具
"""
from langchain.tools import BaseTool
from typing import Optional
from pydantic import BaseModel, Field
import yfinance as yf
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import pandas_ta as ta
from datetime import datetime
from pathlib import Path

class ChartInput(BaseModel):
    """Chart tool input schema"""
    chart_type: str = Field(description="图表类型: price, price_rsi, portfolio")
    symbol: Optional[str] = Field(default=None, description="股票代码")
    period: str = Field(default="3mo", description="时间周期: 1mo, 3mo, 6mo, 1y, 2y, 5y")
    user_id: str = Field(default="default", description="用户ID")

class ChartGeneratorTool(BaseTool):
    """图表生成工具"""
    
    name = "generate_chart"
    description = (
        "生成股票走势图表。支持的图表类型："
        "1. price: 价格走势图（带均线）"
        "2. price_rsi: 价格+RSI 组合图"
        "3. portfolio: 持仓饼图"
    )
    args_schema = ChartInput
    
    def __init__(self):
        super().__init__()
        # 使用 object.__setattr__ 绕过 Pydantic 限制
        chart_dir = Path("data/charts")
        chart_dir.mkdir(parents=True, exist_ok=True)
        object.__setattr__(self, 'chart_dir', chart_dir)
        
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
    
    def _run(self, chart_type: str, symbol: str = None, period: str = "3mo",
             user_id: str = "default") -> str:
        """生成图表"""
        try:
            if chart_type == "price":
                return self._generate_price_chart(symbol, period)
            elif chart_type == "price_rsi":
                return self._generate_price_rsi_chart(symbol, period)
            elif chart_type == "portfolio":
                return self._generate_portfolio_chart(user_id)
            else:
                return f"❌ 不支持的图表类型: {chart_type}。支持: price, price_rsi, portfolio"
        
        except Exception as e:
            return f"❌ 生成图表失败: {str(e)}"
    
    def _generate_price_chart(self, symbol: str, period: str) -> str:
        """生成价格走势图"""
        if not symbol:
            return "❌ 需要提供 symbol（股票代码）"
        
        symbol = symbol.upper()
        
        # 获取数据
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return f"❌ 无法获取 {symbol} 的历史数据"
        
        data_points = len(hist)
        
        # 根据数据量智能选择均线
        # SMA20: 至少需要20个数据点
        # SMA50: 至少需要50个数据点
        # SMA200: 至少需要200个数据点
        show_sma20 = data_points >= 20
        show_sma50 = data_points >= 50
        show_sma200 = data_points >= 200
        
        # 计算可用的均线
        if show_sma20:
            hist['SMA20'] = ta.sma(hist['Close'], length=20)
        if show_sma50:
            hist['SMA50'] = ta.sma(hist['Close'], length=50)
        if show_sma200:
            hist['SMA200'] = ta.sma(hist['Close'], length=200)
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 绘制价格
        ax.plot(hist.index, hist['Close'], label='Price', linewidth=2, color='#2E86DE')
        
        # 绘制可用的均线（只绘制非NaN部分）
        if show_sma20:
            valid_sma20 = hist['SMA20'].dropna()
            if len(valid_sma20) > 0:
                ax.plot(valid_sma20.index, valid_sma20, label='SMA20', 
                       linewidth=1.5, color='#FFA502', alpha=0.8)
        
        if show_sma50:
            valid_sma50 = hist['SMA50'].dropna()
            if len(valid_sma50) > 0:
                ax.plot(valid_sma50.index, valid_sma50, label='SMA50', 
                       linewidth=1.5, color='#FF6B6B', alpha=0.8)
        
        if show_sma200:
            valid_sma200 = hist['SMA200'].dropna()
            if len(valid_sma200) > 0:
                ax.plot(valid_sma200.index, valid_sma200, label='SMA200', 
                       linewidth=1.5, color='#4ECDC4', alpha=0.8)
        
        # 设置标题和标签
        title = f'{symbol} Price Chart ({period}, {data_points} days)'
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price ($)', fontsize=12)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        # 保存图表
        filename = f"{symbol}_price_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.chart_dir / filename
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        # 生成结果信息
        result = f"✅ 图表已生成: {filepath}\n\n"
        result += f"当前价格: ${hist['Close'].iloc[-1]:.2f}\n"
        result += f"数据点数: {data_points} 天\n"
        result += f"均线: "
        
        ma_list = []
        if show_sma20:
            ma_list.append("SMA20")
        if show_sma50:
            ma_list.append("SMA50")
        if show_sma200:
            ma_list.append("SMA200")
        else:
            ma_list.append("SMA200(需要≥200天数据)")
        
        result += ", ".join(ma_list)
        
        return result
    
    def _generate_price_rsi_chart(self, symbol: str, period: str) -> str:
        """生成价格+RSI组合图"""
        if not symbol:
            return "❌ 需要提供 symbol（股票代码）"
        
        symbol = symbol.upper()
        
        # 获取数据
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return f"❌ 无法获取 {symbol} 的历史数据"
        
        data_points = len(hist)
        
        # 根据数据量智能选择均线
        show_sma20 = data_points >= 20
        show_sma50 = data_points >= 50
        show_sma200 = data_points >= 200
        
        # 计算指标
        if show_sma20:
            hist['SMA20'] = ta.sma(hist['Close'], length=20)
        if show_sma50:
            hist['SMA50'] = ta.sma(hist['Close'], length=50)
        if show_sma200:
            hist['SMA200'] = ta.sma(hist['Close'], length=200)
        hist['RSI'] = ta.rsi(hist['Close'], length=14)
        
        # 创建子图
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), 
                                        gridspec_kw={'height_ratios': [3, 1]})
        
        # 上图：价格和均线
        ax1.plot(hist.index, hist['Close'], label='Price', linewidth=2, color='#2E86DE')
        
        # 绘制可用的均线
        if show_sma20:
            valid_sma20 = hist['SMA20'].dropna()
            if len(valid_sma20) > 0:
                ax1.plot(valid_sma20.index, valid_sma20, label='SMA20', 
                        linewidth=1.5, color='#FFA502', alpha=0.8)
        
        if show_sma50:
            valid_sma50 = hist['SMA50'].dropna()
            if len(valid_sma50) > 0:
                ax1.plot(valid_sma50.index, valid_sma50, label='SMA50', 
                        linewidth=1.5, color='#FF6B6B', alpha=0.8)
        
        if show_sma200:
            valid_sma200 = hist['SMA200'].dropna()
            if len(valid_sma200) > 0:
                ax1.plot(valid_sma200.index, valid_sma200, label='SMA200', 
                        linewidth=1.5, color='#4ECDC4', alpha=0.8)
        
        title = f'{symbol} Price & RSI Chart ({period}, {data_points} days)'
        ax1.set_title(title, fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price ($)', fontsize=12)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # 下图：RSI
        ax2.plot(hist.index, hist['RSI'], label='RSI', linewidth=2, color='#9B59B6')
        ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Overbought (70)')
        ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='Oversold (30)')
        ax2.fill_between(hist.index, 30, 70, alpha=0.1, color='gray')
        
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('RSI', fontsize=12)
        ax2.set_ylim(0, 100)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        
        # 保存图表
        filename = f"{symbol}_price_rsi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.chart_dir / filename
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        current_price = hist['Close'].iloc[-1]
        current_rsi = hist['RSI'].iloc[-1]
        
        return f"✅ 图表已生成: {filepath}\n\n当前价格: ${current_price:.2f}\n当前RSI: {current_rsi:.1f}"
    
    def _generate_portfolio_chart(self, user_id: str) -> str:
        """生成持仓饼图"""
        from ..portfolio_manager import portfolio_manager
        
        holdings = portfolio_manager.get_holdings(user_id)
        
        if not holdings:
            return "❌ 当前没有持仓记录"
        
        # 获取当前价格并计算市值
        symbols = list(set(h["symbol"] for h in holdings))
        current_prices = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_prices[symbol] = hist['Close'].iloc[-1]
            except:
                current_prices[symbol] = None
        
        # 计算每只股票的市值
        values = {}
        for holding in holdings:
            symbol = holding["symbol"]
            if symbol in current_prices and current_prices[symbol]:
                value = holding["quantity"] * current_prices[symbol]
                values[symbol] = values.get(symbol, 0) + value
        
        if not values:
            return "❌ 无法获取持仓股票的当前价格"
        
        # 创建饼图
        fig, ax = plt.subplots(figsize=(10, 8))
        
        labels = list(values.keys())
        sizes = list(values.values())
        colors = plt.cm.Set3(range(len(labels)))
        
        # 计算百分比
        total = sum(sizes)
        percentages = [f'{label}\n${size:,.0f}\n({size/total*100:.1f}%)' 
                      for label, size in zip(labels, sizes)]
        
        ax.pie(sizes, labels=percentages, colors=colors, autopct='',
               startangle=90, textprops={'fontsize': 10})
        ax.set_title(f'Portfolio Distribution (Total: ${total:,.0f})', 
                    fontsize=16, fontweight='bold')
        
        # 保存图表
        filename = f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.chart_dir / filename
        plt.tight_layout()
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()
        
        return f"✅ 持仓饼图已生成: {filepath}\n\n总市值: ${total:,.2f}"
    
    def _arun(self, **kwargs):
        raise NotImplementedError("异步暂不支持")
