# Fork 二开增量（jiechu555/ragapp）

> 基于 ragapp 0.1.5（Apache-2.0）的二开：把我在 Java 电商项目里验证过的 RAG 方法论（混合检索/RRF/评测闭环/降级）移植到 Python 生态，**同一套方法论、两种语言双实现**。上游文档见下方原文。

## 六个二开 commit 与实测数字

| # | 主题 | 关键产出与实测 |
|---|---|---|
| 1 | 智谱端点接入 | 自定义 OpenAI 兼容端点补丁（原生 OpenAI 模型名枚举锁死是接入国产模型第一道坎）；E2E 3 问全对，2.1-3.8s |
| 2 | 混合检索 + RRF | 自研 BM25（CJK 二元分词，零依赖）+ RRF(k=60) 融合（`backend/engine/hybrid.py`）；`USE_HYBRID` 开关留 A/B；单测 5 用例 |
| 3 | 评测体系 | 22 篇语料（含 10 篇友商干扰项）+ 28 问三风格评测集；**评测抓出 BM25 路静默失效**（首轮双路逐题一致=失效信号）；hit@1 双路 86% 持平的诚实结论：RRF 定位是稳健性兜底而非召回提升（详见 `document/eval/README.md`） |
| 4 | LLM 降级 + embedding 缓存 | 坏 key 实测 HTTP 200 + degraded 事件 + 检索摘要（原为 500）；LRU 缓存第二轮同问题 API 调用 **3→0 次** |
| 5 | 自实现 Embedding + CI | `OpenAICompatEmbedding`（60 行 BaseEmbedding 子类）替换版本冲突的 openai-like 包；GitHub Actions 24 用例全绿 |
| 6 | 收官 | 本 README、复现指南、查询改写展望 |

## 快速复现（智谱端点）

```bash
cd src/ragapp
make patch-chat                    # 生成 create_llama 脚手架并应用二开补丁
poetry install --no-root
cp config/.env.example config/.env # 填入智谱 OPENAI_API_KEY
PYTHONPATH=./create_llama/backend poetry run python main.py
# 另一终端：poetry run python ../../scripts/baseline_e2e.py
```

评测：`poetry run python ../../scripts/evaluate.py`（自动导语料→重建索引→双路 A/B→明细落盘）

## 工程结论（面试视角）

- **国产模型接入**：llama_index 的 OpenAI 枚举校验（LLM 与 Embedding 两层）+ openai-like 包的版本冲突，说明"OpenAI 兼容"生态仍有暗礁——自实现抽象层是终解
- **评测先行**：混合检索首测与单路逐题一致，暴露 BM25 语料重建静默失效（chroma 正文在 documents 字段而非 _node_content）——评测的价值不在数字，在暴露"你以为生效其实没生效的东西"
- **降级设计**：FastAPI 流式路由中 await 时机决定异常能否被路由层捕获——降级的前提是让错误抛在能接住它的地方
- **已知边界**：3 类双失问句（"东西坏了"≠"质量问题"）属语义鸿沟，解法是查询改写/HyDE/Agent 多步推理，不是检索层能解决的——见下一步

---

<p align="center"><img alt="Logo - RAGapp" src="docs/logo.png"></p>

<p align="center"><strong>The easiest way to use Agentic RAG in any enterprise.</strong></p>

<p align="center">As simple to configure as <a href="https://openai.com/index/introducing-gpts" target="_blank">OpenAI's custom GPTs</a>, but deployable in your own cloud infrastructure using Docker. Built using <a href="https://github.com/run-llama/llama_index">LlamaIndex</a>.</p>

<p align="center">
  <a href="#get-started"><strong>Get Started</strong></a> ·
  <a href="#endpoints"><strong>Endpoints</strong></a> ·
  <a href="#deployment"><strong>Deployment</strong></a> ·
  <a href="#contact"><strong>Contact</strong></a> 
</p>

<br/>
<img alt="Screenshot" src="docs/screenshot.png">

## Get Started

To run, start a docker container with our image:

```shell
docker run -p 8000:8000 ragapp/ragapp
```

Then, access the Admin UI at http://localhost:8000/admin to configure your RAGapp.

You can use hosted AI models from OpenAI or Gemini, and local models using [Ollama](https://ollama.com/).

> _Note_: To avoid [running into any errors](https://github.com/ragapp/ragapp/issues/22), we recommend using the latest version of Docker and (if needed) Docker Compose.

## Endpoints

The docker container exposes the following endpoints:

- Admin UI: http://localhost:8000/admin
- Chat UI: http://localhost:8000
- API: http://localhost:8000/docs

> _Note_: The Chat UI and API are only functional if the RAGapp is configured.

## Security

### Authentication

Just the RAGapp container doesn't come with any authentication layer by design. This is the task
of an API Gateway routing the traffic to RAGapp.
This step heavily depends on your cloud provider and the services you use.
For a pure Docker Compose environment, you can look at our [RAGapp with management UI](./deployments/multiple-ragapps) deployment.

### Authorization

Later versions of RAGapp will support restricting access based on access tokens forwarded from an API Gateway or similar.

## Deployment

### Using Docker Compose

You can easily deploy RAGapp to your own infrastructure with one of these Docker Compose deployments:

1. [RAGapp with Ollama and Qdrant](./deployments/single)
2. [Multiple RAGapps with a management UI](./deployments/multiple-ragapps)

### Kubernetes

It's easy to deploy RAGapp in your own cloud infrastructure. Customized K8S deployment descriptors are coming soon.

## Development

### RAGApp:

> _Important_: Parts of this project's source code is dynamically retrieved from the [create-llama](https://github.com/run-llama/create-llama) project. Before committing changes, make sure to update the source code by calling `make build-frontends`.

Move to [src/ragapp](src/ragapp) directory and start with these commands:

```shell
export ENVIRONMENT=dev
poetry install --no-root
make build-frontends
make dev
```

Then, to check out the admin UI, go to http://localhost:3000/admin.

> _Note_: Make sure you have [Poetry](https://python-poetry.org/) installed.

## Contact

Questions, feature requests or found a bug? [Open an issue](https://github.com/ragapp/ragapp/issues/new/choose) or reach out to [marcusschiesser](https://github.com/marcusschiesser).

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=ragapp/ragapp&type=Date)](https://star-history.com/#ragapp/ragapp&Date)
