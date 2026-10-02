# ragapp 二开基线报告（commit 1）

> 2026-10-02 实测。底座 ragapp 0.1.5（4446★，Apache-2.0，FastAPI + llama_index 0.11.17 + Chroma 0.5.1）。
> 环境：Windows + Python 3.11.9（poetry venv）+ 智谱 OpenAI 兼容端点（glm-4.5-air + embedding-2 1024 维，CHROMA_PATH 本地持久化）。

## 端到端基线（星辰咖啡机测试文档，3 问）

| 问题 | 回答质量 | 延迟 |
|---|---|---|
| X1 咖啡机保修几年？ | ✅ "整机保修2年，水泵保修5年"（精确） | 3.8s |
| X2 和 X1 哪个预热更快？ | ✅ 跨段对比："X2 快 10 秒（30s vs 40s）" | 2.1s |
| 买的咖啡机不满意能退吗？ | ✅ "7 天无理由、质量问题 15 天换新" | 2.9s |

延迟与 mall RAG（1.8~3.5s）同量级，瓶颈同为 LLM API 网络。

## 跑通过程中修复的三个原生问题（= 二开增量起点）

1. **Embedding 枚举锁死**：`OpenAIEmbedding` 只认 OpenAI 官方模型名（embedding-2 报 `not a valid OpenAIEmbeddingModelType`）→ 补丁 `init_openai`：当设置 `OPENAI_API_BASE` 时走 `OpenAILikeEmbedding`（任意模型名 + 自定义端点 + dimensions）
2. **LLM 枚举锁死**：同构问题，`glm-4.5-air` 不在 OpenAI 模型表 → 走 `OpenAILike`（`is_chat_model=True` 走 /chat/completions，`is_function_calling_model=True` 过 Agent 断言）
3. **依赖回归风险**：`poetry add` 会把 llama-index-core 拉到 0.14.x 破坏 AgentRunner 导入（qdrant 声明 <0.12）——还原 lock 后用 `pip install --no-deps` 装 `llama-index-embeddings-openai-like==0.3.1`，版本组合锁定为 core 0.11.19 + openai-like 0.3.1

补丁文件落在 `patch/backend/app/settings.py`（ragapp 的脚手架再生机制会重放 patch/，改动不丢失）。

## 踩坑记录（全为 upstream 语义，面试可讲）

- **知识库上传走 `/api/management/files`**（multipart，`fileIndex`/`totalFiles` 从 1 计数，`fileIndex == totalFiles` 时同步触发索引）——`/api/chat/upload` 是"会话内私有文件"，索引带 `private=true`，chat 检索过滤器 `private != true` 会把它排除：**两个上传口语义不同，投错口=检索永远为空**
- **索引缓存**：engine 模块级缓存 index，重建索引后必须重启服务才可见（基线阶段"索引成功但检索为空"耗了一轮排查，根因在此）
- 知识库只收 `.txt/.pdf/.csv`（`.md` 不支持）；上传的 base64 必须带 data-uri 头
- `src/ragapp/.gitignore` 的 `!config/*` 反向规则会覆盖根 `**/.env`——config/.env（含 key）需显式再忽略；已加 `config/.env.example` 模板并 untrack 真实 .env

## 二开 backlog（后续 commit）

1. 混合检索 + RRF（engine 现为单路向量 + reranker 后处理）
2. 评测集 + recall@k（mall 方法论 Python 复刻）
3. LLM 降级（当前 LLM 异常直接 500，无降级）+ embedding 缓存
4. pytest + CI

## 复现

```bash
cd src/ragapp
npx create-llama@0.3.7 ...   # 见 Makefile（已生成 create_llama/）
cp -r patch/* create_llama/  # 应用二开补丁
poetry install --no-root
pip install --no-deps llama-index-embeddings-openai-like==0.3.1
cp config/.env.example config/.env  # 填入智谱 key
poetry run python main.py           # PYTHONPATH=./create_llama/backend
python ../../scripts/baseline_e2e.py
```
