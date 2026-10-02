# -*- coding: utf-8 -*-
"""检索质量评测：单路向量 vs 混合检索（RRF）——mall 方法论的 Python 复刻。

用法：先确保语料已导入（本脚本自动复制语料到 data/ 并重建索引），然后：
  poetry run python ../../scripts/evaluate.py
"""
import io, json, os, shutil, sys, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RE = os.path.join(ROOT, "src", "ragapp")
os.chdir(RE)
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./create_llama/backend"))

from dotenv import load_dotenv
load_dotenv("config/.env")

# 1. 导入语料并重建索引
corpus_dir = os.path.join(ROOT, "document", "eval-corpus")
data_dir = "data"
os.makedirs(data_dir, exist_ok=True)
copied = 0
for fn in os.listdir(corpus_dir):
    if fn.endswith(".txt"):
        shutil.copy(os.path.join(corpus_dir, fn), os.path.join(data_dir, fn))
        copied += 1
print(f"[1] 语料导入 {copied} 篇（累计 {len(os.listdir(data_dir))} 个文件）")

from backend.tasks.indexing import index_all
t0 = time.time()
index_all()
print(f"[2] 索引重建完成，耗时 {time.time()-t0:.1f}s")

# 2. 构建两路检索器
from create_llama.backend.app.settings import init_settings
init_settings()
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.vector_stores.types import (
    FilterOperator, MetadataFilter, MetadataFilters,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

db = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH", "storage/chroma"))
coll = db.get_or_create_collection(os.getenv("CHROMA_COLLECTION", "default"))
print(f"[3] 向量库节点数: {coll.count()}")

sc = StorageContext.from_defaults(vector_store=ChromaVectorStore(chroma_collection=coll))
index = VectorStoreIndex.from_vector_store(sc.vector_store)

filters = MetadataFilters(
    filters=[MetadataFilter(key="private", value="true", operator=FilterOperator.NE)]
)
vector_retriever = index.as_retriever(similarity_top_k=5, filters=filters)

from backend.engine.hybrid import HybridRetriever, nodes_from_vector_store
hybrid_retriever = HybridRetriever(
    vector_retriever, nodes_from_vector_store(index.vector_store), top_k=5, filters=filters
)

# 3. 评测
eval_set = json.load(open(os.path.join(ROOT, "document", "eval", "eval-set.json"), encoding="utf-8"))["questions"]

def hits_at(retriever, q, expects, k):
    """hit@k：前 k 个结果中任一包含期望关键词"""
    nodes = retriever.retrieve(q)[:5]
    for n in nodes[:k]:
        text = n.node.get_content()
        if any(e in text for e in expects):
            return True
    return False

stats = {"exact": [0, 0, 0, 0], "colloquial": [0, 0, 0, 0], "cross": [0, 0, 0, 0]}  # [n, v@1, h@1, v&h@3计]
details = []
for item in eval_set:
    q, style = item["q"], item["style"]
    nodes_v = vector_retriever.retrieve(q)[:5]
    nodes_h = hybrid_retriever.retrieve(q)[:5]
    def hit(nodes, k):
        return any(any(e in n.node.get_content() for e in item["expect"]) for n in nodes[:k])
    v1, h1 = hit(nodes_v, 1), hit(nodes_h, 1)
    v3, h3 = hit(nodes_v, 3), hit(nodes_h, 3)
    v5, h5 = hit(nodes_v, 5), hit(nodes_h, 5)
    s = stats[style]
    s[0] += 1
    s[1] += v1
    s[2] += h1
    details.append((style, q, v1, h1, v3, h3, v5, h5))
    flag = "✅" if (v1 and h1) else ("🔵" if h1 else ("🟠" if v1 else "⬜"))
    print(f"[{flag}] {style:<10} {q}  top1: {'向量' if v1 and not h1 else ('混合' if h1 and not v1 else ('双中' if v1 and h1 else '双失'))}")

n_total = len(eval_set)
print("\n========== 结果（recall@k）==========")
print(f"{'风格':<10}{'指标':<10}{'单路向量':>10}{'混合检索':>10}")
v1a = sum(s[1] for s in stats.values()); h1a = sum(s[2] for s in stats.values())
v3a = sum(d[4] for d in details); h3a = sum(d[5] for d in details)
v5a = sum(d[6] for d in details); h5a = sum(d[7] for d in details)
for name, key in [("精确词", "exact"), ("白话", "colloquial"), ("交叉", "cross")]:
    s = stats[key]
    print(f"{name:<10}{'hit@1':<10}{s[1]:>7}/{s[0]}{s[2]:>8}/{s[0]}")
print(f"{'总计':<10}{'hit@1':<10}{v1a:>7}/{n_total}{h1a:>8}/{n_total}")
print(f"{'总计':<10}{'hit@3':<10}{v3a:>7}/{n_total}{h3a:>8}/{n_total}")
print(f"{'总计':<10}{'hit@5':<10}{v5a:>7}/{n_total}{h5a:>8}/{n_total}")
print(f"\nhit@1：单路向量 {v1a/n_total*100:.0f}%  →  混合检索 {h1a/n_total*100:.0f}%")
print(f"hit@3：单路向量 {v3a/n_total*100:.0f}%  →  混合检索 {h3a/n_total*100:.0f}%")

# 4. 写结果文件
lines = ["# 评测明细", "", "| 风格 | 问题 | 单路 | 混合 |", "|---|---|---|---|"]
for style, q, v, h, _ in details:
    lines.append(f"| {style} | {q} | {v} | {h} |")
io.open(os.path.join(ROOT, "document", "eval", "details.md"), "w", encoding="utf-8").write("\n".join(lines))
print("明细已写 document/eval/details.md")
