"""
智能提醒工具
"""
from langchain.tools import BaseTool
from typing import Optional
from pydantic import BaseModel, Field
from ..alert_manager import alert_manager

class AlertInput(BaseModel):
    """Alert tool input schema"""
    action: str = Field(description="操作类型: add, remove, list, check")
    user_id: str = Field(default="default", description="用户ID")
    symbol: Optional[str] = Field(default=None, description="股票代码")
    alert_type: Optional[str] = Field(default=None, description="提醒类型: price_above, price_below, rsi_above, rsi_below")
    threshold: Optional[float] = Field(default=None, description="阈值")

class SmartAlertTool(BaseTool):
    """智能提醒工具"""
    
    name = "smart_alert"
    description = (
        "设置和管理股票价格/指标提醒。支持的操作："
        "1. add: 添加提醒，需要 symbol, alert_type, threshold"
        "   - alert_type 可选: price_above(价格突破), price_below(价格跌破), rsi_above(RSI超过), rsi_below(RSI低于)"
        "2. remove: 移除提醒，需要 symbol"
        "3. list: 查看所有活跃提醒"
        "4. check: 立即检查所有提醒是否触发"
    )
    args_schema = AlertInput
    
    def __init__(self):
        super().__init__()
    
    def _run(self, action: str, user_id: str = "default", symbol: str = None,
             alert_type: str = None, threshold: float = None) -> str:
        """执行提醒操作"""
        try:
            if action == "add":
                if not all([symbol, alert_type, threshold]):
                    return "❌ 添加提醒需要提供: symbol（股票代码）, alert_type（提醒类型）, threshold（阈值）"
                
                valid_types = ["price_above", "price_below", "rsi_above", "rsi_below"]
                if alert_type not in valid_types:
                    return f"❌ alert_type 必须是以下之一: {', '.join(valid_types)}"
                
                result = alert_manager.add_alert(
                    user_id=user_id,
                    symbol=symbol,
                    alert_type=alert_type,
                    threshold=threshold
                )
                return f"✅ {result['message']}"
            
            elif action == "remove":
                if not symbol:
                    return "❌ 移除提醒需要提供 symbol（股票代码）"
                
                result = alert_manager.remove_alert(user_id=user_id, symbol=symbol)
                return f"✅ {result['message']}" if result['success'] else f"❌ {result['message']}"
            
            elif action == "list":
                return self._list_alerts(user_id)
            
            elif action == "check":
                return self._check_alerts(user_id)
            
            else:
                return f"❌ 不支持的操作: {action}。支持的操作: add, remove, list, check"
        
        except Exception as e:
            return f"❌ 操作失败: {str(e)}"
    
    def _list_alerts(self, user_id: str) -> str:
        """列出所有提醒"""
        alerts = alert_manager.get_alerts(user_id, active_only=True)
        
        if not alerts:
            return "📢 当前没有活跃的提醒。\n\n使用示例：\n/agent 提醒我 AAPL 跌破 150 美元"
        
        output = "📢 **活跃提醒列表**\n\n"
        
        # 按股票分组
        by_symbol = {}
        for alert in alerts:
            symbol = alert["symbol"]
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(alert)
        
        for symbol, symbol_alerts in by_symbol.items():
            output += f"**{symbol}**\n"
            for alert in symbol_alerts:
                alert_type = alert["type"]
                threshold = alert["threshold"]
                
                if alert_type == "price_above":
                    desc = f"价格突破 ${threshold:.2f}"
                elif alert_type == "price_below":
                    desc = f"价格跌破 ${threshold:.2f}"
                elif alert_type == "rsi_above":
                    desc = f"RSI 超过 {threshold:.0f}"
                elif alert_type == "rsi_below":
                    desc = f"RSI 低于 {threshold:.0f}"
                else:
                    desc = f"{alert_type} {threshold}"
                
                output += f"  • {desc}\n"
            output += "\n"
        
        output += f"共 {len(alerts)} 个提醒\n"
        output += "\n💡 提示：提醒会在后台自动检查，触发时会通过 Telegram 通知你"
        
        return output
    
    def _check_alerts(self, user_id: str) -> str:
        """检查提醒"""
        triggered = alert_manager.check_alerts(user_id)
        
        if not triggered:
            return "✅ 已检查所有提醒，暂无触发"
        
        output = f"🔔 **触发了 {len(triggered)} 个提醒！**\n\n"
        
        for alert in triggered:
            symbol = alert["symbol"]
            trigger_msg = alert.get("trigger_message", "提醒已触发")
            trigger_value = alert.get("trigger_value")
            
            output += f"• {trigger_msg}\n"
        
        output += "\n这些提醒已被标记为已触发，不会再次提醒。"
        
        return output
    
    def _arun(self, **kwargs):
        raise NotImplementedError("异步暂不支持")
