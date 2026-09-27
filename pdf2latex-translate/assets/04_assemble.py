# Assemble all translated chapters into main.tex and compile the full book.
# Usage: python 04_assemble.py
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = [f"ch{i:02d}" for i in range(1, 16)] + ["chA"]


def main():
    for name in CHAPTERS:
        tex = ROOT / "chapters" / name / f"{name}.tex"
        if not tex.exists():
            print(f"missing {tex}", file=sys.stderr)
            sys.exit(1)

    preamble = (ROOT / "preamble.tex").read_text(encoding="utf-8")
    paths = " ".join(f"{{chapters/{c}/figures/}}" for c in CHAPTERS)
    inputs = "\n".join(f"\\input{{chapters/{c}/{c}.tex}}" for c in CHAPTERS)
    main_tex = (
        preamble
        + f"\n\\graphicspath{{{paths}}}\n"
        + "\\begin{document}\n"
        + inputs
        + "\n\\end{document}\n"
    )
    (ROOT / "main.tex").write_text(main_tex, encoding="utf-8")
    print("wrote main.tex")

    for _ in range(2):  # second pass for cross references
        r = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if r.returncode != 0:
            log = ROOT / "main.log"
            if log.exists():
                print("\n".join(log.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]))
            print("compile: FAIL")
            sys.exit(1)

    overfull = []
    log = ROOT / "main.log"
    if log.exists():
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if "Overfull \\hbox" in line:
                overfull.append(line.strip())
    if overfull:
        print(f"OVERFULL HBOX ({len(overfull)}):")
        print("\n".join(overfull[:10]))
    try:
        import fitz

        print("compile: OK, pages:", fitz.open(ROOT / "main.pdf").page_count)
    except ImportError:
        print("compile: OK")


if __name__ == "__main__":
    main()
