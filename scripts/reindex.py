# -*- coding: utf-8 -*-
"""手动触发知识库索引（data/ -> Chroma）"""
import io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from dotenv import load_dotenv
load_dotenv("config/.env")

import os
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./create_llama/backend"))

from backend.tasks.indexing import index_all

t0 = time.time()
index_all()
print("索引完成，耗时 %.1fs" % (time.time() - t0))
