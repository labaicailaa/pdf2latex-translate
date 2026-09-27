# 翻译契约（每一章的每个翻译任务都必须完整遵守）

## 任务
将 `chapters/chNN/text.md` 逐段翻译为中文，输出 LaTeX 文件 `chapters/chNN/chNN.tex`。
本质是**忠实翻译**：不总结、不删减、不增补、不改写结构。原文每一个段落、例证、
脚注、练习题都必须出现在译文中。

## 输出格式
1. 文件以 `\chapter{章标题中文}` 开始，之后为正文
2. 小节用 `\section`，子小节用 `\subsection`，编号由 LaTeX 自动生成，不要手写编号
3. 原文页标记 `<!-- [p.NN] -->` 转为注释 `% [p.NN]` 保留在对应位置
4. 数学公式：text.md 中的 Unicode 数学符号（𝑌𝑖𝑡、𝛽、𝛼ᵢ 等）必须转写为标准 LaTeX
   （如 `$Y_{it}$`、`\beta`、`\alpha_i`）；独立公式用 `\[...\]` 或 `equation` 环境，
   原文带编号的公式 (3.3) 用 `\tag{3.3}` 保留原编号
5. 转义：正文中 `%` → `\%`、`&` → `\&`、`_` → `\_`、`#` → `\#`
6. 只输出 body（从 `\chapter` 开始），不含 documentclass / preamble

## 占位符处理（关键，禁止遗漏或改名）
- `[TABLE tbl_pNNN_K | 题注]` → 查看 `figures/tbl_pNNN_K.png`，将表格重制为
  `booktabs` 三线表（`table` 浮动体 + `\caption{题注中文}` + `\label{tab:...}`），
  表格数据必须与 PNG 完全一致，不编造数字
- `[FIGURE fig_pNNN_K | 题注]` → `figure` 浮动体 +
  `\includegraphics[width=\textwidth]{fig_pNNN_K.png}` + `\caption{题注中文}`
  文件名保持原样
- `[CALLOUT box_pNNN_K | 标题]` → 将紧随其后的段落放入
  `\begin{insightbox}{标题中文}...\end{insightbox}` 环境，内容完整翻译
- 输出中不得残留任何 `[TABLE` / `[FIGURE` / `[CALLOUT` 占位符

## 术语与风格
- 术语严格按 `glossary.md`，表中没有的术语保持一致、自然的译法
- **缩写规则**：缩写首次出现时必须给出完整原词，格式为
  `中文全称（English full term, 缩写）`，例如：局部平均处理效应（local average
  treatment effect, LATE）；此后只用缩写。常见缩写（OLS、IV、GMM、SMM、MLE、
  ATE、ATT、CATE、LATE、SUTVA、DiD、RD、iid、AR(1)）全称见 glossary.md
- **信达雅要求**：译文必须符合中文的逻辑和语感，逐段意译而非逐句直译：
  - 英文长句按中文习惯拆短重组，先条件后结论、先背景后重点
  - 禁止保留英文的修饰语挂靠结构（如"读着……的论文，使用着……的估计量"这类
    一一对应的欧化排比），改写成自然的中文流水句
  - 少用被动式；"的"字连续不超过两个；不用翻译腔短语（"作为一个……"、
    "基于……的角度"、"在……的情况下"堆砌）
  - 语气保持原书的口语化教学风格（"you" 译为"你"），干净利落，可用四字结构
    但不做作
- 数字、变量、引用编号（如 Section 1.7 → 第 1.7 节、Table 1.2 → 表 1.2）保持对应
- 练习题（Exercises）逐题翻译，保留题号

## 表格防越界规则（强制）
- 任何含长文本的列必须用 `p{宽度}` 或 `tabularx` 的 X 列，禁止用 `l`/`c` 承载
  会换行的长句
- 各列宽度之和加列间距不得超过文本宽度（本文档约 16cm）；三列长文本表参考
  `p{3.4cm} p{3.4cm} p{7.6cm}` 的分配
- 编译日志中不得出现 `Overfull \hbox`（由 03 脚本自动检查）

## 自检（输出前）
- 段落数量与原文一一对应（可多于不可少于原文段落数）
- 无残留占位符、无 Unicode 数学字符、环境配对完整
- 每个缩写首次出现处都有全称；通读一遍，删掉欧化句式
