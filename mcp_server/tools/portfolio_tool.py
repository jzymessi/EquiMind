"""
持仓管理工具
"""
from langchain.tools import BaseTool
from typing import Optional
from pydantic import BaseModel, Field
import yfinance as yf
from ..portfolio_manager import portfolio_manager

class PortfolioInput(BaseModel):
    """Portfolio tool input schema"""
    action: str = Field(description="操作类型: add, remove, view, check")
    user_id: str = Field(default="default", description="用户ID")
    symbol: Optional[str] = Field(default=None, description="股票代码")
    quantity: Optional[float] = Field(default=None, description="股票数量")
    buy_price: Optional[float] = Field(default=None, description="买入价格")

class PortfolioManagementTool(BaseTool):
    """持仓管理工具"""
    
    name = "portfolio_management"
    description = (
        "管理用户的股票持仓。支持的操作："
        "1. add: 添加持仓，需要 symbol, quantity, buy_price"
        "2. remove: 移除持仓，需要 symbol，可选 quantity"
        "3. view: 查看所有持仓和盈亏情况"
        "4. check: 检查单只股票的持仓状态"
    )
    args_schema = PortfolioInput
    
    def __init__(self):
        super().__init__()
    
    def _run(self, action: str, user_id: str = "default", symbol: str = None, 
             quantity: float = None, buy_price: float = None) -> str:
        """执行持仓管理操作"""
        try:
            if action == "add":
                if not all([symbol, quantity, buy_price]):
                    return "❌ 添加持仓需要提供: symbol（股票代码）, quantity（数量）, buy_price（买入价）"
                
                result = portfolio_manager.add_holding(
                    user_id=user_id,
                    symbol=symbol,
                    quantity=quantity,
                    buy_price=buy_price
                )
                return f"✅ {result['message']}"
            
            elif action == "remove":
                if not symbol:
                    return "❌ 移除持仓需要提供 symbol（股票代码）"
                
                result = portfolio_manager.remove_holding(
                    user_id=user_id,
                    symbol=symbol,
                    quantity=quantity
                )
                return f"✅ {result['message']}" if result['success'] else f"❌ {result['message']}"
            
            elif action == "view":
                return self._view_portfolio(user_id)
            
            elif action == "check":
                if not symbol:
                    return "❌ 检查持仓需要提供 symbol（股票代码）"
                return self._check_holding(user_id, symbol)
            
            else:
                return f"❌ 不支持的操作: {action}。支持的操作: add, remove, view, check"
        
        except Exception as e:
            return f"❌ 操作失败: {str(e)}"
    
    def _view_portfolio(self, user_id: str) -> str:
        """查看持仓和盈亏"""
        holdings = portfolio_manager.get_holdings(user_id)
        
        if not holdings:
            return "📊 当前没有持仓记录。\n\n使用示例：\n/agent 添加持仓 AAPL 100股 买入价150美元"
        
        # 获取当前价格
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
        
        # 计算盈亏
        pnl_data = portfolio_manager.calculate_pnl(user_id, current_prices)
        
        # 格式化输出
        output = "📊 **持仓概览**\n\n"
        
        for holding in pnl_data["holdings"]:
            symbol = holding["symbol"]
            pnl = holding["pnl"]
            pnl_pct = holding["pnl_pct"]
            
            emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
            sign = "+" if pnl > 0 else ""
            
            output += f"{emoji} **{symbol}**\n"
            output += f"   持仓: {holding['quantity']:.0f}股\n"
            output += f"   成本: ${holding['buy_price']:.2f} → 现价: ${holding['current_price']:.2f}\n"
            output += f"   盈亏: {sign}${pnl:.2f} ({sign}{pnl_pct:.2f}%)\n"
            output += f"   买入日期: {holding['buy_date']}\n\n"
        
        summary = pnl_data["summary"]
        total_pnl = summary["total_pnl"]
        total_pnl_pct = summary["total_pnl_pct"]
        
        emoji = "🟢" if total_pnl > 0 else "🔴" if total_pnl < 0 else "⚪"
        sign = "+" if total_pnl > 0 else ""
        
        output += "━━━━━━━━━━━━━━━━\n"
        output += f"{emoji} **总计**\n"
        output += f"   总成本: ${summary['total_cost']:.2f}\n"
        output += f"   总市值: ${summary['total_value']:.2f}\n"
        output += f"   总盈亏: {sign}${total_pnl:.2f} ({sign}{total_pnl_pct:.2f}%)\n"
        
        return output
    
    def _check_holding(self, user_id: str, symbol: str) -> str:
        """检查单只股票的持仓"""
        holdings = portfolio_manager.get_holdings(user_id)
        symbol = symbol.upper()
        
        matching = [h for h in holdings if h["symbol"] == symbol]
        
        if not matching:
            return f"❌ 未找到 {symbol} 的持仓记录"
        
        # 获取当前价格
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            current_price = hist['Close'].iloc[-1] if not hist.empty else None
        except:
            current_price = None
        
        if current_price is None:
            return f"❌ 无法获取 {symbol} 的当前价格"
        
        # 计算总持仓
        total_quantity = sum(h["quantity"] for h in matching)
        avg_price = sum(h["quantity"] * h["buy_price"] for h in matching) / total_quantity
        
        total_cost = total_quantity * avg_price
        total_value = total_quantity * current_price
        pnl = total_value - total_cost
        pnl_pct = (pnl / total_cost) * 100
        
        emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
        sign = "+" if pnl > 0 else ""
        
        output = f"{emoji} **{symbol} 持仓详情**\n\n"
        output += f"总持仓: {total_quantity:.0f}股\n"
        output += f"平均成本: ${avg_price:.2f}\n"
        output += f"当前价格: ${current_price:.2f}\n"
        output += f"总成本: ${total_cost:.2f}\n"
        output += f"总市值: ${total_value:.2f}\n"
        output += f"盈亏: {sign}${pnl:.2f} ({sign}{pnl_pct:.2f}%)\n\n"
        
        if len(matching) > 1:
            output += "**分批记录:**\n"
            for i, h in enumerate(matching, 1):
                output += f"{i}. {h['quantity']:.0f}股 @${h['buy_price']:.2f} ({h.get('buy_date', 'N/A')})\n"
        
        return output
    
    def _arun(self, **kwargs):
        raise NotImplementedError("异步暂不支持")
