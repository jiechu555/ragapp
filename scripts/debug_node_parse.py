# -*- coding: utf-8 -*-
"""调试 TextNode 反序列化失败原因"""
import os, json
from dotenv import load_dotenv
load_dotenv("config/.env")
import chromadb

db = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH", "storage/chroma"))
coll = db.get_or_create_collection("default")
data = coll.get(include=["metadatas"], limit=1)
raw = data["metadatas"][0]["_node_content"]
payload = json.loads(raw)
print("字段列表:", sorted(payload.keys()))

from llama_index.core.schema import TextNode
try:
    n = TextNode.model_validate(payload)
    print("model_validate OK:", n.id_[:8], "| text:", n.get_content()[:40])
except Exception as e:
    print("model_validate 失败:", type(e).__name__, str(e)[:300])
    # 降级路径：手工构造
    n = TextNode(id_=payload["id_"], text=payload.get("text", ""), metadata=payload.get("metadata", {}))
    print("手工构造 OK:", n.id_[:8])
