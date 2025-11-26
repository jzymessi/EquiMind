import os
from typing import Dict, Any, List
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI, OpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage
from langchain.tools import BaseTool
from .tools.funnel_strategy_tool_v2 import FunnelStrategyToolV2
from .tools.news_tool import NewsRetrievalTool, MarketNewsAnalysisTool

class EquiMindAgent:
    """EquiMind 智能投资 Agent"""
    
    def __init__(self):
        # 统一的 LLM 提供方选择：vllm / openrouter / openai
        provider = (os.getenv("EQUIMIND_LLM_PROVIDER") or "").strip().lower()

        # 公共配置
        custom_base_url = os.getenv("EQUIMIND_LLM_BASE_URL")
        custom_model = os.getenv("EQUIMIND_LLM_MODEL")
        custom_api_key = os.getenv("EQUIMIND_LLM_API_KEY")

        openrouter_base_url = os.getenv("OPENROUTER_BASE_URL")
        openai_api_key = os.getenv("OPENAI_API_KEY")

        # 显式选择 vllm（本地 / 自建 OpenAI 兼容服务）
        if provider == "vllm":
            if not custom_base_url:
                raise ValueError("EQUIMIND_LLM_PROVIDER=vllm 时必须配置 EQUIMIND_LLM_BASE_URL")
            self.llm = OpenAI(
                model=custom_model or "gpt-3.5-turbo",
                openai_api_key=custom_api_key or openai_api_key or "EMPTY",
                openai_api_base=custom_base_url,
                temperature=0.7,
                max_tokens=2048,
            )

        # 显式选择 OpenRouter
        elif provider == "openrouter":
            if not openrouter_base_url:
                raise ValueError("EQUIMIND_LLM_PROVIDER=openrouter 时必须配置 OPENROUTER_BASE_URL")
            if not openai_api_key:
                raise ValueError("EQUIMIND_LLM_PROVIDER=openrouter 时必须配置 OPENAI_API_KEY 作为 OpenRouter 的 API Key")
            self.llm = ChatOpenAI(
                model=os.getenv("EQUIMIND_LLM_MODEL") or "openai/chatgpt-4o-latest",
                openai_api_key=openai_api_key,
                openai_api_base=openrouter_base_url,
            )

        # 显式选择 OpenAI 官方
        elif provider == "openai":
            if not openai_api_key:
                raise ValueError("EQUIMIND_LLM_PROVIDER=openai 时必须配置 OPENAI_API_KEY")
            self.llm = ChatOpenAI(
                model=os.getenv("EQUIMIND_LLM_MODEL") or "gpt-3.5-turbo",
                openai_api_key=openai_api_key,
            )

        else:
            # 未显式指定 provider 时，保持向后兼容的自动检测逻辑
            if custom_base_url:
                # 使用自定义兼容 OpenAI 的接口（如 vLLM）
                self.llm = OpenAI(
                    model=custom_model or "gpt-3.5-turbo",
                    openai_api_key=custom_api_key or openai_api_key or "EMPTY",
                    openai_api_base=custom_base_url,
                    temperature=0.7,
                    max_tokens=2048,
                )
            elif openrouter_base_url:
                # 使用 OpenRouter
                self.llm = ChatOpenAI(
                    model=os.getenv("EQUIMIND_LLM_MODEL") or "openai/chatgpt-4o-latest",
                    openai_api_key=openai_api_key or "EMPTY",
                    openai_api_base=openrouter_base_url,
                )
            else:
                # 默认使用 OpenAI 官方接口
                if not openai_api_key:
                    raise ValueError("未配置 OpenAI API 密钥。请设置 OPENAI_API_KEY 环境变量，或设置 EQUIMIND_LLM_PROVIDER 与对应配置。")
                self.llm = ChatOpenAI(
                    model=os.getenv("EQUIMIND_LLM_MODEL") or "gpt-3.5-turbo",
                    openai_api_key=openai_api_key,
                )
        
        # 初始化工具
        self.tools = [
            FunnelStrategyToolV2(),
            NewsRetrievalTool(),
            MarketNewsAnalysisTool(),
        ]
        # 系统Prompt
        self.system_prompt = (
            "你是EquiMind智能投顾Agent，拥有三大核心能力：\n"
            "1. 股票分析：使用 funnel_stock_strategy_v2 工具执行'三张王牌+两根线'漏斗选股策略。\n"
            "2. 新闻获取：使用 get_financial_news 工具获取最新财经新闻（中文翻译）。\n"
            "3. 情绪分析：使用 analyze_market_sentiment 工具分析市场情绪。\n"
            "你可以根据用户需求灵活调用这些工具，提供专业的投资分析和建议。"
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
            
            # 检查结果是否为空或无效
            if not result or not result.strip():
                result = "抱歉，我无法为您提供完整的分析结果。请稍后再试或换个问题。"
            
            return {
                "success": True,
                "response": result.strip(),
                "context": context
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "context": context
            }

    def simple_reply(self, user_query: str) -> str:
        """直接调用底层 LLM，返回最简单的问答结果，不走工具和 Agent。"""
        # 这里不包装上下文，也不调用任何工具，只做纯模型问答
        return self.llm.predict(user_query)
    
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