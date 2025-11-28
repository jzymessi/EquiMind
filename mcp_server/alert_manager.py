"""
智能提醒管理模块
"""
import json
from datetime import datetime
from typing import Dict, List
from pathlib import Path
import yfinance as yf

class AlertManager:
    """提醒管理器"""
    
    def __init__(self, data_dir: str = "data/alerts"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_file(self, user_id: str) -> Path:
        """获取用户提醒文件路径"""
        return self.data_dir / f"{user_id}.json"
    
    def _load_alerts(self, user_id: str) -> List[Dict]:
        """加载用户提醒"""
        file_path = self._get_user_file(user_id)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_alerts(self, user_id: str, alerts: List[Dict]):
        """保存用户提醒"""
        file_path = self._get_user_file(user_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(alerts, f, ensure_ascii=False, indent=2)
    
    def add_alert(self, user_id: str, symbol: str, alert_type: str, 
                  threshold: float, message: str = None) -> Dict:
        """添加提醒
        
        Args:
            user_id: 用户ID
            symbol: 股票代码
            alert_type: 提醒类型 (price_above, price_below, rsi_above, rsi_below)
            threshold: 阈值
            message: 自定义消息
        """
        alerts = self._load_alerts(user_id)
        
        alert = {
            "id": f"{symbol}_{alert_type}_{threshold}_{datetime.now().timestamp()}",
            "symbol": symbol.upper(),
            "type": alert_type,
            "threshold": threshold,
            "message": message,
            "created_at": datetime.now().isoformat(),
            "triggered": False
        }
        
        alerts.append(alert)
        self._save_alerts(user_id, alerts)
        
        return {
            "success": True,
            "message": f"已设置提醒：{symbol} {self._format_alert_type(alert_type)} {threshold}",
            "alert": alert
        }
    
    def remove_alert(self, user_id: str, alert_id: str = None, symbol: str = None) -> Dict:
        """移除提醒"""
        alerts = self._load_alerts(user_id)
        
        if alert_id:
            alerts = [a for a in alerts if a["id"] != alert_id]
            message = f"已移除提醒 {alert_id}"
        elif symbol:
            symbol = symbol.upper()
            original_count = len(alerts)
            alerts = [a for a in alerts if a["symbol"] != symbol]
            removed_count = original_count - len(alerts)
            message = f"已移除 {symbol} 的 {removed_count} 个提醒"
        else:
            return {"success": False, "message": "需要提供 alert_id 或 symbol"}
        
        self._save_alerts(user_id, alerts)
        return {"success": True, "message": message}
    
    def get_alerts(self, user_id: str, active_only: bool = True) -> List[Dict]:
        """获取用户提醒"""
        alerts = self._load_alerts(user_id)
        if active_only:
            alerts = [a for a in alerts if not a.get("triggered", False)]
        return alerts
    
    def check_alerts(self, user_id: str) -> List[Dict]:
        """检查并触发提醒
        
        Returns:
            被触发的提醒列表
        """
        alerts = self.get_alerts(user_id, active_only=True)
        triggered = []
        
        # 按股票分组
        symbols = list(set(a["symbol"] for a in alerts))
        
        for symbol in symbols:
            try:
                # 获取当前数据
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")
                
                if hist.empty:
                    continue
                
                current_price = hist['Close'].iloc[-1]
                
                # 计算 RSI
                try:
                    import pandas_ta as ta
                    rsi = ta.rsi(hist['Close'], length=14).iloc[-1]
                except:
                    rsi = None
                
                # 检查每个提醒
                symbol_alerts = [a for a in alerts if a["symbol"] == symbol]
                
                for alert in symbol_alerts:
                    alert_type = alert["type"]
                    threshold = alert["threshold"]
                    
                    should_trigger = False
                    
                    if alert_type == "price_above" and current_price > threshold:
                        should_trigger = True
                        alert["trigger_value"] = current_price
                        alert["trigger_message"] = f"{symbol} 价格 ${current_price:.2f} 已突破 ${threshold:.2f}"
                    
                    elif alert_type == "price_below" and current_price < threshold:
                        should_trigger = True
                        alert["trigger_value"] = current_price
                        alert["trigger_message"] = f"{symbol} 价格 ${current_price:.2f} 已跌破 ${threshold:.2f}"
                    
                    elif alert_type == "rsi_above" and rsi and rsi > threshold:
                        should_trigger = True
                        alert["trigger_value"] = rsi
                        alert["trigger_message"] = f"{symbol} RSI {rsi:.1f} 已超过 {threshold}"
                    
                    elif alert_type == "rsi_below" and rsi and rsi < threshold:
                        should_trigger = True
                        alert["trigger_value"] = rsi
                        alert["trigger_message"] = f"{symbol} RSI {rsi:.1f} 已低于 {threshold}"
                    
                    if should_trigger:
                        alert["triggered"] = True
                        alert["triggered_at"] = datetime.now().isoformat()
                        triggered.append(alert)
            
            except Exception as e:
                print(f"检查 {symbol} 提醒时出错: {str(e)}")
                continue
        
        # 更新提醒状态
        if triggered:
            all_alerts = self._load_alerts(user_id)
            for alert in all_alerts:
                for t in triggered:
                    if alert["id"] == t["id"]:
                        alert["triggered"] = True
                        alert["triggered_at"] = t["triggered_at"]
            self._save_alerts(user_id, all_alerts)
        
        return triggered
    
    def _format_alert_type(self, alert_type: str) -> str:
        """格式化提醒类型"""
        mapping = {
            "price_above": "价格突破",
            "price_below": "价格跌破",
            "rsi_above": "RSI 超过",
            "rsi_below": "RSI 低于"
        }
        return mapping.get(alert_type, alert_type)

# 全局实例
alert_manager = AlertManager()
