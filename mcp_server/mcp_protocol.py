from typing import Dict, Any

class MCPMessage:
    def __init__(self, context: Dict[str, Any], tool_name: str, inputs: Dict[str, Any]):
        self.context = context
        self.tool_name = tool_name
        self.inputs = inputs

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            context=data.get('context', {}),
            tool_name=data.get('tool_name', ''),
            inputs=data.get('inputs', {})
        )

    def to_dict(self):
        return {
            'context': self.context,
            'tool_name': self.tool_name,
            'inputs': self.inputs
        } 