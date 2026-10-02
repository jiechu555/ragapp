# -*- coding: utf-8 -*-
"""用服务端同款 where 过滤器查 chroma"""
import os
from dotenv import load_dotenv
load_dotenv("config/.env")
import chromadb

db = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH", "storage/chroma"))
coll = db.get_or_create_collection("default")
print("总节点:", coll.count())

q = coll.get(limit=3, where={"private": {"$ne": "true"}}, include=["metadatas"])
print("private!=true 命中:", len(q["ids"]))
for m in q["metadatas"][:3]:
    print("  -", m.get("file_name"), "| private:", m.get("private"))
