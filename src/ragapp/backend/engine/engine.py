import logging
import os
from typing import List, Optional

from app.api.routers.models import ChatMessage
from app.engine.index import IndexConfig, get_index
from llama_index.core.agent import AgentRunner
from llama_index.core.callbacks import CallbackManager
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.settings import Settings

from backend.engine.constants import DEFAULT_MAX_TOP_K, DEFAULT_TOP_K
from backend.engine.postprocessors import NodeCitationProcessor, get_reranker
from backend.workflows.multi import AgentOrchestrator
from backend.workflows.orchestrator import get_agents
from backend.workflows.single import FunctionCallingAgent

logger = logging.getLogger("uvicorn")


def get_retriever(filters=None, params=None, top_k: Optional[int] = None, callback_manager=None):
    """检索器装配（混合/单路由 USE_HYBRID 决定）。chat 路由降级路径复用同一装配。"""
    top_k = top_k or int(os.getenv("TOP_K", "3"))
    index_config = IndexConfig(callback_manager=callback_manager, **(params or {}))
    index = get_index(index_config)
    if index is None:
        raise RuntimeError("Index is not found")
    vector_retriever = index.as_retriever(
        filters=filters,
        **({"similarity_top_k": top_k} if top_k != 0 else {}),
    )
    if os.getenv("USE_HYBRID", "true").lower() == "true":
        from backend.engine.hybrid import HybridRetriever, nodes_from_vector_store

        return HybridRetriever(
            vector_retriever,
            nodes_from_vector_store(index.vector_store),
            top_k=top_k,
            filters=filters,
        )
    return vector_retriever


def get_chat_engine(
    filters=None,
    params=None,
    event_handlers=None,
    chat_history: Optional[List[ChatMessage]] = None,
) -> CondensePlusContextChatEngine | AgentOrchestrator | FunctionCallingAgent:
    """
    Create chat engine based on the configurations.
    If there is only one agent and no tool enabled, use the context chat engine.
    Otherwise, use the agent workflow.
    """

    top_k = int(os.getenv("TOP_K", "3"))
    citation_prompt = os.getenv("SYSTEM_CITATION_PROMPT")
    node_postprocessors = []
    callback_manager = CallbackManager(handlers=event_handlers or [])

    if citation_prompt is not None:
        node_postprocessors.append(NodeCitationProcessor())

    if os.getenv("USE_RERANKER", "False").lower() == "true":
        top_k = max(top_k, DEFAULT_MAX_TOP_K)
        node_postprocessors.append(get_reranker())
    else:
        top_k = int(os.getenv("TOP_K", DEFAULT_TOP_K))

    # We need to create index here because we need to pass the callback manager to the index
    # and we need to pass the index to the agents
    # TODO: Refactor code to create index independently
    index_config = IndexConfig(callback_manager=callback_manager, **(params or {}))
    index = get_index(index_config)
    if index is None:
        raise RuntimeError("Index is not found")

    # 二开：混合检索（向量 + BM25，RRF 融合）。USE_HYBRID=false 可回退单路向量做对照。
    retriever = get_retriever(filters, params, top_k, callback_manager)

    from llama_index.core.query_engine import RetrieverQueryEngine

    query_engine = RetrieverQueryEngine.from_args(
        retriever,
        llm=Settings.llm,
        node_postprocessors=node_postprocessors,
        callback_manager=callback_manager,
    )
    agents = get_agents(chat_history, query_engine)
    if len(agents) == 0:
        raise ValueError("Required at least one agent to run chat engine.")

    if len(agents) == 1:
        agent = agents[0]
        tools = agent.tools
        # Update agent system prompt with citation prompt
        system_prompt = agent.system_prompt
        if citation_prompt is not None:
            system_prompt = f"{system_prompt}\n{citation_prompt}"
        if len(tools) == 1 and tools[0].metadata.name == "QueryEngine":
            return CondensePlusContextChatEngine(
                llm=Settings.llm,
                memory=ChatMemoryBuffer.from_defaults(
                    token_limit=Settings.llm.metadata.context_window - 256
                ),
                system_prompt=system_prompt,
                retriever=retriever,
                node_postprocessors=node_postprocessors,
                callback_manager=callback_manager,
            )
        else:
            return AgentRunner.from_llm(
                llm=Settings.llm,
                tools=tools,
                system_prompt=system_prompt,
                callback_manager=callback_manager,
                verbose=True,
            )
    else:
        return AgentOrchestrator(agents=agents, refine_plan=False)
