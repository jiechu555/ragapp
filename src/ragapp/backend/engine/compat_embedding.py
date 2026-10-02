# -*- coding: utf-8 -*-
"""自定义 OpenAI 兼容端点 Embedding（ragapp 二开，替代 llama-index-embeddings-openai-like）。

为什么不依赖 openai-like 包：其全版本线要求 llama-index-embeddings-openai>=0.3/0.5/0.6，
与 ragapp 锁定的 0.2.5 冲突（poetry 解不开）。自实现只依赖 llama_index-core 的
BaseEmbedding 抽象 + requests 直连 /embeddings——60 行，零版本约束，且 embed 与
cache 解耦（cache 子类同样适用于任何 BaseEmbedding）。
"""
import logging
from typing import Any, List, Optional

import requests
from llama_index.core.base.embeddings.base import BaseEmbedding
from pydantic import Field

logger = logging.getLogger("uvicorn")


class OpenAICompatEmbedding(BaseEmbedding):
    """任意 OpenAI 兼容 /embeddings 端点（智谱/SiliconFlow/本地 vLLM 等）。

    BaseEmbedding 要求模型名必须可枚举——本类的意义就是打破这个约束：
    model_name 任意、api_base 任意、dimensions 由端点决定。
    """

    api_base: str = Field(default="https://open.bigmodel.cn/api/paas/v4")
    api_key: Optional[str] = Field(default=None)
    timeout: float = Field(default=60.0)

    def __init__(self, model_name: str, api_base: str, api_key: str,
                 dimensions: Optional[int] = None, **kwargs: Any):
        super().__init__(
            model_name=model_name,
            api_base=api_base,
            api_key=api_key,
            dimensions=dimensions,
            **kwargs,
        )

    @classmethod
    def class_name(cls) -> str:
        return "OpenAICompatEmbedding"

    def _call_api(self, texts: List[str]) -> List[List[float]]:
        resp = requests.post(
            f"{self.api_base.rstrip('/')}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"input": texts, "model": self.model_name},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()["data"]
        return [d["embedding"] for d in data]

    def _get_query_embedding(self, query: str) -> List[float]:
        return self._call_api([query])[0]

    async def _aget_query_embedding(self, query: str) -> List[float]:
        return self._get_query_embedding(query)

    def _get_text_embedding(self, text: str) -> List[float]:
        return self._call_api([text])[0]

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self._call_api(texts)
