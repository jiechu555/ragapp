# -*- coding: utf-8 -*-
"""降级路径测试：坏 key → 检索摘要降级（HTTP 200 + degraded 事件）"""
import io, json, sys, urllib.request, urllib.error
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
payload = json.dumps({"messages": [{"role": "user", "content": "X1 保修几年"}]}).encode()
req = urllib.request.Request("http://127.0.0.1:8000/api/chat", data=payload,
                             headers={"Content-Type": "application/json"})
try:
    resp = urllib.request.urlopen(req, timeout=120)
    raw = resp.read().decode("utf-8", errors="replace")
    print("HTTP", resp.status)
    has_degraded = "degraded" in raw
    has_sources = "sources" in raw
    print("degraded事件:", has_degraded, "| sources事件:", has_sources)
    import re
    texts = re.findall(r'0:"((?:[^"\\]|\\.)*)"', raw)
    print("回答:", "".join(texts)[:200].replace("\\n", " "))
except urllib.error.HTTPError as e:
    print("HTTP", e.code, "(500=降级未生效)", e.read().decode()[:200])
