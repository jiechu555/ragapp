# -*- coding: utf-8 -*-
"""hybrid.py 单测：RRF 融合数学 / BM25 排序 / 分词（mall 同款用例的 Python 版）"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llama_index.core.schema import NodeWithScore, TextNode
from backend.engine.hybrid import bm25_scores, rrf_fuse, tokenize


def _nws(node_id: str) -> NodeWithScore:
    return NodeWithScore(node=TextNode(id_=node_id, text=node_id), score=0.0)


def test_tokenize_中文二元与英文词元():
    toks = tokenize("X1 咖啡机保修 Coffee")
    assert "咖啡" in toks and "啡机" in toks  # CJK 二元
    assert "coffee" in toks and "x1" in toks  # ASCII 小写词元


def test_rrf_两路共识胜过单路头部():
    # B 在两路都出现（rank2 + rank1），A 只在路1 头部——共识文档应胜出
    fused = rrf_fuse([[_nws("A"), _nws("B")], [_nws("B")]])
    assert fused[0].node.node_id == "B"


def test_rrf_分数与公式一致():
    fused = rrf_fuse([[_nws("A")], []], k=60)
    # 单路第一名 = 1/(60+1)
    assert abs(fused[0].score - 1 / 61) < 1e-9


def test_bm25_精确词命中排前():
    corpus = [tokenize(t) for t in ["1450 瓦 预热 40 秒", "1600 瓦 预热 30 秒 自动清洗"]]
    scores = bm25_scores(tokenize("1450"), corpus)
    assert scores[0] > scores[1]  # 含 1450 的文档得分更高
    assert scores[1] == 0.0


def test_rrf_空路与去重():
    fused = rrf_fuse([[], [_nws("A")], [_nws("A")]])
    # A 在路2、路3 都是 rank1：得分 = 2 × 1/61
    assert len(fused) == 1 and abs(fused[0].score - 2 / 61) < 1e-9
