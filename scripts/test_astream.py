# -*- coding: utf-8 -*-
"""隔离测试 OpenAILike.astream_chat（ragapp 用的路径）"""
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
    print("[astream_chat]")
    r = await llm.astream_chat([ChatMessage(role="user", content="从1数到3")])
    n = 0
    async for d in r.async_response_gen():
        n += 1
        print(d.delta, end="", flush=True)
    print("\n→ delta 数:", n)

asyncio.run(main())
