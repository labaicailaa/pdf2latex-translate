# Validate a translated chapter and compile it standalone.
# Usage: python 03_check_chapter.py ch01
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def check(tex_text, src_text=""):
    errs = []
    if re.search(r"\[(FIGURE|TABLE)\s", tex_text):
        errs.append("leftover [FIGURE/TABLE ...] placeholder")
    bad = sorted(set(re.findall(r"[\U0001D400-\U0001D7FF\u2102-\u214F]", tex_text)))
    if bad:
        errs.append(f"unconverted Unicode math chars: {' '.join(bad)}")
    envs = {}
    for m in re.finditer(r"\\(begin|end)\{(\*?\w+\*?)\}", tex_text):
        envs.setdefault(m.group(2), [0, 0])[0 if m.group(1) == "begin" else 1] += 1
    for name, (b, e) in envs.items():
        if b != e:
            errs.append(f"environment {name}: {b} begin vs {e} end")
    t = re.sub(r"(?<!\\)%.*", "", tex_text).replace(r"\{", "").replace(r"\}", "")
    if t.count("{") != t.count("}"):
        errs.append(f"braces: {t.count('{')} open vs {t.count('}')} close")
    # every source page marker must survive as a % comment (catches truncated output)
    if src_text:
        src_pages = set(re.findall(r"<!-- \[p\.(\d+)\] -->", src_text))
        got_pages = set(re.findall(r"% \[p\.(\d+)\]", tex_text))
        missing = sorted(src_pages - got_pages, key=int)
        if missing:
            errs.append(f"missing page markers (truncated output?): {', '.join(missing)}")
    # a % [p.NN] marker must not have text after it on the same line (rest gets commented out)
    midline = sum(1 for ln in tex_text.splitlines()
                  if re.search(r"% \[p\.\d+\]\s+\S", ln))
    if midline:
        errs.append(f"{midline} page marker(s) with text after them on the same line")
    return errs


def compile_chapter(name):
    ch = ROOT / "chapters" / name
    preamble = (ROOT / "preamble.tex").read_text(encoding="utf-8")
    wrapper = ROOT / "chapters" / f"compile_{name}.tex"
    wrapper.write_text(
        preamble
        + f"\n\\graphicspath{{{chr(123)}{name}/figures/{chr(125)}}}\n"
        + "\\begin{document}\n"
        + f"\\input{{{name}/{name}.tex}}\n"
        + "\\end{document}\n",
        encoding="utf-8",
    )
    r = subprocess.run(
        ["xelatex", "-interaction=nonstopmode", "-halt-on-error", f"compile_{name}.tex"],
        cwd=ROOT / "chapters", capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    log = (ROOT / "chapters" / f"compile_{name}.log")
    overfull = []
    if log.exists():
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.search(r"Overfull \\hbox \((\d+(?:\.\d+)?)pt", line)
            if m and float(m.group(1)) > 5:  # ignore trivial overflows below 5pt
                overfull.append(line.strip())
    if r.returncode != 0 and log.exists():
        tail = "\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-25:])
        print(tail)
    if overfull:
        print(f"OVERFULL HBOX ({len(overfull)}):")
        print("\n".join(overfull[:10]))
    return "OK" if (r.returncode == 0 and not overfull) else "FAIL"


def main():
    name = sys.argv[1]
    ch = ROOT / "chapters" / name
    tex_file = ch / f"{name}.tex"
    if not tex_file.exists():
        print(f"missing {tex_file}")
        sys.exit(1)
    src_file = ch / "text.md"
    src_text = src_file.read_text(encoding="utf-8") if src_file.exists() else ""
    errs = check(tex_file.read_text(encoding="utf-8"), src_text)
    print("checks:", "\n".join(errs) if errs else "OK")
    print("compile:", compile_chapter(name))


if __name__ == "__main__":
    main()
