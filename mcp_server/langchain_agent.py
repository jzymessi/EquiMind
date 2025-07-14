import os
from typing import Dict, Any, List
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage
from langchain.tools import BaseTool
from mcp_server.tools.langchain_tools import SmartStockScreeningTool, USStockDataTool, AnalyzeStockTool, AllTechStockDataTool

class EquiMindAgent:
    """EquiMind 智能投资 Agent"""
    
    def __init__(self):
        # 检查是否使用 OpenRouter
        openrouter_base_url = os.getenv("OPENROUTER_BASE_URL")
        
        if openrouter_base_url:
            # 使用 OpenRouter
            self.llm = ChatOpenAI(
                model="openai/chatgpt-4o-latest",  # 或其他 OpenRouter 支持的模型
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                openai_api_base=openrouter_base_url
            )
        else:
            # 使用 OpenAI
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
        
        # 初始化工具
        self.tools = [
            SmartStockScreeningTool(),
            USStockDataTool(),
            AnalyzeStockTool(),
            AllTechStockDataTool()
        ]
        # 系统Prompt
        self.system_prompt = (
            "你是EquiMind智能投顾Agent，善于用量化和多因子分析帮助用户投资决策。"
            "如需推荐股票，请优先调用 all_tech_stock_data 工具获取全量科技股池数据，"
            "结合用户的风险偏好、成长性、估值等需求，做出专业推荐。"
            "如需分析单只股票，请调用 analyze_stock 工具。"
        )
        
        # 初始化记忆
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            k=10   # 只保留近10轮
        )
        
        # 初始化 Agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            system_prompt=self.system_prompt
        )
    
    def handle_query(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理用户查询"""
        try:
            # 构建带上下文的查询
            if context:
                context_str = f"用户上下文: {context}\n"
                full_query = context_str + user_query
            else:
                full_query = user_query
            
            # 执行 Agent
            result = self.agent.run(full_query)
            print("Agent LLM result:", result)  # 调试输出
            
            return {
                "success": True,
                "response": result,
                "context": context
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "context": context
            }
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """获取可用工具列表"""
        tools_info = []
        for tool in self.tools:
            tools_info.append({
                "name": tool.name,
                "description": tool.description
            })
        return tools_info
    
    def clear_memory(self):
        """清除对话记忆"""
        self.memory.clear()

# 全局 Agent 实例
equimind_agent = EquiMindAgent() 