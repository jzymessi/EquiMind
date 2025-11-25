"""
Telegram 机器人模块
支持：发送消息、接收消息、自动回复
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

from .langchain_agent import equimind_agent

TELEGRAM_API_BASE = "https://api.telegram.org"


def _get_bot_token() -> Optional[str]:
    """从环境变量中读取 Telegram Bot Token。"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        return token.strip()
    return None


def get_default_chat_id() -> Optional[str]:
    """获取默认推送目标 chat_id（用于定时推送等场景）。"""
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if chat_id:
        return chat_id.strip()
    return None


def send_telegram_message(
    chat_id: str,
    text: str,
    *,
    parse_mode: Optional[str] = None,
    disable_web_page_preview: bool = True,
) -> Dict[str, Any]:
    """
    发送 Telegram 文本消息。

    Args:
        chat_id: 接收者 chat_id（群或用户）
        text: 消息文本
        parse_mode: MarkdownV2 / HTML / Markdown（可选）
        disable_web_page_preview: 是否禁用链接预览
    """
    token = _get_bot_token()
    if not token:
        return {"success": False, "error": "TELEGRAM_BOT_TOKEN 未配置"}

    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": disable_web_page_preview,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            return {"success": True, "result": data.get("result")}
        return {"success": False, "error": data.get("description", "未知错误")}
    except requests.RequestException as exc:
        return {"success": False, "error": str(exc)}


def handle_telegram_update(update: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理 Telegram Webhook 更新。
    自动调用 Agent 生成回复并回发给用户。
    """
    token = _get_bot_token()
    if not token:
        return {"success": False, "error": "TELEGRAM_BOT_TOKEN 未配置"}

    message = (
        update.get("message")
        or update.get("edited_message")
        or update.get("channel_post")
        or update.get("edited_channel_post")
    )
    if not message:
        return {"success": True, "message": "无文本消息，跳过"}

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return {"success": False, "error": "无法解析 chat_id"}

    from_user = message.get("from", {}) or {}
    user_id = from_user.get("id")
    username = from_user.get("username") or from_user.get("first_name", "")
    text = message.get("text", "") or ""

    if not text.strip():
        reply = "目前仅支持文本消息，请输入您的问题。"
        send_telegram_message(str(chat_id), reply)
        return {"success": True, "message": "非文本消息已提示"}

    stripped = text.strip()
    if stripped.lower() in ("/start", "/help"):
        welcome = (
            "👋 欢迎使用 EquiMind 投资助手！\n"
            "发送您的投资问题，例如：“帮我推荐 5 个当前值得关注的美股”。"
        )
        send_telegram_message(str(chat_id), welcome)
        return {"success": True, "message": "发送欢迎语"}

    print(f"[Telegram] 收到消息: {stripped} (来自: {user_id} / {username})")

    # 如果以 /agent 开头，则走完整 Agent 工作流（带工具、多步骤推理）
    if stripped.lower().startswith("/agent"):
        query = stripped[len("/agent"):].strip() or "请根据当前市场情况，给出一份投资分析。"
        result = equimind_agent.handle_query(
            user_query=query,
            context={"user_id": str(user_id or ""), "platform": "telegram"},
        )

        if result.get("success"):
            reply_text = result.get("response", "抱歉，我暂时无法给出投资建议。")
            send_result = send_telegram_message(str(chat_id), reply_text)
            if send_result.get("success"):
                print(f"[Telegram] [Agent] 已回复消息到 {chat_id}")
            else:
                print(f"[Telegram] [Agent] 回复失败: {send_result.get('error')}")
            return {"success": True, "message": "Agent 消息已处理", "response": reply_text}

        error_msg = result.get("error", "unknown error")
        send_telegram_message(str(chat_id), f"Agent 处理失败：{error_msg}")
        return {"success": False, "error": error_msg}

    # 默认：走简单 LLM 问答，响应更快，不使用工具
    try:
        reply_text = equimind_agent.simple_reply(stripped)
    except Exception as e:
        error_msg = str(e)
        send_telegram_message(str(chat_id), f"处理失败：{error_msg}")
        return {"success": False, "error": error_msg}

    send_result = send_telegram_message(str(chat_id), reply_text or "抱歉，我暂时无法回答这个问题。")
    if send_result.get("success"):
        print(f"[Telegram] 已回复消息到 {chat_id}")
    else:
        print(f"[Telegram] 回复失败: {send_result.get('error')}")
    return {"success": True, "message": "消息已处理", "response": reply_text}


def broadcast_digest(text: str) -> Dict[str, Any]:
    """
    用于定时任务的推送方法。
    优先使用环境变量中的 TELEGRAM_CHAT_ID。
    """
    chat_id = get_default_chat_id()
    if not chat_id:
        return {"success": False, "error": "TELEGRAM_CHAT_ID 未配置"}
    return send_telegram_message(chat_id, text)


