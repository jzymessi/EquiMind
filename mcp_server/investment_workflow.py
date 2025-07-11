from typing import Dict, Any, List, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from mcp_server.tools.langchain_tools import SmartStockScreeningTool, USStockDataTool
import os

# 状态定义
class InvestmentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    user_query: str
    market_analysis: Dict[str, Any]
    stock_screening: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    final_recommendation: Dict[str, Any]

# 初始化 LLM - 支持 OpenRouter
def get_llm():
    openrouter_base_url = os.getenv("OPENROUTER_BASE_URL")
    
    if openrouter_base_url:
        # 使用 OpenRouter
        return ChatOpenAI(
            model="openai/gpt-3.5-turbo",  # 或其他 OpenRouter 支持的模型
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            openai_api_base=openrouter_base_url
        )
    else:
        # 使用 OpenAI
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

llm = get_llm()

# 工具实例
stock_screening_tool = SmartStockScreeningTool()
stock_data_tool = USStockDataTool()

def analyze_market(state: InvestmentState) -> InvestmentState:
    """市场分析节点"""
    messages = state["messages"]
    user_query = state["user_query"]
    
    # 分析用户查询，确定市场分析策略
    analysis_prompt = f"""
    基于用户查询：{user_query}
    
    请分析当前市场环境，考虑以下因素：
    1. 整体市场趋势
    2. 科技股表现
    3. 风险偏好
    
    请提供简要的市场分析。
    """
    
    response = llm.invoke([HumanMessage(content=analysis_prompt)])
    
    state["market_analysis"] = {
        "analysis": response.content,
        "timestamp": "2024-01-01"  # 实际应用中应该用真实时间戳
    }
    
    state["messages"].append(AIMessage(content=f"市场分析完成：{response.content}"))
    
    return state

def screen_stocks(state: InvestmentState) -> InvestmentState:
    """股票筛选节点"""
    messages = state["messages"]
    user_query = state["user_query"]
    
    # 根据用户查询和市场分析，确定筛选参数
    if "推荐" in user_query or "筛选" in user_query:
        # 使用智能筛选工具
        result = stock_screening_tool._run(top_n=5)
    else:
        # 默认筛选
        result = stock_screening_tool._run(top_n=3)
    
    state["stock_screening"] = result
    state["messages"].append(AIMessage(content=f"股票筛选完成，找到 {len(result.get('stocks', []))} 只候选股票"))
    
    return state

def assess_risk(state: InvestmentState) -> InvestmentState:
    """风险评估节点"""
    messages = state["messages"]
    stock_screening = state["stock_screening"]
    
    stocks = stock_screening.get("stocks", [])
    if not stocks:
        state["risk_assessment"] = {"risk_level": "unknown", "recommendation": "无可用股票数据"}
        return state
    
    # 分析每只股票的风险
    risk_analysis = []
    for stock in stocks:
        symbol = stock["symbol"]
        pe = stock.get("pe", 0)
        ret_5d = stock.get("ret_5d", 0)
        
        # 简单的风险评估逻辑
        risk_score = 0
        if pe > 30:
            risk_score += 2  # 高估值风险
        elif pe < 15:
            risk_score -= 1  # 低估值优势
            
        if ret_5d and ret_5d > 10:
            risk_score += 1  # 短期涨幅过大风险
        elif ret_5d and ret_5d < -10:
            risk_score += 1  # 短期跌幅过大风险
            
        risk_level = "低风险" if risk_score <= 0 else "中风险" if risk_score <= 2 else "高风险"
        
        risk_analysis.append({
            "symbol": symbol,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "pe": pe,
            "ret_5d": ret_5d
        })
    
    state["risk_assessment"] = {
        "risk_analysis": risk_analysis,
        "overall_risk": "中风险"  # 简化处理
    }
    
    state["messages"].append(AIMessage(content=f"风险评估完成，分析了 {len(risk_analysis)} 只股票"))
    
    return state

def generate_recommendation(state: InvestmentState) -> InvestmentState:
    """生成最终推荐"""
    messages = state["messages"]
    market_analysis = state["market_analysis"]
    stock_screening = state["stock_screening"]
    risk_assessment = state["risk_assessment"]
    
    # 生成综合推荐
    recommendation_prompt = f"""
    基于以下信息生成投资推荐：
    
    市场分析：{market_analysis.get('analysis', '')}
    候选股票：{stock_screening.get('stocks', [])}
    风险评估：{risk_assessment.get('risk_analysis', [])}
    
    请提供：
    1. 投资建议摘要
    2. 推荐股票列表（按风险收益排序）
    3. 风险提示
    4. 投资策略建议
    """
    
    response = llm.invoke([HumanMessage(content=recommendation_prompt)])
    
    state["final_recommendation"] = {
        "recommendation": response.content,
        "stocks": stock_screening.get("stocks", []),
        "risk_assessment": risk_assessment
    }
    
    state["messages"].append(AIMessage(content=response.content))
    
    return state

def should_continue_screening(state: InvestmentState) -> str:
    """决定是否继续筛选"""
    stock_screening = state["stock_screening"]
    stocks = stock_screening.get("stocks", [])
    
    # 如果有足够的候选股票，继续流程
    if len(stocks) >= 2:
        return "continue"
    else:
        return "stop"

def create_investment_workflow() -> StateGraph:
    """创建投资决策工作流"""
    workflow = StateGraph(InvestmentState)
    
    # 添加节点
    workflow.add_node("market_analysis", analyze_market)
    workflow.add_node("stock_screening", screen_stocks)
    workflow.add_node("risk_assessment", assess_risk)
    workflow.add_node("generate_recommendation", generate_recommendation)
    
    # 设置入口
    workflow.set_entry_point("market_analysis")
    
    # 添加边
    workflow.add_edge("market_analysis", "stock_screening")
    workflow.add_edge("stock_screening", "risk_assessment")
    workflow.add_edge("risk_assessment", "generate_recommendation")
    workflow.add_edge("generate_recommendation", END)
    
    # 添加条件分支（可选）
    workflow.add_conditional_edges(
        "stock_screening",
        should_continue_screening,
        {
            "continue": "risk_assessment",
            "stop": END
        }
    )
    
    return workflow.compile()

# 全局工作流实例
investment_workflow = create_investment_workflow() 