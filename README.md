# pdf2latex-translate

把英文学术 PDF 教材逐章翻译成中文 LaTeX 笔记的 TRAE skill。严格逐段全译，不总结、不删减；图形裁剪为 PNG 插入，表格重制为 booktabs 三线表，要点框转为 tcolorbox。

## 安装

把本仓库放到 TRAE 的 skills 目录下即可，入口是根目录的 `SKILL.md`。也可以只把 `assets/` 下的脚本与模板复制到翻译项目根目录使用。

## 管线流程

每章五步：

1. **切章** `python assets/01_split_chapters.py [N]`
   按 PDF 书签切分，产出 `chapters/chNN/text.md`，段落间插入 `<!-- [p.NN] -->` 页标记。先不带参数跑一次可列出书签结构，确认章节边界。
2. **图表提取** `python assets/02_extract_figures.py chNN`
   识别表格、统计图与要点框，产出 `figures/*.png` 与 `manifest.md`，并在正文插入 `[TABLE/FIGURE/CALLOUT name | caption]` 占位符。
3. **翻译** `text.md` → `chNN.tex`
   按 `assets/prompt.md` 的翻译契约与 `assets/glossary.md` 的术语表执行，逐段全译并保留页标记。
4. **校验** `python assets/03_check_chapter.py chNN`
   检查占位符残留、Unicode 数学字符、环境与括号配对、页标记覆盖，并用 xelatex 编译检测 `Overfull \hbox` 越界。
5. **拼装** `python assets/04_assemble.py`
   生成 `main.tex`，编译两遍输出 `main.pdf`，报告页数与残余越界。

单章校验通过后再进入下一章。

## 文件说明

| 文件 | 用途 |
| --- | --- |
| `SKILL.md` | skill 入口，含完整流程、翻译契约要点与已踩过的坑 |
| `assets/01_split_chapters.py` | 按书签切章，插入页标记 |
| `assets/02_extract_figures.py` | 提取表格、统计图与要点框 |
| `assets/03_check_chapter.py` | 单章校验并编译检测越界 |
| `assets/04_assemble.py` | 拼装全书 `main.tex` 并编译 |
| `assets/prompt.md` | 翻译契约模板 |
| `assets/glossary.md` | 术语表模板 |
| `assets/preamble.tex` | ctexbook + tcolorbox(breakable) + threeparttable 导言区 |

## 使用方式

把 `assets/` 下的脚本与模板复制到翻译项目根目录，按书修改脚本顶部的 PDF 路径与书名，再按上面的五步逐章执行。编译用 xelatex。

翻译契约要点、易错点与更多细节见 `SKILL.md`。

## License

MIT