"""
完整的工具测试脚本 - 测试所有6个工具的可用性

测试工具列表：
1. FunnelStrategyToolV2 - 漏斗选股策略
2. NewsRetrievalTool - 新闻获取
3. MarketNewsAnalysisTool - 市场情绪分析
4. PortfolioManagementTool - 持仓管理
5. SmartAlertTool - 智能提醒
6. ChartGeneratorTool - 图表生成
"""
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from mcp_server.tools.funnel_strategy_tool_v2 import FunnelStrategyToolV2
from mcp_server.tools.news_tool import NewsRetrievalTool, MarketNewsAnalysisTool
from mcp_server.tools.portfolio_tool import PortfolioManagementTool
from mcp_server.tools.alert_tool import SmartAlertTool
from mcp_server.tools.chart_tool import ChartGeneratorTool

# 测试结果统计
test_results = {
    "passed": [],
    "failed": [],
    "total": 0
}

def print_section(title):
    """打印分节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_tool(tool_name, test_func):
    """测试工具并记录结果"""
    test_results["total"] += 1
    try:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始测试: {tool_name}")
        test_func()
        test_results["passed"].append(tool_name)
        print(f"✅ {tool_name} 测试通过")
        return True
    except Exception as e:
        test_results["failed"].append(tool_name)
        print(f"❌ {tool_name} 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_funnel_strategy():
    """测试漏斗选股策略工具"""
    print_section("1. 漏斗选股策略工具 (FunnelStrategyToolV2)")
    tool = FunnelStrategyToolV2()
    
    # 测试单股分析
    print("\n[测试] 单股分析模式 - 检查 NVDA")
    result = tool._run(mode="check", symbol="NVDA")
    print(result)
    assert result, "结果不应为空"
    assert "NVDA" in result, "结果应包含股票代码"
    
    # 测试扫描模式（只扫描前3个股票以节省时间）
    print("\n[测试] 扫描模式 - 快速扫描（仅测试3个股票）")
    from mcp_server.tools.funnel_strategy_tool_v2 import MOAT_TICKERS
    original_tickers = MOAT_TICKERS.copy()
    # 临时只测试3个股票
    import mcp_server.tools.funnel_strategy_tool_v2 as funnel_module
    funnel_module.MOAT_TICKERS = ["NVDA", "AAPL", "MSFT"]
    
    result = tool._run(mode="scan")
    print(result[:500] + "..." if len(result) > 500 else result)
    assert result, "扫描结果不应为空"
    
    # 恢复原始列表
    funnel_module.MOAT_TICKERS = original_tickers

def test_news_retrieval():
    """测试新闻获取工具"""
    print_section("2. 新闻获取工具 (NewsRetrievalTool)")
    tool = NewsRetrievalTool()
    
    # 测试基本新闻获取
    print("\n[测试] 获取最近24小时新闻（限5条）")
    result = tool._run(hours=24, limit=5)
    print(result[:500] + "..." if len(result) > 500 else result)
    assert result, "新闻结果不应为空"
    
    # 测试关键词过滤
    print("\n[测试] 获取包含 'tech' 关键词的新闻")
    result = tool._run(hours=48, limit=3, keywords="tech")
    print(result[:300] + "..." if len(result) > 300 else result)
    assert result, "过滤后的新闻结果不应为空"

def test_market_sentiment():
    """测试市场情绪分析工具"""
    print_section("3. 市场情绪分析工具 (MarketNewsAnalysisTool)")
    tool = MarketNewsAnalysisTool()
    
    # 测试基本情绪分析
    print("\n[测试] 分析最近24小时市场情绪")
    result = tool._run(hours=24)
    print(result)
    assert result, "情绪分析结果不应为空"
    assert any(word in result for word in ["乐观", "悲观", "中性"]), "结果应包含情绪判断"
    
    # 测试聚焦领域分析
    print("\n[测试] 分析科技领域情绪")
    result = tool._run(hours=48, focus="tech")
    print(result[:400] + "..." if len(result) > 400 else result)
    assert result, "聚焦分析结果不应为空"

def test_portfolio():
    """测试持仓管理工具"""
    print_section("4. 持仓管理工具 (PortfolioManagementTool)")
    tool = PortfolioManagementTool()
    test_user = "test_all_tools_user"
    
    # 测试添加持仓
    print("\n[测试] 添加持仓 - AAPL 100股 @$150")
    result = tool._run(action="add", user_id=test_user, symbol="AAPL", 
                      quantity=100, buy_price=150.0)
    print(result)
    assert "✅" in result, "添加持仓应该成功"
    
    print("\n[测试] 添加持仓 - NVDA 50股 @$400")
    result = tool._run(action="add", user_id=test_user, symbol="NVDA",
                      quantity=50, buy_price=400.0)
    print(result)
    assert "✅" in result, "添加持仓应该成功"
    
    # 测试查看持仓
    print("\n[测试] 查看所有持仓")
    result = tool._run(action="view", user_id=test_user)
    print(result)
    assert "AAPL" in result and "NVDA" in result, "应该显示所有持仓"
    
    # 测试检查单个持仓
    print("\n[测试] 检查 AAPL 持仓")
    result = tool._run(action="check", user_id=test_user, symbol="AAPL")
    print(result)
    assert "AAPL" in result, "应该显示AAPL持仓详情"
    
    # 测试移除持仓
    print("\n[测试] 移除部分 AAPL 持仓（50股）")
    result = tool._run(action="remove", user_id=test_user, symbol="AAPL", quantity=50)
    print(result)
    
    # 清理测试数据
    print("\n[清理] 移除所有测试持仓")
    tool._run(action="remove", user_id=test_user, symbol="AAPL")
    tool._run(action="remove", user_id=test_user, symbol="NVDA")

def test_alert():
    """测试智能提醒工具"""
    print_section("5. 智能提醒工具 (SmartAlertTool)")
    tool = SmartAlertTool()
    test_user = "test_all_tools_user"
    
    # 测试添加价格提醒
    print("\n[测试] 添加价格提醒 - AAPL 跌破 $140")
    result = tool._run(action="add", user_id=test_user, symbol="AAPL",
                      alert_type="price_below", threshold=140.0)
    print(result)
    assert "✅" in result, "添加提醒应该成功"
    
    print("\n[测试] 添加RSI提醒 - NVDA RSI低于30")
    result = tool._run(action="add", user_id=test_user, symbol="NVDA",
                      alert_type="rsi_below", threshold=30.0)
    print(result)
    assert "✅" in result, "添加提醒应该成功"
    
    # 测试查看提醒
    print("\n[测试] 查看所有提醒")
    result = tool._run(action="list", user_id=test_user)
    print(result)
    assert "AAPL" in result or "NVDA" in result, "应该显示提醒列表"
    
    # 测试检查提醒
    print("\n[测试] 检查提醒是否触发")
    result = tool._run(action="check", user_id=test_user)
    print(result)
    assert result, "检查结果不应为空"
    
    # 清理测试数据
    print("\n[清理] 移除所有测试提醒")
    tool._run(action="remove", user_id=test_user, symbol="AAPL")
    tool._run(action="remove", user_id=test_user, symbol="NVDA")

def test_chart():
    """测试图表生成工具"""
    print_section("6. 图表生成工具 (ChartGeneratorTool)")
    tool = ChartGeneratorTool()
    
    # 测试价格走势图
    print("\n[测试] 生成 AAPL 价格走势图（3个月）")
    result = tool._run(chart_type="price", symbol="AAPL", period="3mo")
    print(result)
    assert "✅" in result, "图表生成应该成功"
    assert "data/charts" in result, "应该包含图表路径"
    
    # 测试价格+RSI组合图
    print("\n[测试] 生成 NVDA 价格+RSI组合图（6个月）")
    result = tool._run(chart_type="price_rsi", symbol="NVDA", period="6mo")
    print(result)
    assert "✅" in result, "图表生成应该成功"
    assert "RSI" in result, "应该包含RSI信息"
    
    # 注意：持仓饼图需要有持仓数据，这里跳过测试
    print("\n[跳过] 持仓饼图测试（需要先添加持仓数据）")

def print_summary():
    """打印测试总结"""
    print("\n" + "="*60)
    print("  测试总结")
    print("="*60)
    
    print(f"\n总测试数: {test_results['total']}")
    print(f"通过: {len(test_results['passed'])} ✅")
    print(f"失败: {len(test_results['failed'])} ❌")
    
    if test_results["passed"]:
        print("\n✅ 通过的工具:")
        for i, tool in enumerate(test_results["passed"], 1):
            print(f"  {i}. {tool}")
    
    if test_results["failed"]:
        print("\n❌ 失败的工具:")
        for i, tool in enumerate(test_results["failed"], 1):
            print(f"  {i}. {tool}")
    
    success_rate = (len(test_results["passed"]) / test_results["total"] * 100) if test_results["total"] > 0 else 0
    print(f"\n成功率: {success_rate:.1f}%")
    
    print("\n" + "="*60)
    print("  数据文件位置")
    print("="*60)
    print("图表: data/charts/")
    print("持仓: data/portfolios/")
    print("提醒: data/alerts/")
    print("新闻: data/news.json")

if __name__ == "__main__":
    print("\n" + "#"*60)
    print("#  EquiMind 工具完整测试")
    print("#  测试时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("#"*60)
    
    # 按顺序测试所有工具
    test_tool("1. FunnelStrategyToolV2", test_funnel_strategy)
    test_tool("2. NewsRetrievalTool", test_news_retrieval)
    test_tool("3. MarketNewsAnalysisTool", test_market_sentiment)
    test_tool("4. PortfolioManagementTool", test_portfolio)
    test_tool("5. SmartAlertTool", test_alert)
    test_tool("6. ChartGeneratorTool", test_chart)
    
    # 打印测试总结
    print_summary()
    
    # 返回退出码
    sys.exit(0 if len(test_results["failed"]) == 0 else 1)
