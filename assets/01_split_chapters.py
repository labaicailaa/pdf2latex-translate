# Split the PDF into per-chapter text files using the built-in TOC.
# Usage: python 01_split_chapters.py [chapter_number]   e.g. "1" for ch01 only
import re
import sys
from pathlib import Path

import fitz

PDF = Path(__file__).resolve().parent.parent / "Empirical Corporate Finance_Murray Frank.pdf"
OUT = PDF.parent / "chapters"


def get_chapters(doc):
    # level-2 TOC entries are chapters: (title, start_page_1based)
    return [(t[1], t[2]) for t in doc.get_toc() if t[0] == 2]


def chapter_dir_name(title):
    # "1 Structural and Causal Approaches" -> ch01 ; "A ..." -> chA
    m = re.match(r"([0-9A-Za-z]+)", title)
    token = m.group(1)
    return f"ch{int(token):02d}" if token.isdigit() else f"ch{token}"


def save_chapter(doc, title, start, end, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for pno in range(start - 1, end):  # TOC pages are 1-based
        lines.append(f"<!-- [p.{pno + 1}] -->")
        lines.append(doc[pno].get_text())
        lines.append("")
    (outdir / "text.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    doc = fitz.open(PDF)
    chaps = get_chapters(doc)
    n = doc.page_count
    for i, (title, page) in enumerate(chaps):
        end = chaps[i + 1][1] - 1 if i + 1 < len(chaps) else n
        name = chapter_dir_name(title)
        if only and name != f"ch{int(only):02d}":
            continue
        save_chapter(doc, title, page, end, OUT / name)
        print(f"{name}: pages {page}-{end}  {title}")


if __name__ == "__main__":
    main()
