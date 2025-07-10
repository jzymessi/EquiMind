 1. 项目概述（Project Overview）
EquiMind 是一个基于大语言模型与金融数据融合的智能投研平台，专注于为全球投资者提供：
- 自动化选股建议
- 上市公司财报解读与业绩预测
- 自然语言交互式的金融知识问答
目标是让非专业用户也能轻松获得机构级别的投研服务。

---
2. 项目背景与痛点（Background & Problem Statement）
This content is only supported in a Feishu Docs

---
3. 核心功能模块（Phase 1）
📌 3.1 智能选股模块（Smart Stock Screening）
功能亮点：
- ⛏ 多因子选股引擎：支持用户自定义因子权重（如PE、PEG、ROE、营收增长率）
- 🗣 自然语言输入：如“找出过去三年盈利稳定、估值偏低的美股科技股”
- 📊 实时数据支持：接入Yahoo Finance / FMP / Polygon.io API
- 📈 策略透明：提供因子解释和回测结果摘要
技术要点：
- LLM Prompt Template → 策略语义解析
- Pandas + ta-lib → 数据筛选
- LangChain Tool → “选股助手”Agent

---
📌 3.2 财报分析与预测模块（Earnings Analysis & Forecasting）
功能亮点：
- 🧾 财报自然语言摘要：自动提炼关键指标、同比环比变动、管理层态度
- 🔍 趋势预测：基于历史数据与大语言模型进行未来财务指标估算（如EPS、利润率）
- 🧠 问答式财报分析：“为什么META的营收增长停滞？”、“AAPL的现金流最近如何？”
- 📌 行业对比：横向比较财报指标，识别优劣势
技术要点：
- LangChain Agent + Tool：动态调度财报分析函数
- 时间序列建模（未来可扩展）：Prophet / LSTM / Autoformer
- SEC API / FMP / Edgar数据库：财报源头数据接入
- GPT + 结构化数据摘要模型（Function Call 或自定义 Prompt）

---
4. 技术架构（Technical Overview）
建议绘制一个架构图，模块包含：
- 前端：Next.js / React + Chat UI
- 中间层：LangChain Agent
- 工具层：数据API（股票/财报）、选股引擎、财报分析器
- 模型层：OpenAI GPT-4 / 本地Qwen / Claude 等

---
5. 用户使用场景（Use Cases）
This content is only supported in a Feishu Docs

---
6. 竞争优势（Why EquiMind）
- ✅ 专注“内容解释 + 策略生成”，强调可解释性而非黑盒预测
- ✅ 模块化构建，易于横向拓展（如新闻、情绪、基金等）
- ✅ 可英文出海，可中文本地部署（政府/券商/私募场景）
- ✅ 可以接入用户私有数据或SaaS API 进行定制

---
7. 路线图（Roadmap 建议）
This content is only supported in a Feishu Docs

✅ 1. 数据源 / API 选型（选股 + 财报分析）
我们分为两个大类：

---
📊 一、选股所需数据源
This content is only supported in a Feishu Docs

---
📄 二、财报分析与预测所需数据源
This content is only supported in a Feishu Docs

---
✅ 推荐组合（最实用组合，适合MVP）
- 免费主用：FMP（结构化财报 + 基本面 + 技术面） + SEC
- 实时行情：Yahoo Finance 或 Polygon.io
- 财报全文：SEC EDGAR 抓取 + 自定义清洗

---
✅ 2. LangChain 代码层结构设计（Agent + Tool + 数据流）
你要实现的功能是：用户自然语言输入 → 智能理解 → 数据调用 → 分析 & 生成内容

---
🧠 LangChain Agent 总体架构图（简化版）
pgsql
复制代码
User (Chat UI)
   ↓
LangChain AgentExecutor
   ↓
+--------------------------+
| Tools                   |
|  - StockDataTool        | ← Yahoo / FMP / Polygon
|  - FinancialStatementTool| ← SEC / FMP
|  - StrategySelectorTool  | ← 本地规则引擎
|  - SummaryReportTool     | ← LLM内容生成
+--------------------------+
   ↓
LLM Chain (OpenAI / Claude / Qwen)
   ↓
Prompt Templates (选股策略、财报分析、内容生成)
   ↓
返回自然语言结果 + 图表数据

---
📦 每个 Tool 的功能说明
✅ 1. StockDataTool
- 功能：获取当前股价、技术指标、财务因子等
- API：Yahoo Finance / FMP
- 参数：
- python
- 复制代码
- def run(ticker: str, metric: str) -> dict
# 示例：metric = "price", "pe_ratio", "macd"

---
✅ 2. FinancialStatementTool
- 功能：获取公司财报结构化数据（如营收、净利、现金流）
- API：FMP / SEC
- 支持问法：
  - "META的收入同比增长多少？"
  - "特斯拉过去三年的毛利率趋势是？"

---
✅ 3. StrategySelectorTool
- 功能：用户输入选股描述 → 转换为选股规则 → 本地数据筛选
- 输入：自然语言策略
- 输出：一组满足条件的股票 + 策略说明
- 技术栈：LangChain Prompt + 本地 DuckDB/Pandas 数据过滤

---
✅ 4. SummaryReportTool
- 功能：对财报内容生成摘要，或对选股逻辑做可解释性说明
- 调用：OpenAI / Qwen + 结构化Prompt模板
- 提示词设计：
- text
- 复制代码
- 请根据以下结构化财务数据，生成一段摘要内容，包含：
关键变化（同比/环比）
管理层观点
行业对比

---
🔁 数据流 & 执行流程（以选股为例）
复制代码
🧍 用户输入：
「请找出估值低、PEG < 1、营收稳定增长的科技股」
1️⃣ LLM解析意图 → 调用 StrategySelectorTool
2️⃣ 工具调用：下载股票列表 + 财务因子 → 筛选
3️⃣ 返回股票列表（打分排序）
4️⃣ LLM生成说明：「根据你设定的PEG<1…」
最终返回：股票列表 + 解释 + 图表（可视化）

---
✅ Agent 配置代码结构建议（伪代码）
langchain.tools
tools = [
    StockDataTool(),
    FinancialStatementTool(),
    StrategySelectorTool(),
    SummaryReportTool()
]

# langchain.agents
agent_executor = initialize_agent(
    tools=tools,
    llm=ChatOpenAI(),
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)
✅ 后续可拓展模块（阶段性增加）
This content is only supported in a Feishu Docs
