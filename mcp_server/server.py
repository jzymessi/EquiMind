from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv
from fastapi.responses import JSONResponse

# 加载环境变量
load_dotenv()

# 导入 LangChain 组件
from mcp_server.langchain_agent import equimind_agent
from mcp_server.investment_workflow import investment_workflow, analyze_stock
from langchain.schema import HumanMessage

app = FastAPI(title="EquiMind MCP Server", version="2.0.0")

class MCPMessage(BaseModel):
    context: Dict[str, Any] = {}
    tool_name: Optional[str] = None
    inputs: Dict[str, Any] = {}
    user_query: Optional[str] = None

class WorkflowRequest(BaseModel):
    user_query: str
    context: Dict[str, Any] = {}

@app.get("/")
async def root():
    return {"message": "EquiMind MCP Server v2.0 - Powered by LangChain"}

@app.get("/tools")
async def get_tools():
    """获取可用工具列表"""
    tools = equimind_agent.get_available_tools()
    return {"tools": tools}

@app.post("/agent/query")
async def agent_query(request: MCPMessage):
    """LangChain Agent 查询接口"""
    try:
        if not request.user_query:
            raise HTTPException(status_code=400, detail="用户查询不能为空")
        
        result = equimind_agent.handle_query(
            user_query=request.user_query,
            context=request.context
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workflow/investment")
async def investment_workflow_query(request: WorkflowRequest):
    """投资决策工作流接口"""
    try:
        # 初始化工作流状态
        initial_state = {
            "messages": [HumanMessage(content=request.user_query)],
            "user_query": request.user_query,
            "market_analysis": {},
            "stock_screening": {},
            "risk_assessment": {},
            "final_recommendation": {}
        }
        
        # 执行工作流
        result = investment_workflow.invoke(initial_state)
        
        return {
            "success": True,
            "workflow_result": result,
            "final_recommendation": result.get("final_recommendation", {}),
            "messages": [msg.content for msg in result.get("messages", [])]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/call")
async def mcp_call(request: MCPMessage):
    """兼容原有的 MCP 调用接口"""
    try:
        if request.tool_name:
            # 直接工具调用（兼容旧接口）
            if request.tool_name == "smart_stock_screening":
                from mcp_server.tools.langchain_tools import SmartStockScreeningTool
                tool = SmartStockScreeningTool()
                result = tool._run(**request.inputs)
                return {"outputs": result}
            elif request.tool_name == "us_stock_data":
                from mcp_server.tools.langchain_tools import USStockDataTool
                tool = USStockDataTool()
                result = tool._run(**request.inputs)
                return {"outputs": result}
            else:
                raise HTTPException(status_code=400, detail=f"未知工具: {request.tool_name}")
        else:
            # 使用 LangChain Agent
            if not request.user_query:
                raise HTTPException(status_code=400, detail="用户查询不能为空")
            
            result = equimind_agent.handle_query(
                user_query=request.user_query,
                context=request.context
            )
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze_stock")
async def api_analyze_stock(request: Request):
    data = await request.json()
    industry_or_code = data.get("industry_or_code", "")
    result = analyze_stock(industry_or_code)
    return JSONResponse(content=result)

@app.post("/agent/clear")
async def clear_agent_memory():
    """清除 Agent 记忆"""
    try:
        equimind_agent.clear_memory()
        return {"success": True, "message": "记忆已清除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 