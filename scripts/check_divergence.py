# -*- coding: utf-8 -*-
"""检查双路检索排序差异"""
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

db = chromadb.PersistentClient(path=os.getenv("CHROMA_PATH", "storage/chroma"))
coll = db.get_or_create_collection("default")
sc = StorageContext.from_defaults(vector_store=ChromaVectorStore(chroma_collection=coll))
index = VectorStoreIndex.from_vector_store(sc.vector_store)
filters = MetadataFilters(filters=[MetadataFilter(key="private", value="true", operator=FilterOperator.NE)])
vr = index.as_retriever(similarity_top_k=5, filters=filters)

from backend.engine.hybrid import HybridRetriever, nodes_from_vector_store
hr = HybridRetriever(vr, nodes_from_vector_store(index.vector_store), top_k=5, filters=filters)

diff = same = 0
qs = [
    "1450 瓦的咖啡机预热要多久",
    "家里养猫床上全是毛买哪款吸尘器",
    "滤芯可以水洗吗",
    "推荐好友买有什么优惠",
    "衬衫皱了想弄平整",
    "能打豆浆还能做米糊给三高老人买一台",
]
for q in qs:
    v = [n.node.node_id for n in vr.retrieve(q)]
    h = [n.node.node_id for n in hr.retrieve(q)]
    if v == h:
        same += 1
    else:
        diff += 1
    print("排序不同" if v != h else "排序相同", "|", q, "| top3:", [i[:6] for i in h[:3]])
print(f"\n排序差异: {diff}/{len(qs)}（不同=混合融合真实生效）")
