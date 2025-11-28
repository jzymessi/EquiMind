"""
持仓管理模块
负责记录和管理用户的股票持仓
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

class PortfolioManager:
    """持仓管理器"""
    
    def __init__(self, data_dir: str = "data/portfolios"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_user_file(self, user_id: str) -> Path:
        """获取用户持仓文件路径"""
        return self.data_dir / f"{user_id}.json"
    
    def _load_portfolio(self, user_id: str) -> Dict:
        """加载用户持仓"""
        file_path = self._get_user_file(user_id)
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"holdings": [], "alerts": []}
    
    def _save_portfolio(self, user_id: str, portfolio: Dict):
        """保存用户持仓"""
        file_path = self._get_user_file(user_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(portfolio, f, ensure_ascii=False, indent=2)
    
    def add_holding(self, user_id: str, symbol: str, quantity: float, 
                    buy_price: float, buy_date: str = None) -> Dict:
        """添加持仓"""
        if buy_date is None:
            buy_date = datetime.now().strftime("%Y-%m-%d")
        
        portfolio = self._load_portfolio(user_id)
        
        holding = {
            "symbol": symbol.upper(),
            "quantity": quantity,
            "buy_price": buy_price,
            "buy_date": buy_date,
            "added_at": datetime.now().isoformat()
        }
        
        portfolio["holdings"].append(holding)
        self._save_portfolio(user_id, portfolio)
        
        return {
            "success": True,
            "message": f"已添加持仓：{symbol} x{quantity}股 @${buy_price}",
            "holding": holding
        }
    
    def remove_holding(self, user_id: str, symbol: str, quantity: float = None) -> Dict:
        """移除持仓（全部或部分）"""
        portfolio = self._load_portfolio(user_id)
        symbol = symbol.upper()
        
        holdings = portfolio["holdings"]
        removed = []
        remaining = []
        
        for holding in holdings:
            if holding["symbol"] == symbol:
                if quantity is None or quantity >= holding["quantity"]:
                    # 全部移除
                    removed.append(holding)
                else:
                    # 部分移除
                    removed_part = holding.copy()
                    removed_part["quantity"] = quantity
                    removed.append(removed_part)
                    
                    holding["quantity"] -= quantity
                    remaining.append(holding)
            else:
                remaining.append(holding)
        
        portfolio["holdings"] = remaining
        self._save_portfolio(user_id, portfolio)
        
        if removed:
            total_qty = sum(h["quantity"] for h in removed)
            return {
                "success": True,
                "message": f"已移除持仓：{symbol} x{total_qty}股",
                "removed": removed
            }
        else:
            return {
                "success": False,
                "message": f"未找到 {symbol} 的持仓"
            }
    
    def get_holdings(self, user_id: str) -> List[Dict]:
        """获取用户所有持仓"""
        portfolio = self._load_portfolio(user_id)
        return portfolio["holdings"]
    
    def calculate_pnl(self, user_id: str, current_prices: Dict[str, float]) -> Dict:
        """计算盈亏
        
        Args:
            user_id: 用户ID
            current_prices: {symbol: current_price} 当前价格字典
        
        Returns:
            持仓详情和总盈亏
        """
        holdings = self.get_holdings(user_id)
        
        results = []
        total_cost = 0
        total_value = 0
        
        for holding in holdings:
            symbol = holding["symbol"]
            quantity = holding["quantity"]
            buy_price = holding["buy_price"]
            
            current_price = current_prices.get(symbol)
            if current_price is None:
                continue
            
            cost = quantity * buy_price
            value = quantity * current_price
            pnl = value - cost
            pnl_pct = (pnl / cost) * 100 if cost > 0 else 0
            
            results.append({
                "symbol": symbol,
                "quantity": quantity,
                "buy_price": buy_price,
                "current_price": current_price,
                "cost": cost,
                "value": value,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "buy_date": holding.get("buy_date", "N/A")
            })
            
            total_cost += cost
            total_value += value
        
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
        
        return {
            "holdings": results,
            "summary": {
                "total_cost": total_cost,
                "total_value": total_value,
                "total_pnl": total_pnl,
                "total_pnl_pct": total_pnl_pct
            }
        }

# 全局实例
portfolio_manager = PortfolioManager()
