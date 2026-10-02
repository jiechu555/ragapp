# 降级与缓存实测报告（commit 4）

> 2026-10-02 实测，全部脚本可复跑（scripts/test_degraded.py / check_cache.py / baseline_e2e.py）。

## LLM 降级（坏 key 注入法实测）

| 场景 | HTTP | 响应 | 判定 |
|---|---|---|---|
| 正常 key | 200 | sources 事件 + 正常 RAG 回答 | ✅ |
| **坏 key** | **200** | **degraded 事件 + 降级话术**（原为 500） | ✅ |
| 恢复 key | 200 | 正常 RAG 回答 | ✅ 无状态残留 |

降级实现两要点：①`astream_chat` 改**急切 await**——condense（首次 LLM 调用）失败才能被路由层捕获进降级，否则在流式生成器内部炸成空响应；②降级响应与 Vercel 流式协议同格式（0:文本/8:事件 + degraded 事件），前端零改动可感知。

## embedding 缓存（LLRU 2048，模块级单例）

| 指标 | 实测 |
|---|---|
| 第 1 轮 3 问（冷缓存） | embedding API 调用 3 次 |
| 第 2 轮同 3 问 | **0 次**（全部 LRU 命中） |
| 命中率 | 重复问题场景 100% |

stats() 暴露 hits/misses/size（`CachedOpenAILikeEmbedding.stats()`），可接监控。

## 过程中修的四个坑（Python/llama_index 特有，面试可讲）

1. **lambda 内零参 `super()`**：`super(): no arguments` —— 类作用域魔法只在类体直接作用域生效，闭包里必须两参形式 `super(Cls, self)`
2. **pydantic v2 PrivateAttr 陷阱**：`default_factory=OrderedDict` 实际产生裸 dict（copy/model_dump 交互），`move_to_end` 崩溃——改模块级单例（服务进程缓存语义本就该单例）
3. **构造参数名**：OpenAILikeEmbedding 收 `model_name` 不是 `model`（传 model 显式 raise）
4. **急切 vs 惰性求值**：FastAPI 流式路由中，await 时机决定异常能否被路由层捕获——降级设计的前提是"让错误抛在能接住它的地方"
