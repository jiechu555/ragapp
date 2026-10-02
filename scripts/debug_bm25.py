# -*- coding: utf-8 -*-
"""显影 BM25 路的独立排序（验证混合不是退化）"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from dotenv import load_dotenv
load_dotenv("config/.env")
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./create_llama/backend"))

from create_llama.backend.app.settings import init_settings
init_settings()
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.vector_stores.types import FilterOperator, MetadataFilter, MetadataFilters
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb
from backend.engine.hybrid import nodes_from_vector_store, tokenize, bm25_scores

db = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH", "storage/chroma"))
coll = db.get_or_create_collection("default")
sc = StorageContext.from_defaults(vector_store=ChromaVectorStore(chroma_collection=coll))
index = VectorStoreIndex.from_vector_store(sc.vector_store)

nodes = nodes_from_vector_store(index.vector_store)
print("重建节点数:", len(nodes))
corpus = [tokenize(n.get_content()) for n in nodes]

filters = MetadataFilters(filters=[MetadataFilter(key="private", value="true", operator=FilterOperator.NE)])
vr = index.as_retriever(similarity_top_k=5, filters=filters)

for q in ["滤芯可以水洗吗", "衬衫皱了想弄平整"]:
    q_tokens = tokenize(q)
    scores = bm25_scores(q_tokens, corpus)
    ranked = sorted(zip(nodes, scores), key=lambda x: x[1], reverse=True)[:3]
    print("\nQ:", q, "| 查询词元:", q_tokens)
    for n, s in ranked:
        print("   BM25 %.3f | %s | %s" % (s, n.metadata.get("file_name", "?")[:28], n.get_content()[:36].replace("\n", " ")))
    v = vr.retrieve(q)[:3]
    print("   向量 top3:")
    for n in v:
        print("   %.3f | %s | %s" % (n.score or 0, n.node.metadata.get("file_name", "?")[:28], n.node.get_content()[:36].replace("\n", " ")))
