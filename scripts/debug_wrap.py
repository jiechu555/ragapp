# -*- coding: utf-8 -*-
"""显影 wrap 失败异常"""
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
from backend.engine.embedding_cache import CachedOpenAILikeEmbedding

try:
    w = CachedOpenAILikeEmbedding(
        model=em.model_name,
        api_base=getattr(em, "api_base", None),
        api_key=getattr(em, "api_key", None),
        dimensions=getattr(em, "dimensions", None),
        is_chat_model=False,
    )
    print("wrap OK:", type(w).__name__, "| dims:", w.dimensions)
except Exception as e:
    print("wrap 失败:", type(e).__name__, "|", str(e)[:400])
