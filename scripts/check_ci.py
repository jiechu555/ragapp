# -*- coding: utf-8 -*-
"""查 CI 状态"""
import io, json, sys, subprocess
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
out = subprocess.run(
    ["git", "credential", "fill"], input="protocol=https\nhost=github.com\n",
    capture_output=True, text=True, cwd=r"C:\Users\12808\Documents\code\mall"
).stdout
token = [l for l in out.splitlines() if l.startswith("password=")][0].split("=", 1)[1]

import urllib.request
req = urllib.request.Request(
    "https://api.github.com/repos/jiechu555/ragapp/actions/runs?per_page=3",
    headers={"Authorization": "token " + token},
)
for r in json.load(urllib.request.urlopen(req, timeout=20)).get("workflow_runs", []):
    print(r["name"][:24], "|", r["status"], "|", str(r.get("conclusion")), "|", r["head_sha"][:7], "|", r["created_at"][11:19])
