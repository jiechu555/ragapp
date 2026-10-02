# -*- coding: utf-8 -*-
"""混合检索：向量 + BM25 双路，RRF(k=60) 融合。

方法论自 mall RAG 模块（Java 实现）移植：
- rrf_fuse：每路文档得分 = Σ 1/(k+rank)，跨路求和（共识信号），只依赖排名不依赖分数
  量纲——BM25 分数无上界、向量相似度 [-1,1]，直接加权是无意义运算。
- bm25_score：自研紧凑实现（k1/b 标准参数，CJK 二元分词 + ASCII 词元），
  小语料零依赖；生产规模可替换 llama-index-retrievers-bm25。
- HybridRetriever：BaseRetriever 子类，向量路与 BM25 路各取 top_n 后 RRF 融合，
  输出语义与单路检索器一致（node_postprocessors/citation 链不受影响）。
"""
import json
import logging
import math
import os
import re
from typing import Any, List, Optional

from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.base.llms.types import TextBlock  # noqa: F401
from llama_index.core.schema import BaseNode, NodeWithScore, TextNode

logger = logging.getLogger("uvicorn")

RRF_K = 60  # Cormack et al. 2009 经验值：平滑头部差距，让两路共识胜出

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


def tokenize(text: str) -> List[str]:
    """CJK 字符二元切分 + ASCII 词元（小写）。中文无空格分词，二元是紧凑近似。"""
    tokens: List[str] = []
    for raw in re.findall(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]+", text.lower()):
        if _CJK_RE.search(raw):
            if len(raw) == 1:
                tokens.append(raw)
            else:
                tokens.extend(raw[i : i + 2] for i in range(len(raw) - 1))
        else:
            tokens.append(raw)
    return tokens


def bm25_scores(
    query_tokens: List[str],
    corpus_tokens: List[List[str]],
    k1: float = 1.5,
    b: float = 0.75,
) -> List[float]:
    """标准 BM25 打分。corpus_tokens[i] 为第 i 篇文档的词元列表。"""
    n = len(corpus_tokens)
    if n == 0:
        return []
    avgdl = sum(len(d) for d in corpus_tokens) / n
    tf_per_doc = []
    for doc in corpus_tokens:
        tf: dict = {}
        for t in doc:
            tf[t] = tf.get(t, 0) + 1
        tf_per_doc.append(tf)
    scores = []
    for doc_tf in tf_per_doc:
        score = 0.0
        for qt in query_tokens:
            f = doc_tf.get(qt, 0)
            if f == 0:
                continue
            # 含 query 词的文档数（用全语料重算会 O(n²)，这里按查询词惰性统计）
            df = sum(1 for tfd in tf_per_doc if qt in tfd)
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            score += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * len(doc_tf) / (avgdl or 1)))
        scores.append(score)
    return scores


def rrf_fuse(ranked_lists: List[List[NodeWithScore]], k: int = RRF_K) -> List[NodeWithScore]:
    """RRF 融合：跨路求和 1/(k+rank)，同文档得分叠加（两路共识 > 单路头部）。
    返回的 NodeWithScore.score 已写为 RRF 融合分（下游 postprocessors 依赖）。"""
    fused: dict = {}
    scores: dict = {}
    for ranked in ranked_lists:
        for rank, nws in enumerate(ranked):
            key = nws.node.node_id
            if key not in fused:
                fused[key] = nws
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
    result = sorted(fused.values(), key=lambda x: scores[x.node.node_id], reverse=True)
    return [NodeWithScore(node=n.node, score=scores[n.node.node_id]) for n in result]


def nodes_from_vector_store(vector_store: Any) -> List[BaseNode]:
    """从 Chroma 等向量库的 _node_content 元数据重建节点（BM25 语料来源）。
    避免引入 docstore 持久化依赖——ragapp 只把向量与节点内容存进向量库。"""
    nodes: List[BaseNode] = []
    try:
        client = vector_store._chroma_collection
        data = client.get(include=["metadatas"])
        for meta in data["metadatas"]:
            raw = (meta or {}).get("_node_content")
            if not raw:
                continue
            payload = json.loads(raw)
            if payload.get("text"):
                nodes.append(TextNode.model_validate(payload))
    except Exception as e:  # noqa: BLE001
        logger.warning("从向量库重建节点失败，BM25 路降级: %s", e)
    return nodes


def _node_passes_filters(node: BaseNode, filters) -> bool:
    """镜像 llama_index MetadataFilters 的最小语义（EQ/NE），BM25 路与向量路过滤对齐。"""
    if not filters:
        return True
    flist = getattr(filters, "filters", None) or []
    for f in flist:
        val = node.metadata.get(f.key)
        if f.operator.value == "==":
            if str(val) != str(f.value):
                return False
        elif f.operator.value == "!=":
            if str(val) == str(f.value):
                return False
        # 其他算子（IN/GT 等）语料小场景暂不支撑，默认放行
    cond = getattr(filters, "condition", None)
    if cond is not None and getattr(cond, "value", None) == "or" and flist:
        return any(True for _ in flist)  # OR 语义简化：任一通过（当前场景仅 AND）
    return True


class HybridRetriever(BaseRetriever):
    """向量路（复用 index 自带 retriever，含 Chroma 过滤）+ BM25 路（自研打分）→ RRF。"""

    def __init__(
        self,
        vector_retriever: BaseRetriever,
        nodes: List[BaseNode],
        top_k: int = 3,
        filters=None,
    ) -> None:
        super().__init__()
        self._vector_retriever = vector_retriever
        self._filters = filters
        self._top_k = top_k
        self._set_nodes(nodes)

    def _set_nodes(self, nodes: List[BaseNode]) -> None:
        self._nodes = [n for n in nodes if _node_passes_filters(n, self._filters)]
        self._corpus_tokens = [tokenize(n.get_content()) for n in self._nodes]

    def refresh_nodes(self, nodes: List[BaseNode]) -> None:
        self._set_nodes(nodes)

    def _retrieve(self, query, **kwargs: Any) -> List[NodeWithScore]:
        # llama_index 标准路径传入 QueryBundle（含 query_str 与 query_embedding）
        query_str = getattr(query, "query_str", None) or str(query)
        vector_hits = self._vector_retriever.retrieve(query)
        q_tokens = tokenize(query_str)
        scores = bm25_scores(q_tokens, self._corpus_tokens)
        ranked = sorted(
            zip(self._nodes, scores), key=lambda x: x[1], reverse=True
        )
        bm25_hits = [
            NodeWithScore(node=n, score=s)
            for n, s in ranked[: self._top_k]
            if s > 0
        ]
        return rrf_fuse([vector_hits, bm25_hits])[: self._top_k]
