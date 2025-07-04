import streamlit as st
import requests
import json
import os

st.set_page_config(page_title="EquiMind LLM-MCP 测试前端", layout="centered")
st.title("EquiMind LLM-MCP 智能工具测试平台")

# 读取本地 OpenRouter API Key
api_key = None
if os.path.exists(".openrouter_key"):
    with open(".openrouter_key", "r") as f:
        api_key = f.read().strip()

if not api_key:
    st.error("请在项目根目录下新建 .openrouter_key 文件，并填入你的 OpenRouter API Key！")

# 1. 用户输入
user_input = st.text_input("请输入你的需求（如：查询微软2024年6月1日至6月10日的日K线）")

# 2. 选择 LLM 模型
model_list = [
    "qwen/qwen3-235b-a22b:free",
    "deepseek/deepseek-r1-0528:free",
    "qwen/qwq-32b:free",
    "google/gemma-3-27b-it:free"
]
selected_model = st.selectbox("选择大模型 (OpenRouter)", model_list)

# 3. MCP Server 地址
mcp_server_url = st.text_input("MCP Server 地址", value="http://localhost:8000/mcp")

# 4. 生成 MCP JSON
if st.button("生成 MCP 请求"):
    if not user_input or not api_key:
        st.warning("请输入需求，并确保 .openrouter_key 文件存在且有内容！")
    else:
        prompt = (
            "你是一个MCP协议助手。请根据用户输入，生成一条用于调用 MCP 协议 us_stock_data 工具的 JSON 请求。"
            "严格只返回如下格式的 JSON，不要代码块、不要解释、不要多余字段：\n"
            "{\n"
            "  \"context\": {\"user_id\": \"leo\"},\n"
            "  \"tool_name\": \"us_stock_data\",\n"
            "  \"inputs\": {\n"
            "    \"symbol\": \"AAPL\",\n"
            "    \"type\": \"history\",\n"
            "    \"start\": \"2024-06-01\",\n"
            "    \"end\": \"2024-06-10\",\n"
            "    \"interval\": \"1d\"\n"
            "  }\n"
            "}\n"
            "其中：type 可选 current(当前价格)、history(历史价格)、kline(K线)、change(涨跌幅)；start/end 为日期，interval 为K线周期（1d/1wk/1mo）。\n"
            f"用户输入：{user_input}"
        )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": "你是MCP协议助手，负责将自然语言转为MCP JSON请求。"},
                {"role": "user", "content": prompt}
            ]
        }
        try:
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            llm_content = resp.json()["choices"][0]["message"]["content"]
            st.code(llm_content, language="json")
            # 尝试解析为 dict
            try:
                mcp_json = json.loads(llm_content)
                st.session_state["mcp_json"] = mcp_json
                st.success("MCP JSON 生成成功！")
            except Exception as e:
                st.error(f"MCP JSON 解析失败: {e}")
        except Exception as e:
            st.error(f"OpenRouter API 调用失败: {e}")

# 5. 调用 MCP Server
if st.button("调用 MCP 工具"):
    mcp_json = st.session_state.get("mcp_json")
    if not mcp_json:
        st.warning("请先生成 MCP JSON！")
    else:
        try:
            resp = requests.post(mcp_server_url, json=mcp_json, timeout=30)
            resp.raise_for_status()
            result_json = resp.json()
            st.subheader("MCP 工具返回结果：")
            st.json(result_json)
            st.session_state["result_json"] = result_json
        except Exception as e:
            st.error(f"MCP Server 调用失败: {e}")

# 6. 自动总结模块
if st.button("生成总结"):
    result_json = st.session_state.get("result_json")
    if not result_json:
        st.warning("请先调用 MCP 工具，获取数据后再生成总结！")
    else:
        summary_prompt = (
            "请用简洁中文总结以下股票行情数据的主要信息和投资提示，只输出总结内容，不要解释：\n"
            f"{json.dumps(result_json, ensure_ascii=False)}"
        )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": "你是金融行情分析助手，擅长用中文总结行情数据。"},
                {"role": "user", "content": summary_prompt}
            ]
        }
        try:
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
            resp.raise_for_status()
            summary = resp.json()["choices"][0]["message"]["content"]
            st.markdown("#### 智能总结：")
            st.write(summary)
        except Exception as e:
            st.error(f"自动总结失败: {e}") 