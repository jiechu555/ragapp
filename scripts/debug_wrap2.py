# -*- coding: utf-8 -*-
"""直接构造 CachedOpenAILikeEmbedding 测试"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from dotenv import load_dotenv
load_dotenv("config/.env")
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./create_llama/backend"))

try:
    from backend.engine.embedding_cache import CachedOpenAILikeEmbedding, wrap_with_cache
    print("import OK")
    w = CachedOpenAILikeEmbedding(
        model=os.getenv("EMBEDDING_MODEL", "embedding-2"),
        api_base=os.getenv("OPENAI_API_BASE"),
        api_key=os.getenv("OPENAI_API_KEY"),
        dimensions=int(os.getenv("EMBEDDING_DIM", "1024")),
        is_chat_model=False,
    )
    print("构造 OK:", type(w).__name__)
    w.get_query_embedding("缓存测试XYZ")
    w.get_query_embedding("缓存测试XYZ")
    print("stats:", CachedOpenAILikeEmbedding.stats())
except Exception as e:
    print("失败:", type(e).__name__, "|", str(e)[:300])
