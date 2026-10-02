# -*- coding: utf-8 -*-
"""直接检查 Chroma 数据与检索链路"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from dotenv import load_dotenv
load_dotenv("config/.env")
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./create_llama/backend"))

import chromadb
db = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH", "storage/chroma"))
coll = db.get_or_create_collection(os.getenv("CHROMA_COLLECTION", "default"))
print("[1] Chroma collection:", coll.name, "| 节点数:", coll.count())

from create_llama.backend.app.settings import init_settings
init_settings()

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore

sc = StorageContext.from_defaults(vector_store=ChromaVectorStore(chroma_collection=coll))
idx = VectorStoreIndex.from_vector_store(sc.vector_store)
r = idx.as_retriever(similarity_top_k=3)
nodes = r.retrieve("X1 咖啡机保修几年")
print("[2] 检索命中:", len(nodes), "| scores:", [round(n.score or 0, 3) for n in nodes])
for n in nodes[:2]:
    print("    -", n.node.get_content()[:60].replace("\n", " "))
