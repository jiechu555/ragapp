import logging

from app.api.routers.events import EventCallbackHandler
from app.api.routers.models import (
    ChatData,
)
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from llama_index.core.agent import AgentRunner
from llama_index.core.chat_engine import CondensePlusContextChatEngine

from backend.engine import get_chat_engine
from backend.engine.query_filters import generate_filters
from backend.routers.chat.vercel_response import (
    ChatEngineVercelStreamResponse,
    WorkflowVercelStreamResponse,
)

chat_router = r = APIRouter()

logger = logging.getLogger("uvicorn")


@r.post("")
async def chat(
    request: Request,
    data: ChatData,
    background_tasks: BackgroundTasks,
):
    try:
        last_message_content = data.get_last_message_content()
        messages = data.get_history_messages()

        doc_ids = data.get_chat_document_ids()
        filters = generate_filters(doc_ids)
        params = data.data or {}
        logger.info(
            f"Creating chat engine with filters: {str(filters)}",
        )
        event_handler = EventCallbackHandler()
        chat_engine = get_chat_engine(
            filters=filters,
            params=params,
            event_handlers=[event_handler],
            chat_history=messages,
        )

        if isinstance(chat_engine, CondensePlusContextChatEngine) or isinstance(
            chat_engine, AgentRunner
        ):
            event_handler = EventCallbackHandler()
            chat_engine.callback_manager.handlers.append(event_handler)  # type: ignore

            # 二开：急切 await——condense（第一次 LLM 调用）失败能进降级路径，
            # 而不是在流式生成器内部炸成空响应。代价：TTFB 增加 condense 时长（~1s）
            response = await chat_engine.astream_chat(last_message_content, messages)

            async def _resolved(r=response):
                return r

            return ChatEngineVercelStreamResponse(
                request=request,
                event_handler=event_handler,
                chat_data=data,
                response=_resolved(),
                background_tasks=background_tasks,
            )
        else:
            event_handler = chat_engine.run(input=last_message_content, streaming=True)
            return WorkflowVercelStreamResponse(
                request=request,
                chat_data=data,
                event_handler=event_handler,
                events=chat_engine.stream_events(),
            )
    except Exception as e:
        # 二开：LLM 链路失败降级——检索摘要 + degraded 标记（HTTP 200），不再 500
        # （mall RAG 同款策略：客服"回答不了"不是系统错误，前端凭 degraded 引导转人工）
        logger.exception("LLM 链路失败，降级: %s", e)
        try:
            filters = generate_filters(data.get_chat_document_ids())
            from backend.engine.degraded import build_degraded_response
            from backend.engine.engine import get_retriever

            retriever = get_retriever(filters=filters, params=data.data or {})
            return await build_degraded_response(
                retriever, data.get_last_message_content(), reason=str(e)[:200]
            )
        except Exception as inner:  # noqa: BLE001  检索也挂：如实 500
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error in chat engine: {e}; degraded path failed: {inner}",
            ) from inner
