class BaseTool:
    def run(self, context, inputs):
        raise NotImplementedError('工具必须实现 run 方法') 