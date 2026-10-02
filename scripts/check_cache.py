# -*- coding: utf-8 -*-
"""检查 Settings.embed_model 是否为缓存实例"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from dotenv import load_dotenv
load_dotenv("config/.env")
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./create_llama/backend"))

from create_llama.backend.app.settings import init_settings
init_settings()
from llama_index.core.settings import Settings

em = Settings.embed_model
print("类型:", type(em).__name__)
print("model_name:", getattr(em, "model_name", "?"))
print("dimensions:", getattr(em, "dimensions", "?"))

# 实测缓存行为
em.get_query_embedding("缓存测试问题ABC")
s1 = type(em).stats() if hasattr(type(em), "stats") else None
em.get_query_embedding("缓存测试问题ABC")
s2 = type(em).stats() if hasattr(type(em), "stats") else None
print("第1次后 stats:", s1)
print("第2次后 stats:", s2, "→", "缓存生效" if s2 and s2["hits"] > 0 else "未走缓存")
