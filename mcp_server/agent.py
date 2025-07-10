from mcp_server.base_tool import BaseTool
from mcp_server.tools.smart_stock_screening import SmartStockScreeningTool

class Agent:
    def __init__(self):
        self.tools = {}
        self.register_tool('smart_stock_screening', SmartStockScreeningTool())

    def register_tool(self, name: str, tool: BaseTool):
        self.tools[name] = tool

    def handle(self, mcp_message):
        tool_name = mcp_message.tool_name
        tool = self.tools.get(tool_name)
        if not tool:
            return {'error': f'工具 {tool_name} 未注册'}
        return tool.run(mcp_message.context, mcp_message.inputs) 