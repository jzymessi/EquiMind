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

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置")
    # 只保留API配置
    api_url = st.text_input(
        "MCP Server URL",
        value="http://localhost:8000",
        help="EquiMind MCP Server 地址"
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

# 聊天历史缓存
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

st.title("🤖 EquiMind - 智能投资助手")
st.markdown("基于 LangChain + LangGraph 的智能投资决策平台")

col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 智能对话")
    # 聊天气泡区
    for msg in st.session_state["chat_history"]:
        if msg["role"] == "user":
            st.markdown(f"<div style='text-align:right;background:#e6f7ff;padding:8px 12px;border-radius:8px;margin:4px 0 4px 40px;'><b>你：</b> {msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:left;background:#f6f6f6;padding:8px 12px;border-radius:8px;margin:4px 40px 4px 0;'><b>AI：</b> {msg['content']}</div>", unsafe_allow_html=True)
    # 用户输入
    if "user_query_input" not in st.session_state:
        st.session_state["user_query_input"] = ""
    def on_user_input():
        user_query = st.session_state["user_query_input"]
        if user_query:
            st.session_state["chat_history"].append({"role": "user", "content": user_query})
            st.session_state["user_query_input"] = ""
    user_query = st.text_input(
        "请输入你的投资需求",
        placeholder="例如：帮我推荐5个现在适合投资的美股",
        key="user_query_input",
        on_change=on_user_input
    )
    context = st.text_area(
        "上下文信息（可选）",
        value='{"user_id": "leo", "risk_preference": "moderate"}',
        height=80,
        help="JSON 格式的上下文信息"
    )
    # 只在有新user消息且未被AI回复时才请求AI
    if (
        st.session_state["chat_history"]
        and st.session_state["chat_history"][-1]["role"] == "user"
    ):
        with st.spinner("正在分析..."):
            try:
                response = requests.post(
                    f"{api_url}/agent/query",
                    json={
                        "user_query": st.session_state["chat_history"][-1]["content"],
                        "context": json.loads(context) if context else {}
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    ai_reply = result.get("response", "")
                    st.session_state["chat_history"].append({"role": "ai", "content": ai_reply})
                    st.success("分析完成！")
                    # st.json(result) 
                    # 展示Agent LLM result调试信息
                    st.subheader("🤖 Agent 回复")
                    st.markdown(result.get("response", ""))
                else:
                    st.session_state["chat_history"].append({"role": "ai", "content": f"请求失败: {response.status_code}"})
                    st.error(f"请求失败: {response.status_code}")
            except Exception as e:
                st.session_state["chat_history"].append({"role": "ai", "content": f"连接失败: {e}"})
                st.error(f"连接失败: {e}")

with col2:
    st.header("📚 功能说明")
    st.markdown("""
    ### 🚀 新功能特性
    - 智能 Agent 对话式投资决策
    - 多因子智能选股
    - 上下文记忆与多轮追问
    - 结构化结果与可视化支持
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