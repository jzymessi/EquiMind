from fastapi import FastAPI, Request
from mcp_server.agent import Agent
from mcp_server.mcp_protocol import MCPMessage

app = FastAPI()
agent = Agent()

@app.post('/mcp')
async def mcp_endpoint(request: Request):
    data = await request.json()
    mcp_message = MCPMessage.from_dict(data)
    result = agent.handle(mcp_message)
    return result 