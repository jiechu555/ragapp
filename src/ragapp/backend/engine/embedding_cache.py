# -*- coding: utf-8 -*-
"""embedding 缓存：查询向量按文本 LRU 缓存（ragapp 二开）。

动机：每次问答都要把 condense 后的问题实时向量化，重复问题/相近会话会重复调用
embedding API（commit 3 评测实测该调用占混合检索 P95 的 ~85%）。缓存键 = 文本内容，
LRU 2048 条防内存膨胀。索引期批量向量化走 _get_text_embeddings，同样命中缓存。

实现注记：缓存状态用模块级单例而非 pydantic PrivateAttr——服务进程内所有
embed_model 实例共享同一份缓存才是"缓存"的正确语义，且规避 pydantic v2
copy/model_dump 与可变 PrivateAttr 的交互坑。
"""
import asyncio
import logging
import os
from collections import OrderedDict
from threading import Lock
from typing import List, Optional

from llama_index.embeddings.openai_like import OpenAILikeEmbedding

logger = logging.getLogger("uvicorn")

_CACHE: "OrderedDict[str, List[float]]" = OrderedDict()
_LOCK = Lock()
_MAXSIZE = 2048
_HITS = 0
_MISSES = 0


def _cache_get(key: str) -> Optional[List[float]]:
    global _HITS
    with _LOCK:
        if key in _CACHE:
            _CACHE.move_to_end(key)
            _HITS += 1
            return _CACHE[key]
    return None


def _cache_put(key: str, value: List[float]) -> None:
    global _MISSES
    with _LOCK:
        _CACHE[key] = value
        if len(_CACHE) > _MAXSIZE:
            _CACHE.popitem(last=False)
        _MISSES += 1


class CachedOpenAILikeEmbedding(OpenAILikeEmbedding):
    """OpenAILikeEmbedding 的带 LRU 缓存版本（智谱等自定义端点）。"""

    def _get_query_embedding(self, query: str) -> List[float]:
        key = "q|" + query
        cached = _cache_get(key)
        if cached is not None:
            return cached
        value = super(CachedOpenAILikeEmbedding, self)._get_query_embedding(query)
        _cache_put(key, value)
        return value

    async def _aget_query_embedding(self, query: str) -> List[float]:
        key = "aq|" + query
        cached = _cache_get(key)
        if cached is not None:
            return cached
        value = await super(CachedOpenAILikeEmbedding, self)._aget_query_embedding(query)
        _cache_put(key, value)
        return value

    def _get_text_embedding(self, text: str) -> List[float]:
        key = "t|" + text
        cached = _cache_get(key)
        if cached is not None:
            return cached
        value = super(CachedOpenAILikeEmbedding, self)._get_text_embedding(text)
        _cache_put(key, value)
        return value

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量：命中的走缓存，未命中的父类批量计算后逐条回填。"""
        results: List[Optional[List[float]]] = [None] * len(texts)
        for i, t in enumerate(texts):
            results[i] = _cache_get("t|" + t)
        missing = [(i, t) for i, t in enumerate(texts) if results[i] is None]
        if missing:
            computed = super(CachedOpenAILikeEmbedding, self)._get_text_embeddings(
                [t for _, t in missing]
            )
            for (i, t), v in zip(missing, computed):
                results[i] = v
                _cache_put("t|" + t, v)
        return results  # type: ignore[return-value]

    @staticmethod
    def stats() -> dict:
        return {"hits": _HITS, "misses": _MISSES, "size": len(_CACHE)}


def wrap_with_cache(embed_model):
    """将已装配的 embed_model 替换为缓存版（参数从环境变量重取——pydantic 基类
    不可靠地暴露 model_name；非 OpenAILike 实现原样返回）。"""
    if isinstance(embed_model, CachedOpenAILikeEmbedding):
        return embed_model
    try:
        wrapped = CachedOpenAILikeEmbedding(
            model_name=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            api_base=os.getenv("OPENAI_API_BASE"),
            api_key=os.getenv("OPENAI_API_KEY"),
            dimensions=int(os.getenv("EMBEDDING_DIM")) if os.getenv("EMBEDDING_DIM") else None,
            is_chat_model=False,
        )
        return wrapped
    except Exception as e:  # noqa: BLE001
        logger.warning("embedding 缓存包装失败，使用原始实例: %s", e)
        return embed_model
