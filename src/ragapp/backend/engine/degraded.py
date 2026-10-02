# -*- coding: utf-8 -*-
"""LLM 降级响应：LLM 链路失败时返回检索摘要 + degraded 标记（HTTP 200）。

移植自 mall RAG 的降级策略：客服场景"回答不了"不是系统错误，前端凭
degraded 事件引导转人工。降级内容 = 混合检索 top3 的标题与摘要，用户可自助。
"""
import json
import logging

from fastapi.responses import StreamingResponse

logger = logging.getLogger("uvicorn")


def _vercel_text(text: str) -> str:
    return "0:" + json.dumps(text) + "\n"


def _vercel_data(obj: dict) -> str:
    return "8:" + json.dumps([obj], ensure_ascii=False) + "\n"


async def build_degraded_response(retriever, query: str, reason: str) -> StreamingResponse:
    """检索摘要降级流：与 VercelStreamResponse 同协议（0: 文本 / 8: 事件），前端无感降级。"""
    try:
        nodes = retriever.retrieve(query)[:3]
    except Exception as e:  # noqa: BLE001  检索也挂：纯话术降级
        logger.error("降级检索失败: %s", e)
        nodes = []

    async def generator():
        if nodes:
            yield _vercel_text("智能客服暂时不可用，以下是与您问题最相关的资料：\n")
            for i, n in enumerate(nodes, 1):
                content = n.node.get_content().replace("\n", " ")[:200]
                yield _vercel_text(f"{i}. {n.node.metadata.get('file_name', '')}\n   {content}\n")
        else:
            yield _vercel_text("智能客服暂时不可用，请稍后重试或联系人工客服。")
        yield _vercel_data({"type": "degraded", "data": {"reason": reason, "nodes": len(nodes)}})

    return StreamingResponse(generator(), media_type="text/event-stream")
