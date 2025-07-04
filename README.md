# EquiMind

EquiMind 是一个基于 MCP（模型上下文协议，Model Context Protocol）的智能股票买卖 Agent 平台。它支持多工具集成、上下文驱动的智能决策，并可通过 API 实现自动化选股、消息推送和交易。

## 项目定位
- 智能量化投资 Agent
- 支持多工具插件（行情、策略、推送、交易等）
- 基于 MCP 协议，统一上下文和消息格式
- 可扩展、可集成、自动化

## 主要功能
- 实时获取股票行情数据
- 低估值股票智能筛选（可扩展多种策略）
- 消息推送到手机/终端
- 自动化交易接口（可扩展）
- 提供标准化 API 服务

## 架构说明
```
EquiMind/
  ├── mcp_server/                # MCP Agent Server
  │     ├── server.py            # FastAPI 主服务，MCP协议入口
  │     ├── mcp_protocol.py      # MCP协议实现（上下文格式、消息封装等）
  │     ├── agent.py             # Agent主逻辑，负责调度工具
  │     ├── base_tool.py         # 工具基类
  │     └── tools/               # MCP工具目录
  │           ├── stock_data.py  # 行情工具示例
  │           ├── us_stock_data.py # 美股行情工具
  ├── frontend_streamlit/        # Streamlit 前端
  │     └── app.py               # 前端主页面
  ├── requirements.txt           # 依赖包
  ├── config.py                  # 配置文件
  └── .openrouter_key            # OpenRouter API Key 文件
```

## 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **启动 MCP Server**
   ```bash
   uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000
   ```

3. **准备 OpenRouter API Key**
   - 在项目根目录下新建 `.openrouter_key` 文件，并将你的 OpenRouter API Key 填入（只需一行）。

4. **运行前端页面**
   ```bash
   streamlit run frontend_streamlit/app.py
   ```

5. **在浏览器访问前端页面**
   - 输入你的需求（如“查询微软2024年6月1日至6月10日的日K线”）
   - 选择大模型（如 qwen/qwen3-32b:free 等）
   - 点击“生成 MCP 请求” → 自动生成 JSON
   - 点击“调用 MCP 工具” → 结果展示
   - 点击“生成总结” → LLM 自动总结行情要点


## MCP 协议说明
- 统一的 JSON 消息格式：
```json
{
  "context": {"user_id": "leo"},
  "tool_name": "us_stock_data",
  "inputs": {
    "symbol": "AAPL",
    "type": "history",
    "start": "2024-06-01",
    "end": "2024-06-10",
    "interval": "1d"
  }
}
```
- type 可选：
  - current（当前价格）
  - history（历史价格）
  - kline（K线数据）
  - change（涨跌幅）
- start/end/interval 用于指定查询区间和K线周期

## 典型使用例子

### 例1：查询美股当前价格
- **输入需求**：查一下苹果公司股价
- **生成的 JSON**：
  ```json
  {
    "context": {"user_id": "leo"},
    "tool_name": "us_stock_data",
    "inputs": {
      "symbol": "AAPL",
      "type": "current"
    }
  }
  ```
- **返回结果**：
  ```json
  {
    "outputs": {
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "price": 190.5,
      "currency": "USD"
    }
  }
  ```
- **智能总结**：
  > 苹果公司（AAPL）当前股价为190.5美元，投资者可关注其后续走势。

### 例2：查询历史价格
- **输入需求**：查询特斯拉2024年6月1日至6月10日的历史收盘价
- **生成的 JSON**：
  ```json
  {
    "context": {"user_id": "leo"},
    "tool_name": "us_stock_data",
    "inputs": {
      "symbol": "TSLA",
      "type": "history",
      "start": "2024-06-01",
      "end": "2024-06-10"
    }
  }
  ```
- **返回结果**：
  ```json
  {
    "outputs": {
      "symbol": "TSLA",
      "history_close": {
        "2024-06-03": 180.2,
        "2024-06-04": 182.5
      }
    }
  }
  ```
- **智能总结**：
  > 特斯拉（TSLA）在2024年6月1日至6月10日期间收盘价整体呈现小幅上涨，建议关注其后续表现。

### 例3：查询K线数据
- **输入需求**：查询微软2024年6月1日至6月10日的日K线
- **生成的 JSON**：
  ```json
  {
    "context": {"user_id": "leo"},
    "tool_name": "us_stock_data",
    "inputs": {
      "symbol": "MSFT",
      "type": "kline",
      "start": "2024-06-01",
      "end": "2024-06-10",
      "interval": "1d"
    }
  }
  ```
- **返回结果**：返回日K线数据（包含开盘、收盘、最高、最低、成交量等）。
- **智能总结**：
  > 微软（MSFT）在该区间内波动较小，整体走势平稳，建议结合基本面进一步分析。

### 例4：查询涨跌幅
- **输入需求**：查询谷歌2024年6月1日至6月10日的涨跌幅
- **生成的 JSON**：
  ```json
  {
    "context": {"user_id": "leo"},
    "tool_name": "us_stock_data",
    "inputs": {
      "symbol": "GOOG",
      "type": "change",
      "start": "2024-06-01",
      "end": "2024-06-10"
    }
  }
  ```
- **返回结果**：
  ```json
  {
    "outputs": {
      "symbol": "GOOG",
      "start_price": 170.0,
      "end_price": 175.0,
      "pct_change": 2.94
    }
  }
  ```
- **智能总结**：
  > 谷歌（GOOG）在2024年6月1日至6月10日期间上涨了2.94%，表现优于大盘。


## 扩展方式
- 新增工具：在 `mcp_server/tools/` 目录下添加新模块，并继承 `BaseTool` 实现 `run` 方法。
- 注册工具：在 `agent.py` 中注册新工具。
- 扩展协议/上下文：修改 `mcp_protocol.py` 和 Agent 逻辑。

## 适用场景
- 智能量化投资
- 多 Agent 协作
- 自动化金融决策
- 可扩展的智能工具平台

---
如需扩展功能或有其他需求，欢迎随时交流！

---
