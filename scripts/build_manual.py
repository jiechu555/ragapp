# -*- coding: utf-8 -*-
"""生成 ragapp 复现手册 PDF（docx -> LibreOffice PDF）"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

doc = Document()

# 页边距
for sec in doc.sections:
    sec.left_margin = Inches(0.7)
    sec.right_margin = Inches(0.7)

# 基础字体
style = doc.styles["Normal"]
style.font.name = "Microsoft YaHei"
style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
style.font.size = Pt(10.5)


def heading(text, size=15, color="1A2636", space_before=14):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    r.font.name = "Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    return p


def body(text, size=10.5, color="2C3E50", keep=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
    if keep:
        p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    r.font.name = "Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    return p


def set_cell_bg(cell, hexcolor):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hexcolor)
    cell._tc.get_or_add_tcPr().append(shd)


def term_block(lines, title=None):
    """终端样式块：深底等宽字。lines 为 (text, color) 或 str"""
    table = doc.add_table(rows=1, cols=1)
    table.autofit = True
    tr = table.rows[0]._tr
    trPr = tr.get_or_add_trPr()
    cantSplit = OxmlElement("w:cantSplit")
    trPr.append(cantSplit)
    cell = table.rows[0].cells[0]
    set_cell_bg(cell, "1E1E1E")
    first = True
    if title:
        p = cell.paragraphs[0]
        r = p.add_run(title)
        r.font.name = "Consolas"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor.from_string("6A9955")
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        first = False
    for line in lines:
        text, color = (line, "D4D4D4") if isinstance(line, str) else line
        if first:
            p = cell.paragraphs[0]
            first = False
        else:
            p = cell.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(text)
        r.font.name = "Consolas"
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor.from_string(color)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table


GREEN = "6A9955"


def tip_block(title, text):
    """知识点卡片：浅蓝底，穿插在步骤之间帮助理解"""
    table = doc.add_table(rows=1, cols=1)
    table.autofit = True
    tr = table.rows[0]._tr
    trPr = tr.get_or_add_trPr()
    cantSplit = OxmlElement("w:cantSplit")
    trPr.append(cantSplit)
    cell = table.rows[0].cells[0]
    set_cell_bg(cell, "EEF4FB")
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run("💡 知识点 · " + title)
    r.bold = True
    r.font.size = Pt(9.5)
    r.font.color.rgb = RGBColor.from_string("0B57D0")
    r.font.name = "Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    r2 = p2.add_run(text)
    r2.font.size = Pt(9.5)
    r2.font.color.rgb = RGBColor.from_string("2C3E50")
    r2.font.name = "Microsoft YaHei"
    r2._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return table
YELLOW = "DCDCAA"
BLUE = "569CD6"
GRAY = "9AA4B2"
RED = "F48771"

# ============ 封面区 ============
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("ragapp 本地复现手册")
r.bold = True
r.font.size = Pt(24)
r.font.color.rgb = RGBColor.from_string("1A2636")
r.font.name = "Microsoft YaHei"
r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("第 0 课配套 · 从零跑通你自己的 RAG 问答系统 · 2026-10-03")
r.font.size = Pt(11)
r.font.color.rgb = RGBColor.from_string("5F6B7A")
r.font.name = "Microsoft YaHei"
r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

body("")
body("适用环境：Windows + Git Bash + Python 3.11（poetry 虚环境已就绪）。全部命令与输出为 2026-10-03 实机复现记录，逐条可复制。")
body("跟随本手册走完 = 你独立跑通了简历主推项目。出错时先查文末《常见故障速查表》。", color="0B57D0")

# ============ 学习地图 ============
heading("学习地图 · 这本手册教你什么", size=13, space_before=10)
body("跑通只是结果，真正值钱的是路上这 8 个概念——每个都对应手册里的一个步骤和课程体系的一课：", size=9.5)
tbl = doc.add_table(rows=9, cols=2)
tbl.style = "Table Grid"
rows = [
    ("概念", "在哪学（步骤 → 第几课）"),
    ("虚拟环境与依赖锁", "步骤 2 → 第 1 课"),
    ("模块导入机制（PYTHONPATH）", "步骤 3 → 第 2 课"),
    ("HTTP 服务与状态码", "步骤 4 → 第 1 课"),
    ("REST 接口与 curl 调试", "步骤 5 → 第 2 课"),
    ("流式响应（为什么聊天要打字机效果）", "步骤 6 → 第 2 课"),
    ("检索三范式：关键词/语义/混合", "原理图解 → 第 3 课"),
    ("评测思维：怎么量化『好用』", "历史实测 → 第 5 课"),
    ("降级设计：外部依赖会挂怎么办", "原理图解 → 第 4 课"),
]
for i, (a, b) in enumerate(rows):
    c0, c1 = tbl.rows[i].cells
    c0.text, c1.text = a, b
    for c in (c0, c1):
        for pp in c.paragraphs:
            pp.paragraph_format.keep_with_next = (i == 0)
            for rr in pp.runs:
                rr.font.size = Pt(8.5)
                rr.font.name = "Microsoft YaHei"
                rr._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    if i == 0:
        set_cell_bg(c0, "1A2636"); set_cell_bg(c1, "1A2636")
        for pp in c0.paragraphs + c1.paragraphs:
            for rr in pp.runs:
                rr.font.color.rgb = RGBColor.from_string("FFFFFF")
doc.add_paragraph().paragraph_format.space_after = Pt(2)

# ============ 步骤 1 ============
heading("步骤 1 · 打开终端，进入项目目录")
body("打开 Git Bash（开始菜单搜 Git Bash），逐行输入：")
term_block([
    ("$ cd /c/Users/12808/Documents/code/ragapp/src/ragapp", YELLOW),
    ("$ pwd", YELLOW),
    ("/c/Users/12808/Documents/code/ragapp/src/ragapp", GREEN),
], title="终端")
body("要点：项目真正的工作目录是 src/ragapp（不是仓库根目录）——main.py、config/、backend/ 都在这里。")

# ============ 步骤 2 ============
heading("步骤 2 · 验证虚拟环境与依赖")
body("确认 poetry 虚环境和三个核心依赖完好（跑一次只要几秒）：")
term_block([
    ("$ PY=/c/Users/12808/AppData/Local/Programs/Python/Python311/python.exe", YELLOW),
    ("$ $PY -m poetry run python -c \"import fastapi, chromadb, llama_index.core; print('依赖OK')\"", YELLOW),
    ("依赖OK: fastapi 0.111.1 | chromadb 0.5.1 | llama-index-core 0.11.19", GREEN),
], title="终端")
body("若报 ModuleNotFoundError：见故障表 F2。")

tip_block("虚拟环境与依赖锁（步骤 2 的灵魂）",
    "每个 Python 项目一个独立环境，互不污染——A 项目要 libX 1.0、B 项目要 2.0，全局只能装一个，虚拟环境各装各的。poetry.lock 锁的不是『大概版本』而是精确到补丁号的整棵依赖树，任何人 poetry install 都得到一模一样的环境——这就是为什么本手册能保证你复现不出 bug。想一想：为什么 pip install 装了『更新的版本』反而可能坏？→ 因为新版本改了 API，锁文件就是防这个的。")

# ============ 步骤 3 ============
heading("步骤 3 · 启动服务器")
body("两个关键：① 必须在 src/ragapp 目录下；② 必须带 PYTHONPATH（原因见自测题 Q1）：")
term_block([
    ("$ PYTHONPATH=./create_llama/backend $PY -m poetry run python main.py", YELLOW),
    ("INFO:     Application startup complete.", GREEN),
    ("INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)", GREEN),
], title="终端")
body("看到 Uvicorn running 即启动成功（约 20-30 秒）。这个终端窗口要保持开着——服务器在前台运行，关窗口=关服务。", color="B45309")

tip_block("PYTHONPATH 与 import 机制（步骤 3 为什么那样启动）",
    "Python 找模块靠 sys.path 列表：当前目录 → PYTHONPATH 环境变量 → 安装目录，按序查找。main.py 里 import app.xxx，而 app 包在 create_llama/backend/ 下——不设 PYTHONPATH，解释器在默认路径里找不到就报 ModuleNotFoundError（正是故障 F3）。环境变量只对这一条命令生效，不污染系统。想一想：把 backend 目录的代码复制到当前目录行不行？→ 行但丑，路径引用全会乱。")

# ============ 步骤 4 ============
heading("步骤 4 · 验证服务存活（新开一个终端标签）")
body("保持步骤 3 的窗口不动，新开一个终端标签（Git Bash 窗口顶部 + 号），同样 cd 到项目目录，然后：")
term_block([
    ("$ curl -s -m 10 http://127.0.0.1:8000/api/chat/config", YELLOW),
    ('{"starterQuestions":null}', GREEN),
    ("$ curl -s -o /dev/null -w \"%{http_code}\\n\" http://127.0.0.1:8000/api/chat/config", YELLOW),
    ("200", GREEN),
], title="终端（第二个标签）")
body("HTTP 200 = 服务器活着。若连接被拒绝：见故障表 F1。")

tip_block("HTTP 状态码分层排错法（步骤 4 在验什么）",
    "200=服务活着且处理成功；404=服务活着但路径错；500=服务活着但代码炸了；连接拒绝=服务根本没起来。先 curl 一发把问题定位到层，再去看日志——这是后端排错第一反射。/config 端点返回运行配置，是『服务体检』的惯用入口。想一想：curl 返回 500 你第一件事干嘛？→ 看服务端日志最后几行，而不是改客户端。")

# ============ 步骤 5 ============
heading("步骤 5 · 端到端问答测试（E2E）")
body("跑项目自带的测试脚本——它会自动上传测试文档并向服务器提 3 个问题：")
term_block([
    ("$ $PY -m poetry run python ../../scripts/baseline_e2e.py", YELLOW),
    ("[1] 上传索引: 200 耗时 0.0s | {\"name\":\"coffee_manual_xxx.txt\",\"status\":\"uploaded\"}", GRAY),
    ("[2] Q: X1 咖啡机保修几年？", BLUE),
    ("    A(4.2s): 根据提供的文档，X1咖啡机的保修政策是：整机保修2年，水泵保修5年。", GREEN),
    ("[2] Q: X2 和 X1 哪个预热更快？", BLUE),
    ("    A(4.5s): …X2型号的预热时间是40秒 - X2型号的预热时间是30秒 所以X2比X1预热快10秒…", GREEN),
    ("[2] Q: 买的咖啡机不满意能退吗？", BLUE),
    ("    A(3.9s): …签收后7天内可以无理由退货…质量问题，可以在15天内换新机…", GREEN),
], title="终端（第二个标签）")
body("三个回答都正确出现 = 完整链路（文档上传→智谱向量化→混合检索→GLM 生成）全部健康。✅ 第 0 课验收通过。", color="0B57D0")

tip_block("curl 与 REST 语义（步骤 5 在干什么）",
    "curl 是命令行 HTTP 客户端：-X 指动词（GET 读/POST 写）、-H 加请求头、-d 带请求体。REST 约定：URL 是资源（/api/chat 是『对话』资源）、动词表意图、响应是 JSON{code, data} 结构。测试脚本本质是三个 HTTP 请求的自动重放+断言——你手写 curl 就是在手动做 E2E。想一想：为什么测试要问『整机保修』这种知识库里的问题？→ 答案必须来自检索命中，模型瞎编就露馅，这是检验 RAG 真伪的关键设计。")

# ============ 步骤 6 ============
heading("步骤 6 · 用浏览器跟你的系统对话")
body("服务器运行状态下，浏览器直接打开：http://localhost:8000/chat.html（教学版聊天页，50 行手写 UI）：")
try:
    doc.add_picture(r"C:\Users\12808\Documents\code\ragapp\scripts\manual-assets\chat.png", width=Inches(5.8))
    last = doc.paragraphs[-1]
    last.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run("▲ 实机截图：教学版聊天页，问题与回答均来自本地 ragapp + 智谱 GLM")
    r.font.size = Pt(9)
    r.font.color.rgb = RGBColor.from_string("5F6B7A")
    r.font.name = "Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
except Exception as e:
    body(f"[截图缺失: {e}]")
body("在输入框输入任意问题（例如：买的咖啡机不满意能退吗）→ 回车 → 等待 3-5 秒。这个页面就是你的系统在\"服务用户\"的样子。")

tip_block("流式响应（步骤 6 为什么像打字机）",
    "大模型生成是逐 token 的，等全生成完再返回，用户要盯着空白等 3 秒——首字延迟体验极差。流式把『生成一点发一点』变成 HTTP 分块传输。本项目用的是 Vercel AI SDK 协议：每行一个 JSON 片段，前缀 0: 是文本增量、8: 是事件（如降级标记）。浏览器端用 fetch 整包读再按行解析（本项目的 chat.html 就是 50 行手写实现，第 1 课会带你重写一遍）。想一想：SSE 和普通分块传输什么区别？→ SSE 是带 event/data 格式约定的分块，本质都是流。")

# ============ 步骤 7 ============
heading("步骤 7 · 停止服务器")
body("回到步骤 3 的终端窗口按 Ctrl+C；若无效（Windows 偶发），用端口定位强停：")
term_block([
    ("$ netstat -ano | grep \":8000.*LISTENING\"   # 找到最后一列的 PID", YELLOW),
    ("  TCP    0.0.0.0:8000    ...    LISTENING    20264", GRAY),
    ("$ taskkill //PID 20264 //F", YELLOW),
    ("成功: 已终止 PID 为 20264 的进程。", GREEN),
], title="终端")
body("注意 Git Bash 里是双斜杠 //PID（MSYS 路径转换，单斜杠会被吃掉）。")

tip_block("进程、端口与 PID（步骤 7 的排错逻辑）",
    "每个运行的程序是一个进程，有唯一 PID；端口是进程对外服务的门牌号，一个端口同一时刻只能一个进程监听。『端口被占用』= 上一个服务没退干净——netstat 找到占用的 PID，taskkill 定点清除。Ctrl+C 发的是中断信号，正常情况进程优雅退出，Windows 偶发卡死才需要 kill -F（强杀）。想一想：为什么强杀是最后手段？→ 进程没机会保存状态、关闭文件，可能留下脏数据。")

# ============ 原理图解 ============
heading("原理图解 · RAG 全链路（这个系统到底在干嘛）", size=14)
body("ragapp = 检索增强问答：先从你的知识库里找相关内容，再让大模型基于这些内容回答——模型只负责组织语言，事实来自知识库：")
term_block([
    ("【知识入库】(management 接口，一次性)", BLUE),
    ("  文档上传(txt/pdf/csv) → 切块 → 智谱 embedding-2 向量化 → ChromaDB 持久化", "D4D4D4"),
    ("", "D4D4D4"),
    ("【提问回答】(chat 接口，每次问答)", BLUE),
    ("  用户问题", "D4D4D4"),
    ("    ↓ HybridRetriever 双路召回", GRAY),
    ("    ├─ BM25 路：自研实现，CJK 二元分词（中文按两字切）→ 词频打分", "D4D4D4"),
    ("    └─ kNN 路：问题向量化 → ChromaDB 余弦相似检索", "D4D4D4"),
    ("    ↓ RRF 融合（k=60）：融合分 = Σ 1/(60+各路排名) → 取 top-k", "D4D4D4"),
    ("    ↓ 拼 Prompt（问题 + 检索到的原文）", "D4D4D4"),
    ("    ↓ 智谱 glm-4.5-air 生成", "D4D4D4"),
    ("    ↓ 流式返回：\"0:\"行=文本增量  \"8:\"行=降级事件", "D4D4D4"),
    ("  LLM 挂了？→ 降级：检索摘要话术 + degraded 标记，用户永远有响应", RED),
], title="数据流")
body("三个关键设计为什么（面试常问）：")
body("① 为什么混合检索？BM25 抓关键词精确匹配（型号、专有名词），向量抓语义（换个说法也能找到）。中文场景 BM25 必须自己做二元分词，英文分词器对中文是整句一个词。", size=9.5)
body("② RRF 是什么？两路打分量纲不同（BM25 是 TF-IDF 分、kNN 是余弦相似度），直接加权要调参。RRF 只看排名不看分数——每路第 r 名贡献 1/(60+r) 分，天然免疫量纲差异，k=60 是原论文通用值。", size=9.5)
body("③ 为什么有降级？LLM 是外部 API，会挂会超时。设计上检索在本地永远可用，LLM 失败时退化为检索摘要，服务不 503——这是可用性设计，不是补丁。", size=9.5)

# ============ 历史实测 ============
heading("历史实测数据（跑通后的下一步：量化它）", size=14)
tbl = doc.add_table(rows=4, cols=2)
tbl.style = "Table Grid"
rows = [
    ("实测项（出处可查）", "结果"),
    ("评测集 28 问三风格 hit@1（document/evaluation/）", "BM25 路与 kNN 路 86% 持平——诚实结论：混合检索在本语料非护城河，面试要敢讲"),
    ("同源方案在 mall 的 25 问评测（mall 仓库 ci）", "混合检索召回@5 从 BM25 基线 84% → 100%"),
    ("embedding LRU 缓存（commit 4）", "第二轮同 3 问：embedding API 调用 3 → 0（2048 容量模块级单例）"),
]
for i, (a, b) in enumerate(rows):
    c0, c1 = tbl.rows[i].cells
    c0.text, c1.text = a, b
    for c in (c0, c1):
        for pp in c.paragraphs:
            for rr in pp.runs:
                rr.font.size = Pt(9)
                rr.font.name = "Microsoft YaHei"
                rr._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    if i == 0:
        set_cell_bg(c0, "1A2636"); set_cell_bg(c1, "1A2636")
        for pp in c0.paragraphs + c1.paragraphs:
            for rr in pp.runs:
                rr.font.color.rgb = RGBColor.from_string("FFFFFF")
doc.add_paragraph().paragraph_format.space_after = Pt(2)

# ============ 面试五问 ============
heading("面试五问（面试官视角，答题要点）", size=14)
for q, a in [
    ("Q1 这个项目解决什么问题？", "私有知识的问答：文档不出内网（ChromaDB 本地）、答案有出处（引用检索原文）、模型可换（OpenAI 兼容层）——三个卖点各打一个场景。"),
    ("Q2 检索为什么不用 ES？", "教学复现优先轻依赖：自研 BM25 200 行 + ChromaDB 替掉五件套；代价是语量大后性能不如 ES——知道取舍比背结论加分。"),
    ("Q3 RRF 的 k=60 是什么？", "排名平滑常数：名次 r 的贡献 1/(k+r)。k 越大两路名次差异越被抹平；60 是原论文值，没调参，如实说。"),
    ("Q4 LLM 挂了用户看到什么？", "正常响应但内容是检索摘要 + degraded:true 事件标记——前端可据此事后提示。实测：坏 key 时 HTTP 仍是 200 流式。"),
    ("Q5 你怎么证明它好？", "28 问三风格评测集 hit@1 86%，且敢说 BM25 与向量持平的阴性结论；降级路径实测过；缓存效果有前后对比数字。"),
]:
    body(q, color="1A2636", size=10, keep=True)
    body("要点：" + a, size=9.5, color="5F6B7A")

# ============ 故障表 ============
heading("常见故障速查表（全部真实发生过）", size=14)
faults = [
    ("F1", "curl 报\"积极拒绝\"/连不上", "服务器没起来或已挂", "回步骤 3 窗口看最后几行报错；端口被占用先执行步骤 7 的强停"),
    ("F2", "ModuleNotFoundError", "依赖缺失/虚环境不对", "确认命令带 $PY -m poetry run 前缀；仍缺则见故障 F5 重装"),
    ("F3", "ModuleNotFoundError: No module named 'app'", "启动时漏了 PYTHONPATH", "步骤 3 的命令原样复制，PYTHONPATH 不能省"),
    ("F4", "打开 localhost:8000 根路径 500", "官方前端从未构建（static/ 不存在），不是坏了", "用 /chat.html 教学页即可；要官方 UI 需 make build-frontends（需 pnpm）"),
    ("F5", "依赖彻底乱掉", "误用 pip 装了高版本包", "cd src/ragapp && $PY -m poetry install --no-root --sync 还原锁文件"),
    ("F6", "回答全是\"智能客服暂时不可用\"", "LLM 降级被触发（key 失效/欠费/断网）", "检查 config/.env 里智谱 key；curl 官方端点验证；恢复后重启服务"),
]
t = doc.add_table(rows=1, cols=3)
t.style = "Table Grid"
hdr = t.rows[0].cells
for i, h in enumerate(["#", "症状", "原因与处置"]):
    set_cell_bg(hdr[i], "1A2636")
    r = hdr[i].paragraphs[0].add_run(h)
    r.bold = True
    r.font.size = Pt(10)
    r.font.color.rgb = RGBColor.from_string("FFFFFF")
    r.font.name = "Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
for fid, sym, cause, fix in faults:
    tr = t.add_row()._tr
    trPr0 = tr.get_or_add_trPr()
    cs = OxmlElement("w:cantSplit")
    trPr0.append(cs)
    row = t.rows[-1].cells
    row[0].text = fid
    row[1].text = sym
    row[2].text = f"{cause}。处置：{fix}"
    for c in row:
        for p in c.paragraphs:
            for r in p.runs:
                r.font.size = Pt(9.5)
                r.font.name = "Microsoft YaHei"
                r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

# ============ 自测题 ============
heading("第 0 课自测题（做完手册后回答，不看讲义）", size=13, space_before=10)
for q in [
    "Q1：PYTHONPATH=./create_llama/backend 是干什么的？去掉会发生什么？（提示：main.py 里 import 了谁）",
    "Q2：服务器跑在哪个端口？你从哪个文件知道的？",
    "Q3：步骤 5 的脚本向服务器发了几个 HTTP 请求？分别打到什么路径？",
]:
    body(q, color="1A2636", size=9.5)
body("答案写在第 0 课作业里交回——不要翻讲义，答错比抄对有用。", color="B45309", size=9.5)

out_docx = r"C:\Users\12808\Documents\复现手册\ragapp复现手册.docx"
doc.save(out_docx)
print("docx saved:", out_docx)
