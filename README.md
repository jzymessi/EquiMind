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
  ├── requirements.txt           # 依赖包
  └── config.py                  # 配置文件
```

## MCP 协议说明
- 统一的 JSON 消息格式：
```json
{
  "context": {"user_id": "leo"},
  "tool_name": "stock_data",
  "inputs": {"symbol": "600519"}
}
```
- Agent 根据 tool_name 自动调度对应工具，返回标准 outputs 字段。

## 快速开始
1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
2. 启动服务
   ```bash
   uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000
   ```
3. 发送 MCP 请求（如用 curl 或 Postman）：
   ```json
   POST http://localhost:8000/mcp
   {
     "context": {"user_id": "leo"},
     "tool_name": "stock_data",
     "inputs": {"symbol": "600519"}
   }
   ```
   返回：
   ```json
   {
     "outputs": {
       "symbol": "600519",
       "price": 1800.0,
       "pe": 25.0
     }
   }
   ```

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
