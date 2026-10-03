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
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    r.font.name = "Microsoft YaHei"
    r._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    return p


def body(text, size=10.5, color="2C3E50"):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(4)
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

# ============ 步骤 3 ============
heading("步骤 3 · 启动服务器")
body("两个关键：① 必须在 src/ragapp 目录下；② 必须带 PYTHONPATH（原因见自测题 Q1）：")
term_block([
    ("$ PYTHONPATH=./create_llama/backend $PY -m poetry run python main.py", YELLOW),
    ("INFO:     Application startup complete.", GREEN),
    ("INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)", GREEN),
], title="终端")
body("看到 Uvicorn running 即启动成功（约 20-30 秒）。这个终端窗口要保持开着——服务器在前台运行，关窗口=关服务。", color="B45309")

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

# ============ 步骤 6 ============
heading("步骤 6 · 用浏览器跟你的系统对话")
body("服务器运行状态下，浏览器直接打开：http://localhost:8000/chat.html（教学版聊天页，50 行手写 UI）：")
try:
    doc.add_picture(r"C:\Users\12808\AppData\Local\Temp\ragapp_ui_chat.png", width=Inches(6.3))
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
    row = t.add_row().cells
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
heading("第 0 课自测题（做完手册后回答，不看讲义）", size=14)
for q in [
    "Q1：PYTHONPATH=./create_llama/backend 是干什么的？去掉会发生什么？（提示：main.py 里 import 了谁）",
    "Q2：服务器跑在哪个端口？你从哪个文件知道 的？",
    "Q3：步骤 5 的脚本向服务器发了几个 HTTP 请求？分别打到什么路径？",
]:
    body(q, color="1A2636")
body("答案写在第 0 课作业里交回——不要翻讲义，答错比抄对有用。", color="B45309")

out_docx = r"C:\Users\12808\Documents\ragapp复现手册.docx"
doc.save(out_docx)
print("docx saved:", out_docx)
