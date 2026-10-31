import json
import re
import time
from typing import Any

import httpx
from fastapi import HTTPException

from app.config import (
    MINIMAX_API_KEY,
    MINIMAX_BASE_URL,
    MINIMAX_MAX_TOKENS,
    MINIMAX_MODEL,
    MINIMAX_TIMEOUT_SECONDS,
)

SYSTEM_PROMPT = """你是一个专业的 HTML5 Canvas 小游戏生成器。根据用户需求生成完整、可直接运行的 2D 单人浏览器小游戏。

硬性要求：
1. 只返回严格 JSON 对象，不要 Markdown、代码围栏或任何解释，格式为 {"title":"...","description":"...","html":"..."}。
2. html 必须是完整单文件 HTML，包含内联 CSS 和 JavaScript，不得依赖任何外部图片、字体、音频、脚本、样式或网络请求。
3. 使用 Canvas 绘制画面，包含清晰的操作说明、开始或重新开始、得分或胜负反馈、游戏结束状态。
4. 游戏必须立即可玩，逻辑完整，支持键盘操作；适合时同时提供触摸按钮，画面可随窗口缩放。
5. 只使用程序绘制的图形、文字和简单粒子效果，不使用 alert，不访问 parent、localStorage、Cookie 或浏览器敏感能力。
6. 代码必须妥善处理动画循环、碰撞检测、输入状态和重新开始，避免重复注册定时器。
7. title 不超过 30 个汉字，description 用简洁中文说明玩法，JSON 必须正确转义 HTML 字符串。
"""

GENERATION_HINT = "请根据以下需求生成游戏，并严格遵守输出协议：\n"


def validate_game_html(html: str) -> None:
    """校验保存或预览前的基本 HTML 结构与资源约束。"""
    if len(html) < 100 or len(html) > 400_000:
        raise ValueError("游戏 HTML 长度不合法")

    lower = html.lower()
    required = ("<html", "</html>", "<canvas", "<script")
    if any(token not in lower for token in required):
        raise ValueError("模型未返回完整的 Canvas HTML 游戏")

    forbidden = (
        "<iframe",
        "<object",
        "<embed",
        "<link",
        "<img",
        "fetch(",
        "xmlhttprequest",
        "websocket(",
        "localstorage",
        "sessionstorage",
        "document.cookie",
    )
    if any(token in lower for token in forbidden):
        raise ValueError("游戏包含禁止的外部资源或浏览器访问能力")

    if re.search(r"<script[^>]+\bsrc\s*=", lower):
        raise ValueError("游戏不能加载外部脚本")
    if re.search(r"(?:src|href)\s*=\s*['\"]\s*https?://", lower):
        raise ValueError("游戏不能引用外部资源")


def _parse_game_content(content: str) -> dict[str, str]:
    text = content.strip()
    if not text or text.startswith("```"):
        raise ValueError("模型输出包含代码围栏或空内容")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"模型输出不是严格 JSON：{exc.msg}") from exc

    if not isinstance(data, dict):
        raise ValueError("模型输出必须是 JSON 对象")

    result: dict[str, str] = {}
    for key in ("title", "description", "html"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"模型输出缺少有效字段：{key}")
        result[key] = value.strip()

    result["title"] = result["title"][:100]
    validate_game_html(result["html"])
    return result


async def _call_minimax(messages: list[dict[str, str]], temperature: float) -> str:
    if not MINIMAX_API_KEY:
        raise HTTPException(status_code=503, detail="尚未配置 MINIMAX_API_KEY，请在 backend/.env 中设置")

    payload = {
        "model": MINIMAX_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": MINIMAX_MAX_TOKENS,
    }
    timeout = httpx.Timeout(MINIMAX_TIMEOUT_SECONDS, connect=15)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{MINIMAX_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {MINIMAX_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="MiniMax 生成超时，请稍后重试") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="无法连接 MiniMax 服务") from exc

    if response.status_code != 200:
        message = ""
        try:
            message = response.json().get("error", {}).get("message", "")
        except (ValueError, AttributeError):
            message = ""
        suffix = f"：{message[:160]}" if message else ""
        raise HTTPException(
            status_code=502,
            detail=f"MiniMax 调用失败（HTTP {response.status_code}）{suffix}",
        )

    try:
        content: Any = response.json()["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        if not isinstance(content, str) or not content.strip():
            raise ValueError("empty content")
        return content
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise HTTPException(status_code=502, detail="MiniMax 返回了无法识别的响应") from exc


async def _generate_with_repair(messages: list[dict[str, str]]) -> dict[str, Any]:
    started = time.perf_counter()
    content = await _call_minimax(messages, temperature=0.65)
    try:
        draft = _parse_game_content(content)
    except ValueError as first_error:
        repair_messages = messages + [
            {"role": "assistant", "content": content},
            {
                "role": "user",
                "content": (
                    f"上一次输出未通过校验：{first_error}。"
                    "请修复并重新返回完整结果，只输出符合要求的严格 JSON，不要使用 Markdown。"
                ),
            },
        ]
        repaired_content = await _call_minimax(repair_messages, temperature=0.2)
        try:
            draft = _parse_game_content(repaired_content)
        except ValueError as second_error:
            raise HTTPException(
                status_code=502,
                detail=f"生成结果校验失败，自动修复后仍不合格：{second_error}",
            ) from second_error

    return {
        **draft,
        "generation_ms": round((time.perf_counter() - started) * 1000),
        "model_name": MINIMAX_MODEL,
    }


async def generate_game(prompt: str) -> dict[str, Any]:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": GENERATION_HINT + prompt},
    ]
    return await _generate_with_repair(messages)


async def revise_game(original_prompt: str, current_html: str, instruction: str) -> dict[str, Any]:
    validate_game_html(current_html)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "请基于当前游戏和用户修改意见生成完整的新版本，保留未要求修改的玩法。"
                "不要只返回代码片段，仍须返回完整严格 JSON。\n\n"
                f"【原始需求】\n{original_prompt}\n\n"
                f"【当前 HTML】\n{current_html}\n\n"
                f"【本次修改意见】\n{instruction}"
            ),
        },
    ]
    return await _generate_with_repair(messages)
