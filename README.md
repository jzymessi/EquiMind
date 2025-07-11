# EquiMind v2.0

EquiMind 是一个基于 **LangChain + LangGraph** 的智能投资决策平台。它支持多工具集成、上下文驱动的智能决策，并可通过 API 实现自动化选股、消息推送和交易。

## 🚀 新版本特性

### LangChain 集成
- **智能 Agent**：基于 LangChain 的对话式投资助手
- **自动工具选择**：根据用户意图智能选择合适的工具
- **上下文记忆**：完整的对话历史和状态管理
- **结构化输出**：标准化的工具输入输出格式

### LangGraph 工作流
- **多步骤投资决策**：市场分析 → 股票筛选 → 风险评估 → 推荐
- **条件分支**：根据市场情况选择不同策略
- **状态管理**：跟踪投资组合和决策历史
- **可扩展工作流**：支持自定义投资策略

## 项目定位
- 智能量化投资 Agent
- 支持多工具插件（行情、策略、推送、交易等）
- 基于 LangChain + LangGraph 的现代化架构
- 可扩展、可集成、自动化

## 主要功能
- 实时获取股票行情数据
- 智能股票筛选（多因子分析）
- 投资决策工作流
- 风险评估和推荐
- 提供标准化 API 服务

## 架构说明
```
EquiMind/
  ├── mcp_server/                # LangChain Agent Server
  │     ├── server.py            # FastAPI 主服务，支持多种模式
  │     ├── langchain_agent.py   # LangChain Agent 实现
  │     ├── investment_workflow.py # LangGraph 投资工作流
  │     ├── tools/
  │           ├── langchain_tools.py # LangChain 工具实现
  │           └── smart_stock_screening.py # 原有工具（兼容）
  ├── frontend_streamlit/        # Streamlit 前端
  │     └── app.py               # 现代化前端界面
  ├── requirements.txt           # 依赖包
  ├── config.py                  # 配置文件
  └── env_example.txt           # 环境变量示例
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# 复制环境变量示例文件
cp env_example.txt .env

# 编辑 .env 文件，填入你的 API Keys
# 支持 OpenAI 或 OpenRouter API Key
OPENAI_API_KEY=your_openai_or_openrouter_api_key_here
ALPHAVANTAGE_API_KEY=your_alphavantage_api_key_here

# 如果使用 OpenRouter，可以设置基础 URL（可选）
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### 3. 启动 LangChain Server
```bash
uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000
```

### 4. 运行前端页面
```bash
streamlit run frontend_streamlit/app.py
```

### 5. 在浏览器访问前端页面
- 选择处理模式（智能 Agent / 投资工作流 / 直接工具调用）
- 输入你的投资需求
- 查看智能分析结果

## API 接口

### 1. 智能 Agent 查询
```bash
POST /agent/query
{
  "user_query": "帮我推荐5个现在适合投资的美股",
  "context": {"user_id": "leo", "risk_preference": "moderate"}
}
```

### 2. 投资工作流
```bash
POST /workflow/investment
{
  "user_query": "帮我分析当前科技股投资机会",
  "context": {"user_id": "leo"}
}
```

### 3. 兼容原有 MCP 接口
```bash
POST /mcp/call
{
  "tool_name": "smart_stock_screening",
  "inputs": {"top_n": 5}
}
```

## 模式说明

### 1. 智能体（Agent）模式
- 基于 LangChain 的对话式智能助手，用户用自然语言提问，Agent 自动理解意图、选择合适工具（如选股、查行情、分析财报等），并给出结构化或自然语言答案。
- 支持多轮对话和上下文记忆，能理解追问、指代、补充等复杂语境。
- 适合“像和投顾聊天一样”的智能投研体验。
- 底层实现：LangChain Agent + ConversationBufferMemory 记忆模块 + 多工具自动调度。

### 2. 工作流（Workflow）模式
- 基于 LangGraph 的多步骤决策流程，将投资决策拆分为市场分析→股票筛选→风险评估→推荐等环节，每步可独立扩展和调试。
- 适合标准化、结构化的投研流程，如自动化投研报告、投资决策流水线。
- 底层实现：LangGraph 状态机 + 多工具组合 + 每步状态可追踪。

### 3. 直接工具调用
- 直接调用底层某个工具（如选股、查行情），无需智能推理和上下文。
- 适合前端开发、API对接、自动化脚本、单工具调试。
- 兼容 MCP 协议，便于老系统迁移。

## 记忆模块说明
- 智能体模式下，系统自动记录完整的历史对话（用户输入+AI回复），支持多轮追问、上下文理解。
- 默认保存全部原文（不做摘要），可配置只保留最近N轮或用摘要机制压缩历史。
- 记忆模块让Agent能像真人一样理解“它”、“再来一个”、“上次那个”等指代。
- 工作流和工具调用模式一般无长期记忆，仅在本流程内短暂保存状态。

## 智能体（Agent）完整流程
1. 用户输入自然语言问题，前端发送到 /agent/query。
2. 后端初始化 Agent，载入工具和记忆模块。
3. Agent 组装历史对话和本次输入，作为 LLM 输入。
4. LLM 推理意图，自动选择合适工具和参数。
5. Agent 调用工具（如选股、查行情），获取结构化结果。
6. LLM 根据工具结果生成自然语言回复。
7. Agent 返回回复和结构化数据，前端展示。
8. 用户可继续追问，Agent 自动利用记忆理解上下文。

## 典型使用场景
- 智能投顾对话、自动化投研报告、API集成、批量数据处理等。

## 典型使用例子

### 例1：智能 Agent 对话
- **输入**：帮我推荐5个现在适合投资的美股
- **Agent 回复**：基于当前市场分析，我为您推荐以下5只科技股...
- **特点**：自动工具选择、上下文记忆、自然对话

### 例2：投资工作流分析
- **输入**：分析当前科技股投资机会
- **工作流**：
  1. 市场分析：当前科技股整体表现...
  2. 股票筛选：筛选出5只优质科技股
  3. 风险评估：评估每只股票的风险等级
  4. 最终推荐：综合建议和投资策略

### 例3：直接工具调用
- **输入**：查询苹果公司当前股价
- **返回**：{"symbol": "AAPL", "price": 190.5, "volume": 1234567}

## 扩展方式

### 添加新工具
```python
from langchain.tools import BaseTool

class MyNewTool(BaseTool):
    name = "my_new_tool"
    description = "我的新工具描述"
    
    def _run(self, **kwargs):
        # 工具逻辑
        return result
```

### 注册到 Agent
```python
# 在 langchain_agent.py 中添加
self.tools.append(MyNewTool())
```

### 扩展工作流
```python
# 在 investment_workflow.py 中添加新节点
def my_new_node(state: InvestmentState) -> InvestmentState:
    # 新节点逻辑
    return state

workflow.add_node("my_new_node", my_new_node)
```

## 技术栈

- **后端框架**：FastAPI + LangChain + LangGraph
- **前端框架**：Streamlit
- **LLM 集成**：OpenAI GPT / OpenRouter
- **数据源**：AlphaVantage API
- **状态管理**：LangGraph State Management

## 适用场景
- 个人投资者智能选股
- 量化投资策略开发
- 投资顾问工具
- 金融教育平台
- 自动化交易系统

## 开发计划
- [ ] 支持更多数据源（Yahoo Finance、IEX Cloud）
- [ ] 增加技术指标分析
- [ ] 实现回测功能
- [ ] 添加风险管理模块
- [ ] 支持多语言界面
- [ ] 移动端适配

## 贡献指南
欢迎提交 Issue 和 Pull Request！

## 许可证
MIT License
