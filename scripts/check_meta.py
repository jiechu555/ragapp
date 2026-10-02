# -*- coding: utf-8 -*-
"""打印 chroma 节点元数据"""
import os
from dotenv import load_dotenv
load_dotenv("config/.env")
import chromadb
db = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH", "storage/chroma"))
coll = db.get_or_create_collection("default")
d = coll.get(limit=2, include=["metadatas"])
print("元数据:", d["metadatas"])
