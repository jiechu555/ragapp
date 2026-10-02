# -*- coding: utf-8 -*-
"""隔离测试 astream_chat（async generator 直接迭代）"""
import asyncio, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from dotenv import load_dotenv
load_dotenv("config/.env")
from llama_index.llms.openai_like import OpenAILike
from llama_index.core.base.llms.types import ChatMessage

llm = OpenAILike(
    model=os.environ["MODEL"],
    api_base=os.environ["OPENAI_API_BASE"],
    api_key=os.environ["OPENAI_API_KEY"],
    is_chat_model=True,
    is_function_calling_model=True,
)

async def main():
    r = await llm.astream_chat([ChatMessage(role="user", content="从1数到3")])
    n = 0
    try:
        async for d in r:
            n += 1
            delta = getattr(d, "delta", d)
            print(delta, end="", flush=True)
    except Exception as e:
        print("\n✗ 流中断:", type(e).__name__, str(e)[:150])
    print("\n→ delta 数:", n)

asyncio.run(main())
