# EquiMind 智能投顾

EquiMind 是一个基于 **LangChain** 的智能投资决策平台，专注于"三张王牌+两根线"漏斗选股策略。通过分层架构设计，提供股票分析、新闻获取、市场情绪分析等核心功能，支持 Telegram 机器人交互和自动化投资建议。

## 🎯 核心特性

### 智能投顾 Agent
- **对话式交互**：通过 Telegram 机器人进行自然语言投资咨询
- **六大工具**：股票分析、新闻获取、情绪分析、持仓管理、智能提醒、图表生成
- **上下文记忆**：支持多轮对话和历史记录
- **中文优化**：财经术语中英文对照，本土化体验

### 漏斗选股策略
- **三张王牌**：营收增长 + EPS增长 + 自由现金流
- **两根线择时**：200日均线趋势 + 50日均线+RSI黄金买点
- **分层架构**：数据获取、策略逻辑、工具封装完全分离
- **护城河股票池**：聚焦行业龙头和优质成长股

### 新闻与情绪分析
- **实时新闻获取**：RSS源自动抓取财经新闻
- **中文翻译**：关键财经术语自动翻译
- **市场情绪分析**：基于新闻内容的情绪判断
- **投资建议**：结合技术分析和市场情绪的综合建议

## 🎪 主要功能

### 📊 股票分析
- **漏斗选股**：基于"三张王牌+两根线"策略的智能选股
- **单股分析**：深度分析个股的基本面和技术面
- **批量扫描**：一键扫描护城河股票池，发现黄金买点
- **实时数据**：基于 yfinance 的实时股价和财务数据

### 📰 新闻服务
- **财经新闻**：自动获取最新财经资讯
- **关键词过滤**：支持按行业、公司等关键词筛选
- **中文翻译**：财经术语中英文对照显示
- **定时推送**：支持晨报、晚报定时推送

### 🎭 情绪分析
- **市场情绪**：基于新闻内容分析市场情绪
- **行业聚焦**：支持科技、AI、新能源等细分领域分析
- **投资建议**：结合情绪分析给出投资建议
- **置信度评估**：提供分析结果的可信度评分

### 💼 持仓管理
- **持仓记录**：记录买入价、数量、日期
- **实时盈亏**：自动计算每只股票和总体盈亏
- **分批管理**：支持同一股票多次买入
- **盈亏分析**：盈亏百分比、持仓分布一目了然

### 🔔 智能提醒
- **价格提醒**：设置突破/跌破某价位时通知
- **指标提醒**：RSI 超买/超卖提醒
- **后台监控**：自动检查，触发时 Telegram 通知
- **多条件支持**：同时设置多个股票的多个提醒

### 📊 可视化图表
- **价格走势图**：带 50/200 日均线的价格图
- **RSI 组合图**：价格 + RSI 双图层展示
- **持仓饼图**：直观展示持仓分布和比例
- **自动生成**：一键生成，直接发送到 Telegram

### 🤖 Telegram 机器人
- **智能对话**：`/agent` 前缀触发智能分析
- **简单回复**：普通消息直接LLM回复
- **多轮对话**：支持上下文理解和追问
- **定时推送**：自动发送市场分析和新闻摘要

## 🏢️ 架构设计

### 分层架构
```
EquiMind/
├── mcp_server/                    # 核心服务
│   ├── langchain_agent.py         # LangChain Agent 主控制器
│   ├── telegram_bot.py            # Telegram 机器人服务
│   ├── scheduler.py               # 定时任务调度器
│   ├── news_ingestor.py           # 新闻抓取模块
│   ├── state_store.py             # 数据存储模块
│   └── tools/                     # 工具层
│       ├── data_providers/        # 数据提供层
│       │   ├── stock_data_provider.py      # 股票数据
│       │   └── technical_data_provider.py  # 技术指标
│       ├── strategies/            # 策略层
│       │   └── funnel_strategy.py          # 漏斗策略
│       ├── funnel_strategy_tool_v2.py      # 漏斗工具
│       └── news_tool.py                    # 新闻工具
├── scripts/                       # 运行脚本
│   ├── telegram_polling.py       # Telegram 轮询服务
│   ├── run_scheduler.py           # 定时任务服务
│   └── get_telegram_id.py         # 获取 Telegram ID
├── requirements.txt               # Python 依赖
└── env_example.txt               # 环境变量模板
```

### 设计原则
- **单一职责**：每层只负责特定功能
- **松耦合**：数据层、策略层、工具层完全分离
- **可扩展**：易于添加新策略和数据源
- **可测试**：每层都可独立测试和调试

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
# 复制环境变量示例文件
cp env_example.txt .env

# 编辑 .env 文件，配置以下必需参数：

# LLM 配置（三选一）
EQUIMIND_LLM_PROVIDER=openai  # 或 vllm、openrouter
OPENAI_API_KEY=your_openai_api_key

# Telegram 机器人配置
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_default_chat_id

# 新闻源配置
NEWS_RSS_SOURCES=https://feeds.finance.yahoo.com/rss/2.0/headline
NEWS_POLL_INTERVAL_MIN=60

# 定时推送配置
MORNING_DIGEST_TIME=08:00
EVENING_DIGEST_TIME=18:00
```

> 💡 获取 Telegram Bot Token 和 Chat ID，请使用 `python scripts/get_telegram_id.py`

### 3. 启动 Telegram 机器人
```bash
# 启动 Telegram 轮询服务
python scripts/telegram_polling.py
```

### 4. 启动定时任务（可选）
```bash
# 在另一个终端启动定时任务服务
python scripts/run_scheduler.py

# 启动提醒检查服务（如果使用智能提醒功能）
python scripts/check_alerts.py
```

### 5. 开始使用
在 Telegram 中找到你的机器人，发送以下消息进行测试：

#### 股票分析
- `/agent 分析一下 NVDA 现在怎么样？`
- `/agent 帮我扫描一下所有护城河股票，看看有没有黄金买点`

#### 新闻与情绪
- `/agent 帮我看看最近有什么重要的科技新闻`
- `/agent 分析一下当前AI板块的市场情绪`

#### 持仓管理
- `/agent 添加持仓 AAPL 100股 买入价150美元`
- `/agent 查看我的持仓和盈亏`
- `/agent 移除 AAPL 的持仓`

#### 智能提醒
- `/agent 提醒我 NVDA 跌破 400 美元`
- `/agent 设置 AAPL 的 RSI 低于 30 时提醒我`
- `/agent 查看我的所有提醒`

#### 图表生成
- `/agent 生成 NVDA 的价格走势图`
- `/agent 生成 AAPL 的价格+RSI组合图`
- `/agent 生成我的持仓饼图`

#### 综合分析
- `/agent 结合最新新闻和技术分析，给我一些投资建议`


## 贡献指南
欢迎提交 Issue 和 Pull Request！

## 许可证
MIT License
