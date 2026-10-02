# -*- coding: utf-8 -*-
"""隔离测试 OpenAILike + 智谱：complete / stream / function-call"""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from dotenv import load_dotenv
load_dotenv("config/.env")
from llama_index.llms.openai_like import OpenAILike

llm = OpenAILike(
    model=os.environ["MODEL"],
    api_base=os.environ["OPENAI_API_BASE"],
    api_key=os.environ["OPENAI_API_KEY"],
    is_chat_model=True,
    is_function_calling_model=True,
)

print("[1] complete:")
try:
    r = llm.complete("只回复两个字：好的")
    print("   →", str(r)[:80])
except Exception as e:
    print("   ✗", type(e).__name__, str(e)[:200])

print("[2] stream_complete:")
try:
    chunks = []
    for t in llm.stream_complete("从1数到3"):
        chunks.append(t.delta)
    print("   →", "".join(chunks)[:80])
except Exception as e:
    print("   ✗", type(e).__name__, str(e)[:200])

print("[3] chat + stream_chat:")
try:
    r = llm.chat([{"role": "user", "content": "只回复：OK"}])
    print("   →", str(r)[:80])
except Exception as e:
    print("   ✗", type(e).__name__, str(e)[:200])
