# -*- coding: utf-8 -*-
"""验证第三轮缓存路径回答内容（解码后检查）"""
import io, json, sys, re, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
payload = json.dumps({"messages": [{"role": "user", "content": "X1 咖啡机保修几年？"}]}).encode()
req = urllib.request.Request("http://127.0.0.1:8000/api/chat", data=payload,
                             headers={"Content-Type": "application/json"})
raw = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", errors="replace")
texts = "".join(re.findall(r'0:"((?:[^"\\]|\\.)*)"', raw))
# \uXXXX 解码
try:
    decoded = texts.encode("utf-8").decode("unicode_escape").encode("latin-1").decode("utf-8")
except Exception:
    decoded = texts
print("解码后回答:", decoded[:150])
print("包含 2年:", "2年" in decoded, "| 包含 5年:", "5年" in decoded)
