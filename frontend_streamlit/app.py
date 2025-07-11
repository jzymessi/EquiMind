import streamlit as st
import requests
import json
import time

# 页面配置
st.set_page_config(
    page_title="EquiMind - 智能投资助手",
    page_icon="📈",
    layout="wide"
)

# 标题
st.title("🤖 EquiMind - 智能投资助手")
st.markdown("基于 LangChain + LangGraph 的智能投资决策平台")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置")
    
    # API 配置
    api_url = st.text_input(
        "MCP Server URL",
        value="http://localhost:8000",
        help="EquiMind MCP Server 地址"
    )
    
    # 模式选择
    mode = st.selectbox(
        "选择模式",
        ["智能 Agent", "投资工作流", "直接工具调用"],
        help="选择不同的处理模式"
    )
    
    # 清除记忆按钮
    if st.button("🧹 清除对话记忆"):
        try:
            response = requests.post(f"{api_url}/agent/clear")
            if response.status_code == 200:
                st.success("记忆已清除")
            else:
                st.error("清除失败")
        except Exception as e:
            st.error(f"连接失败: {e}")

# 主界面
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 智能对话")
    
    # 用户输入
    user_query = st.text_area(
        "请输入你的投资需求",
        placeholder="例如：帮我推荐5个现在适合投资的美股",
        height=100
    )
    
    # 上下文信息
    context = st.text_area(
        "上下文信息（可选）",
        value='{"user_id": "leo", "risk_preference": "moderate"}',
        height=80,
        help="JSON 格式的上下文信息"
    )
    
    # 按钮区域
    col1_1, col1_2, col1_3 = st.columns(3)
    
    with col1_1:
        if st.button("🚀 智能分析", type="primary"):
            if user_query:
                with st.spinner("正在分析..."):
                    try:
                        if mode == "智能 Agent":
                            response = requests.post(
                                f"{api_url}/agent/query",
                                json={
                                    "user_query": user_query,
                                    "context": json.loads(context) if context else {}
                                }
                            )
                        elif mode == "投资工作流":
                            response = requests.post(
                                f"{api_url}/workflow/investment",
                                json={
                                    "user_query": user_query,
                                    "context": json.loads(context) if context else {}
                                }
                            )
                        else:
                            # 直接工具调用
                            response = requests.post(
                                f"{api_url}/mcp/call",
                                json={
                                    "user_query": user_query,
                                    "context": json.loads(context) if context else {}
                                }
                            )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("分析完成！")
                            st.json(result)  # 调试：展示完整后端返回内容
                            # 显示结果
                            if mode == "投资工作流":
                                st.subheader("📊 投资决策结果")
                                if "final_recommendation" in result:
                                    rec = result["final_recommendation"]
                                    st.markdown(f"**推荐建议：**\n{rec.get('recommendation', '')}")
                                    
                                    if "stocks" in rec:
                                        st.subheader("📈 推荐股票")
                                        stocks = rec["stocks"]
                                        for i, stock in enumerate(stocks, 1):
                                            st.markdown(f"""
                                            **{i}. {stock['symbol']}**
                                            - 价格: ${stock['price']}
                                            - 市盈率: {stock['pe']}
                                            - 5日涨幅: {stock['ret_5d']}%
                                            - 行业: {stock['industry']}
                                            """)
                            else:
                                st.subheader("🤖 Agent 回复")
                                st.markdown(result.get("response", ""))
                        else:
                            st.error(f"请求失败: {response.status_code}")
                            
                    except Exception as e:
                        st.error(f"连接失败: {e}")
            else:
                st.warning("请输入查询内容")
    
    with col1_2:
        if st.button("📋 生成 JSON"):
            if user_query:
                # 简单的 JSON 生成逻辑
                if "推荐" in user_query or "筛选" in user_query:
                    generated_json = {
                        "user_query": user_query,
                        "context": json.loads(context) if context else {},
                        "mode": mode
                    }
                else:
                    generated_json = {
                        "user_query": user_query,
                        "context": json.loads(context) if context else {},
                        "mode": mode
                    }
                
                st.json(generated_json)
            else:
                st.warning("请输入查询内容")
    
    with col1_3:
        if st.button("🔄 测试连接"):
            try:
                response = requests.get(f"{api_url}/")
                if response.status_code == 200:
                    st.success("连接成功！")
                    st.info(response.json().get("message", ""))
                else:
                    st.error("连接失败")
            except Exception as e:
                st.error(f"连接失败: {e}")

with col2:
    st.header("📚 功能说明")
    
    st.markdown("""
    ### 🚀 新功能特性
    
    **智能 Agent 模式**
    - 基于 LangChain 的智能对话
    - 自动工具选择
    - 上下文记忆
    
    **投资工作流模式**
    - 多步骤投资决策
    - 市场分析 → 股票筛选 → 风险评估 → 推荐
    - 基于 LangGraph 的工作流编排
    
    **直接工具调用**
    - 兼容原有 MCP 协议
    - 直接调用特定工具
    
    ### 🛠️ 可用工具
    
    1. **智能股票筛选**
       - 根据市盈率、涨幅、行业筛选
       - 专注科技股投资
    
    2. **美股数据查询**
       - 实时价格、历史数据
       - K线、涨跌幅分析
    """)
    
    # 获取工具列表
    try:
        response = requests.get(f"{api_url}/tools")
        if response.status_code == 200:
            tools = response.json().get("tools", [])
            st.subheader("🔧 可用工具")
            for tool in tools:
                st.markdown(f"**{tool['name']}**: {tool['description']}")
    except:
        st.info("无法获取工具列表")

# 底部信息
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>EquiMind v2.0 - Powered by LangChain + LangGraph</p>
    <p>智能投资决策平台</p>
</div>
""", unsafe_allow_html=True) 