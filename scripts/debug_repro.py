# -*- coding: utf-8 -*-
"""最小复现：裸类 vs 子类构造"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from dotenv import load_dotenv
load_dotenv("config/.env")

from llama_index.embeddings.openai_like import OpenAILikeEmbedding
try:
    w = OpenAILikeEmbedding(model_name="embedding-2", api_base=os.getenv("OPENAI_API_BASE"),
                            api_key=os.getenv("OPENAI_API_KEY"), dimensions=1024)
    print("裸类构造 OK")
except Exception as e:
    print("裸类失败:", type(e).__name__, str(e)[:200])

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./create_llama/backend"))
from backend.engine.embedding_cache import CachedOpenAILikeEmbedding
try:
    w = CachedOpenAILikeEmbedding(model_name="embedding-2", api_base=os.getenv("OPENAI_API_BASE"),
                                  api_key=os.getenv("OPENAI_API_KEY"), dimensions=1024)
    print("子类构造 OK")
except Exception as e:
    print("子类失败:", type(e).__name__, str(e)[:300])
