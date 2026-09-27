# Extract vector figures/tables from a chapter and insert placeholders into text.md.
# Usage: python 02_extract_figures.py ch01
# Outputs: chapters/ch01/figures/*.png , chapters/ch01/manifest.md
# Handles three graphic kinds:
#   charts   (many drawing paths)  -> [FIGURE name | caption]  + crop
#   tables   (grouped rules)       -> [TABLE name | caption]   + crop (AI rebuilds booktabs)
#   callouts (boxed text, e.g. Key Insight) -> [CALLOUT name] + crop (AI translates text)
# Body references like "Table 1.1 summarizes..." never pair with a graphic -> untouched.
import re
import sys
from pathlib import Path

import fitz

PDF = Path(__file__).resolve().parent.parent / "Empirical Corporate Finance_Murray Frank.pdf"
CAPTION_RE = re.compile(r"^(Figure|Table)\s+(\d+\.\d+)", re.IGNORECASE)
MIN_CHART_W, MIN_CHART_H = 90, 70
RULE_W, RULE_H, RULE_GAP = 180, 5, 260  # rules up to 260pt apart belong to one table
MAX_PAIR_DIST = 260
CHART_MIN_PATHS = 6      # fewer paths -> callout box, not a chart
CALLOUT_MIN_WORDS = 12   # words inside rect to count as text box


def caption_rects(page):
    out = []
    for kind in ("Figure", "Table"):
        for r in page.search_for(f"{kind} "):
            words = page.get_text("words", clip=fitz.Rect(r.x1 - 1, r.y0 - 2, r.x1 + 40, r.y1 + 2))
            toks = sorted(words, key=lambda w: w[0])
            if toks and re.match(r"^\d+\.\d+", toks[0][4]):
                label = re.match(r"^(\d+\.\d+)", toks[0][4]).group(1)
                out.append((kind, label, fitz.Rect(r)))
    return out


def table_candidates(page):
    h = page.rect.height
    # exclude running-head / footer rules
    rules = [fitz.Rect(d["rect"]) for d in page.get_drawings()
             if d["rect"].width >= RULE_W and d["rect"].height <= RULE_H
             and 70 < d["rect"].y0 < h - 60]
    rules.sort(key=lambda r: r.y0)
    groups = []
    for r in rules:
        if groups and r.y0 - groups[-1].y1 <= RULE_GAP:
            g = groups[-1]
            groups[-1] = fitz.Rect(min(g.x0, r.x0), min(g.y0, r.y0), max(g.x1, r.x1), max(g.y1, r.y1))
        else:
            groups.append(fitz.Rect(r))
    return [g for g in groups if g.width >= RULE_W and 15 <= g.height <= 700]


def classify(page, rect):
    """'chart' if rect contains many paths, else 'callout' if it holds text."""
    n_paths = sum(1 for d in page.get_drawings() if fitz.Rect(d["rect"]).intersects(rect))
    words = page.get_text("words", clip=rect)
    if n_paths >= CHART_MIN_PATHS:
        return "chart"
    if len(words) >= CALLOUT_MIN_WORDS:
        return "callout"
    return "ignore"


def v_dist(g, c):
    if g.y1 <= c.y0:
        return c.y0 - g.y1
    if g.y0 >= c.y1:
        return g.y0 - c.y1
    return 0.0


def main():
    name = sys.argv[1]
    ch = Path(__file__).resolve().parent.parent / "chapters" / name
    figdir = ch / "figures"
    figdir.mkdir(exist_ok=True)
    text = (ch / "text.md").read_text(encoding="utf-8")

    doc = fitz.open(PDF)
    page_nums = sorted({int(m) for m in re.findall(r"<!-- \[p\.(\d+)\] -->", text)})

    paired = {}       # (page, kind, label) -> png name, for Figure/Table captions
    callouts = {}     # page -> list of (png, first_line_text)
    manifest, counters = [], {}

    for pno1 in page_nums:
        pno = pno1 - 1
        page = doc[pno]

        cands = []  # (rect, origin)
        for r in page.cluster_drawings():
            r = fitz.Rect(r)
            if r.width >= MIN_CHART_W and r.height >= MIN_CHART_H:
                cands.append((r, "cluster"))
        clusters = [c for c, o in cands]
        for t in table_candidates(page):
            if not any(c.contains(t) for c in clusters):
                cands.append((t, "rules"))

        caps = caption_rects(page)
        used_caps = set()
        for g, origin in cands:
            if origin == "rules":
                kind = "table" if len(page.get_text("words", clip=g)) >= 5 else "ignore"
            else:
                kind = classify(page, g)
            if kind == "ignore":
                continue
            counters[pno1] = counters.get(pno1, 0) + 1
            prefix = {"chart": "fig", "table": "tbl", "callout": "box"}[kind]
            png = f"{prefix}_p{pno1:03d}_{counters[pno1]}"
            clip = (g + (-6, -6, 6, 6)) & page.rect
            page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), clip=clip).save(figdir / f"{png}.png")

            if kind in ("chart", "table"):
                best, best_d = None, 1e9
                for i, (ck, label, cr) in enumerate(caps):
                    d = v_dist(g, cr)
                    if d < best_d and d <= MAX_PAIR_DIST and i not in used_caps:
                        best, best_d = i, d
                if best is None:
                    manifest.append(f"- `{png}.png` p.{pno1} {kind} at {tuple(round(v) for v in g)}: **no caption matched**")
                    continue
                used_caps.add(best)
                ck, label, cr = caps[best]
                paired[(pno1, ck, label)] = png
                manifest.append(f"- `{png}.png`  p.{pno1}  {ck} {label}  dist={best_d:.0f}pt")
            else:  # callout: remember first text line for md matching
                first = page.get_text("text", clip=g).strip().split("\n")[0].strip()
                callouts.setdefault(pno1, []).append((png, first))
                manifest.append(f"- `{png}.png`  p.{pno1}  callout: {first[:70]}")
        for i, (ck, label, cr) in enumerate(caps):
            if i not in used_caps and (pno1, ck, label) not in paired:
                # may be a genuine caption whose graphic sits on a neighbouring page
                manifest.append(f"- p.{pno1} {ck} {label} @y={cr.y0:.0f}: unpaired")

    # md pass: replace paired caption lines; insert CALLOUT markers before box first lines
    callout_by_line = {}
    for pg, items in callouts.items():
        for png, first in items:
            callout_by_line[(pg, first)] = f"[CALLOUT {png} | {first}]"

    out_lines, page_no = [], None
    for line in (lines2 := text.split("\n")):
        m = re.match(r"<!-- \[p\.(\d+)\] -->", line)
        if m:
            page_no = int(m.group(1))
        key = (page_no, line.strip())
        if key in callout_by_line:
            out_lines.append(callout_by_line.pop(key))
            continue
        m = CAPTION_RE.match(line.strip())
        # real captions read "Table 1.1. Title..." / "Figure 3.2: Title"; references
        # like "Table 1.1 summarizes..." have no punctuation right after the number
        if m and page_no and re.match(r"^(Figure|Table)\s+\d+\.\d+[.:]", line.strip(), re.I):
            k = (page_no, m.group(1).capitalize(), m.group(2))
            if k in paired:
                kind = "TABLE" if k[1] == "Table" else "FIGURE"
                out_lines.append(f"[{kind} {paired[k]} | {line.strip()}]")
                continue
        out_lines.append(line)

    (ch / "text.md").write_text("\n".join(out_lines), encoding="utf-8")
    (ch / "manifest.md").write_text("# Figures / Tables manifest\n\n" + "\n".join(manifest) + "\n",
                                    encoding="utf-8")
    print(f"paired captions: {len(paired)}, callouts: {sum(len(v) for v in callouts.values())}, "
          f"unmatched callout lines: {len(callout_by_line)}")


if __name__ == "__main__":
    main()
