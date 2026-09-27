---
name: "pdf2latex-translate"
description: "Translates English academic PDF textbooks into Chinese LaTeX notes chapter by chapter (faithful full-paragraph translation, figures/tables extracted and rebuilt). Invoke when user asks to translate a PDF book to LaTeX, process a new chapter, or fix translation/layout issues in such a project."
---

# PDF 学术书 → 中文 LaTeX 笔记翻译管线

把英文学术 PDF 教材逐章翻译成中文 LaTeX 笔记：严格逐段全译（不总结不删减），
图形裁剪为 PNG 插入、表格重制为 booktabs、要点框转为 tcolorbox。

## 适用场景

- 用户要求把 PDF 书籍翻译成 LaTeX / Markdown 笔记
- 用户要求翻译某一章、校验编译、修复越界或翻译质量问题
- 本 skill 位于某个翻译项目内时，直接使用项目根目录已有的 scripts/ 和配置

## 项目结构（新项目初始化）

```
project/
├── <书名>.pdf
├── scripts/            # 从本 skill assets/ 复制
│   ├── 01_split_chapters.py
│   ├── 02_extract_figures.py
│   └── 03_check_chapter.py
├── prompt.md           # 翻译契约（从 assets/ 复制后按书微调）
├── glossary.md         # 术语表（随翻译不断补充）
├── preamble.tex        # ctexbook + tcolorbox(breakable) + threeparttable
├── main.tex
└── chapters/chNN/
    ├── text.md         # 切章产物（带 <!-- [p.NN] --> 页标记）
    ├── figures/        # PNG + manifest.md
    └── chNN.tex        # 翻译产出
```

初始化步骤：复制 assets/ 下脚本与模板 → 修改脚本顶部 PDF 路径与书名 →
preamble.tex 按需调整（中文文档用 ctexbook，编译用 xelatex）。

## 管线流程（每章四步）

1. **切章**：`python scripts/01_split_chapters.py [N]`
   按 PDF 书签切分 → `chapters/chNN/text.md`，段落间插入 `<!-- [p.NN] -->` 页标记。
   - 先跑 `[N]` 不带参数列出书签结构确认章节边界。
2. **图表提取**：`python scripts/02_extract_figures.py chNN`
   - 表格 = 宽横线分组（RULE_GAP 控制同表横线间距，排除页眉页脚）
   - 统计图 = `cluster_drawings()` 且路径数 ≥ 6
   - 要点框（Key Insight 等）= 矩形框 + 框内文字 ≥ 12 词 → `[CALLOUT]`
   - 产出 `figures/*.png` + `manifest.md`，text.md 中插入
     `[TABLE/FIGURE/CALLOUT name | caption]` 占位符
   - 题注正则必须要求编号后紧跟 `.` 或 `:`，否则正文引用
     （如 "Table 1.1 summarizes..."）会误配成图表
   - 人工核对 manifest：unpaired 项需检查是否漏提
3. **AI 翻译**：text.md → `chNN.tex`，严格逐条遵守 `prompt.md`（翻译契约）
   与 `glossary.md`（术语表）。契约核心见下方"翻译契约要点"。
4. **校验**：`python scripts/03_check_chapter.py chNN`
   检查占位符残留 / Unicode 数学字符 / 环境配对 / 括号配对 / 页标记覆盖（防截断）/
   行内页标记，并用 xelatex 编译，检测 `Overfull \hbox` 越界（>5pt 判 FAIL）。
   单章通过后再进入下一章。
5. **拼装**：`python scripts/04_assemble.py`
   生成 main.tex（preamble + 多图形路径 + 依次 \input 各章），xelatex 编译两遍，
   输出 main.pdf 并报告页数与残余越界。

## 翻译契约要点（prompt.md 的核心，必须逐条执行）

### 忠实度
- 逐段全译：不总结、不删减、不增补。每段、每例、每脚注、每道练习题都要在译文中。
- 页标记 `<!-- [p.NN] -->` 转为 `% [p.NN]` 注释保留，便于对照校对。
- 公式：Unicode 数学符号转写为标准 LaTeX；原文编号公式用 `\tag{N.N}` 保留编号。

### 缩写规则（强制）
- 缩写**首次出现**必须给出完整原词，格式：`中文全称（English full term, 缩写）`
  例：局部平均处理效应（local average treatment effect, LATE）
- 此后只用缩写或中文。常见缩写全称集中在 glossary.md 的"缩写与全称"表维护。

### 信达雅（防机翻，强制）
- **意译而非直译**：以段落为单位重组，先条件后结论、先背景后重点。
- 长句拆短：英文一句话信息量大时拆成 2–3 个中文短句。
- 禁止欧化排比：英文平行结构（"reading ..., using ..., estimating ..."）
  不逐词对应，改写成中文流水句。
- 少用被动式（"被认为是" → "我们认为"或改主动）；"的"字连续不超过两个。
- 不用翻译腔短语："作为一个……"、"基于……的角度"、"在……的情况下"堆砌。
- 保留原书语气：教学口吻的 "you" 译"你"，干净利落，可用四字结构但不做作。
- 输出前通读一遍，专删读起来像翻译的句子。

### 表格防越界（强制）
- 含长文本的列**必须**用 `p{宽度}` 或 `tabularx` 的 X 列；禁止用 `l`/`c`
  承载会换行的长句。
- 各列宽度之和（含列间距）不超过文本宽度（ctexbook 默认约 16cm）；
  三列长文本参考 `p{3.4cm} p{3.4cm} p{7.6cm}`。
- 数字列保持 `l`/`r` 即可，不要全部套 p{} 导致难看。
- 编译日志不得出现 `Overfull \hbox`（03 脚本自动检查）。

### 占位符 → LaTeX
- `[TABLE name | 题注]` → 对照 PNG 重制 booktabs 三线表（数据必须与 PNG 一致，不编造）
- `[FIGURE name | 题注]` → `\includegraphics[width=\textwidth]{name.png}`
- `[CALLOUT name | 标题]` → `\begin{insightbox}{标题中文}...\end{insightbox}`
- 输出中不得残留任何占位符。

## 已踩过的坑（务必规避）

- **AI 翻译输出可能被静默截断**：长章分块翻译时极易丢掉后半章（症状：编译出的 PDF
  页数远少于预期）。03 脚本会核对 text.md 与 chNN.tex 的页标记集合，缺页即报
  `missing page markers (truncated output?)`——每次翻译后必须跑校验。
- 分块翻译不要按"估计剩余篇幅"截断，按页标记或小节边界切块，每块译完立即追加。
- **页标记 `% [p.NN]` 必须独占一行或行尾**：放在一行中间会把该行剩余文字全部注释掉
  （03 脚本已加检查：`page marker(s) with text after them on the same line`）。
- **子代理最终报告可能错乱但产物正常**：判断翻译是否完成以 03 校验结果为准，
  不要只信报告；也不要因为报告异常就重跑整章。
- **原书表格可能自身排印越界**（右缘被裁切）：照录可见部分，截断处以 \ldots{} 标示
  并加"译注"说明，不编造数据；PNG 裁剪过窄时可用 PyMuPDF 重新渲染整页核对。
- **`\centering` 只能写在 table/figure 环境内部**：在正文顶层裸用（如给无题注的
  tabular 居中）会从那一点泄漏到章节末尾所有后续段落，症状是"某节之后正文全部
  居中"。无环境表格用 `\begin{center}...\end{center}` 包裹；03 校验查不出这类
  逻辑排版问题，拼装后要抽页目检。
- **拼装 main.tex 必须补齐原书结构**：titlepage（书名/副标题/作者）、
  `\frontmatter`+`\tableofcontents`+`\mainmatter`、以及按原书一级书签插入
  `\part{...}` 分部页，否则目录层级与原书对不上。
- **多章并行翻译时不要让子代理改 glossary.md**（会冲突）：让它们在最终报告中
  列出新术语，由主会话定期合并；跨章复用术语（如 always-takers 等）要在合并时
  统一各章译法。
- PyMuPDF `Rect |=` 增强赋值不可靠，合并矩形用显式 min/max 构造。
- 全矢量 PDF（零内嵌位图）直接用路径聚类提取，无需截图拼接。
- 公式 Unicode 提取质量高时，纯文本翻译即可，无需把公式截图。
- tcolorbox 必须 `\tcbuselibrary{breakable}`，否则跨页要点框编译报错。
- PDF 物理页号 = 书印刷页号 + 前置页偏移（本书为 +18），切章脚本里处理。
- 翻译质量问题的典型症状：缩写裸奔无全称、欧化排比句、被动连用、
  表格长句不换行越界——对照上方三条强制规则逐项自检。

## 新章节/新术语的维护

- glossary.md 是唯一术语依据：翻译中新出现的术语先补进表再继续，保证全书一致。
- 校验 FAIL 时先修编译错误，再人工通读一遍译文语感，最后才进入下一章。
