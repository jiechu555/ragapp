# -*- coding: utf-8 -*-
"""ragapp 二开 commit 1 基线测试：上传→索引→问答 E2E"""
import io, json, sys, time
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "http://127.0.0.1:8000"

DOC = """# 星辰咖啡机产品手册（测试文档）

## X1 型号
- 容量：1.2 升水箱，可煮 8 杯
- 功率：1450 瓦，预热时间 40 秒
- 保修：整机保修 2 年，水泵保修 5 年
- 特色：双锅炉系统，可同时萃取蒸汽打奶泡

## X2 型号
- 容量：1.8 升水箱，可煮 12 杯
- 功率：1600 瓦，预热时间 30 秒
- 保修：整机保修 3 年
- 特色：自动清洗程序，支持 App 远程预约

## 退换政策
- 签收后 7 天内无理由退货，需包装完好
- 质量问题 15 天内可换新机
"""

# 1. 上传文档（知识库走 management 路由：multipart file + fileIndex/totalFiles）
import uuid
boundary = "----ragapptest"
fn = "coffee_manual_%s.txt" % uuid.uuid4().hex[:8]
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="{fn}"\r\n'
    f"Content-Type: text/plain\r\n\r\n{DOC}\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="fileIndex"\r\n\r\n0\r\n'
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="totalFiles"\r\n\r\n1\r\n'
    f"--{boundary}--\r\n"
).encode("utf-8")
req = urllib.request.Request(
    BASE + "/api/management/files",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
t0 = time.time()
resp = urllib.request.urlopen(req, timeout=180)
print("[1] 上传索引:", resp.status, "耗时 %.1fs" % (time.time() - t0), "|", resp.read().decode()[:120])

# 2. 问答（验证检索+生成）
questions = ["X1 咖啡机保修几年？", "X2 和 X1 哪个预热更快？", "买的咖啡机不满意能退吗？"]
for q in questions:
    payload = json.dumps({"messages": [{"role": "user", "content": q}]}).encode()
    req = urllib.request.Request(BASE + "/api/chat", data=payload, headers={"Content-Type": "application/json"})
    t0 = time.time()
    resp = urllib.request.urlopen(req, timeout=120)
    raw = resp.read().decode("utf-8", errors="replace")
    dt = time.time() - t0
    # 流式响应里抽取文本（vercel AI 数据协议：0:"text" 行）
    import re
    texts = re.findall(r'0:"((?:[^"\\]|\\.)*)"', raw)
    answer = "".join(texts).encode().decode("unicode_escape") if texts else raw[:200]
    print("[2] Q:", q)
    print("    A(%.1fs):" % dt, answer[:180].replace("\n", " "))
