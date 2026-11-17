"""
make_slides.py  —  5-slide PPTX for the GHCP Agentic-Session Trace Analytics project.
Run from repo root:
    D:\\ghcp\\venv\\Scripts\\python.exe make_slides.py
Output: ghcp_analysis_deck.pptx  (repo root)
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import copy, os

# ── colour palette ────────────────────────────────────────────────────────────
BG      = RGBColor(0x0D, 0x1B, 0x2A)   # dark navy
ACCENT  = RGBColor(0x00, 0xC8, 0xFF)   # cyan
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
GREY    = RGBColor(0xAA, 0xBB, 0xCC)
GREEN   = RGBColor(0x00, 0xE6, 0x9A)
ORANGE  = RGBColor(0xFF, 0x8C, 0x00)
RED     = RGBColor(0xFF, 0x45, 0x45)

FIGURES = "D:\\ghcp\\data\\figures"

W  = Inches(13.33)   # widescreen 16:9
H  = Inches(7.5)

# ── helpers ───────────────────────────────────────────────────────────────────
def new_prs():
    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H
    return prs

def blank_slide(prs):
    layout = prs.slide_layouts[6]   # completely blank
    return prs.slides.add_slide(layout)

def fill_bg(slide, colour=BG):
    from pptx.oxml.ns import qn
    from lxml import etree
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = colour

def txbox(slide, text, l, t, w, h,
          size=20, bold=False, colour=WHITE, align=PP_ALIGN.LEFT,
          italic=False, wrap=True):
    """Add a text box and return the run."""
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p  = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size    = Pt(size)
    run.font.bold    = bold
    run.font.italic  = italic
    run.font.color.rgb = colour
    return tb

def hrule(slide, t, colour=ACCENT, l=Inches(0.5), w=Inches(12.33), thickness=Pt(1.5)):
    """Thin horizontal line."""
    from pptx.util import Pt as _Pt
    line = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.LINE doesn't exist in add_shape; use connector
        l, t, w, Inches(0)
    )
    line.line.color.rgb = colour
    line.line.width     = thickness
    line.fill.background()

def rect(slide, l, t, w, h, fill_colour, line_colour=None):
    from pptx.util import Inches
    shp = slide.shapes.add_shape(1, l, t, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill_colour
    if line_colour:
        shp.line.color.rgb = line_colour
    else:
        shp.line.fill.background()
    return shp

def add_picture(slide, path, l, t, w, h=None):
    if not os.path.exists(path):
        return
    if h:
        slide.shapes.add_picture(path, l, t, w, h)
    else:
        slide.shapes.add_picture(path, l, t, w)

def bullet_box(slide, items, l, t, w, h, size=16, gap=Pt(6)):
    """
    items: list of (text, colour, bold)
    """
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, (text, colour, bold) in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.space_before = gap
        run = p.add_run()
        run.text = text
        run.font.size  = Pt(size)
        run.font.bold  = bold
        run.font.color.rgb = colour

def slide_number(slide, num):
    txbox(slide, str(num),
          Inches(12.8), Inches(7.1), Inches(0.4), Inches(0.3),
          size=11, colour=GREY, align=PP_ALIGN.RIGHT)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — Problem & Dataset
# ══════════════════════════════════════════════════════════════════════════════
def slide1(prs):
    sl = blank_slide(prs)
    fill_bg(sl)

    # left accent bar
    rect(sl, Inches(0), Inches(0), Inches(0.07), H, ACCENT)

    # title
    txbox(sl, "Analysing GitHub Copilot Agentic Sessions at Scale",
          Inches(0.35), Inches(0.3), Inches(9), Inches(1.3),
          size=34, bold=True, colour=WHITE)

    # sub
    txbox(sl, "Azure Public Dataset  ghcp-coding-agent-2026  ·  CC BY 4.0  ·  7 days, June 2026",
          Inches(0.35), Inches(1.55), Inches(9), Inches(0.5),
          size=16, colour=ACCENT)

    hrule(sl, Inches(2.15), l=Inches(0.35), w=Inches(12.5))

    # stat cards  (3 columns × 2 rows)
    cards = [
        ("301,026",    "Sessions",          ACCENT),
        ("1.19 M",     "Turns",             WHITE),
        ("9.31 M",     "LLM Calls",         WHITE),
        ("8.68 M",     "Tool Calls",        WHITE),
        ("886 M",      "Prompt Segments",   WHITE),
        ("3.22 GB",    "Compressed Source", GREY),
    ]
    cw, ch = Inches(1.95), Inches(1.4)
    gap    = Inches(0.18)
    x0, y0 = Inches(0.35), Inches(2.35)
    for i, (val, label, col) in enumerate(cards):
        cx = x0 + i * (cw + gap)
        # dark card bg
        rect(sl, cx, y0, cw, ch, RGBColor(0x14, 0x28, 0x3C))
        txbox(sl, val,   cx + Inches(0.1), y0 + Inches(0.1),
              cw - Inches(0.2), Inches(0.65),
              size=26, bold=True, colour=col, align=PP_ALIGN.CENTER)
        txbox(sl, label, cx + Inches(0.1), y0 + Inches(0.75),
              cw - Inches(0.2), Inches(0.4),
              size=12, colour=GREY, align=PP_ALIGN.CENTER)

    # challenge block (right column)
    rx, ry = Inches(12.33 - 3.4) + Inches(0.35), Inches(2.35)

    # pipeline challenge bullets
    bullet_box(sl,
        [
            ("Pipeline constraint", ACCENT,  True),
            ("· 1 GB RAM hard limit — consumer laptop", GREY, False),
            ("· DuckDB streaming, 2 threads, spill to D:\\", WHITE, False),
            ("· 606 shards ingested shard-by-shard", WHITE, False),
            ("· Peak RSS 1,077 MB  —  guard never tripped", GREEN, False),
            ("· Ingest: 50 min  ·  Analysis: 476 s", WHITE, False),
            ("· 7 SQL files → 28 CSV outputs", WHITE, False),
        ],
        Inches(0.35), Inches(4.0), Inches(12.5), Inches(3.0),
        size=15, gap=Pt(4)
    )

    slide_number(sl, 1)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — Architecture & Pipeline
# ══════════════════════════════════════════════════════════════════════════════
def slide2(prs):
    sl = blank_slide(prs)
    fill_bg(sl)
    rect(sl, Inches(0), Inches(0), Inches(0.07), H, ACCENT)

    txbox(sl, "System Architecture & Pipeline",
          Inches(0.35), Inches(0.25), Inches(10), Inches(0.8),
          size=28, bold=True, colour=WHITE)
    hrule(sl, Inches(1.1), l=Inches(0.35), w=Inches(12.5))

    # pipeline stages as arrow boxes
    stages = [
        ("Download",  "7 GitHub\nrelease ZIPs\n3.22 GB"),
        ("Ingest",    "606 shards\nstreaming\n50 min"),
        ("Validate",  "Row counts\nSHA checks\ndiag probes"),
        ("Analyse",   "8 SQL files\n39 chunks\n476 s"),
        ("Benchmark", "DuckDB vs\nPolars\n3 queries"),
        ("Report /\nBundle", "7 PNGs\nMarkdown\n0.4 MB zip"),
    ]
    bw, bh = Inches(1.85), Inches(1.5)
    gx = Inches(0.18)
    x0, y0 = Inches(0.35), Inches(1.3)
    for i, (title, body) in enumerate(stages):
        cx = x0 + i * (bw + gx)
        clr = ACCENT if i in (0, 3, 5) else RGBColor(0x14, 0x28, 0x3C)
        rect(sl, cx, y0, bw, bh, clr)
        txbox(sl, title, cx + Inches(0.07), y0 + Inches(0.1),
              bw - Inches(0.1), Inches(0.4),
              size=14, bold=True, colour=BG if i in (0, 3, 5) else ACCENT,
              align=PP_ALIGN.CENTER)
        txbox(sl, body,  cx + Inches(0.07), y0 + Inches(0.5),
              bw - Inches(0.1), Inches(0.9),
              size=11, colour=BG if i in (0, 3, 5) else WHITE,
              align=PP_ALIGN.CENTER)
        # arrow (except last)
        if i < len(stages) - 1:
            ax = cx + bw + Inches(0.02)
            txbox(sl, "▶", ax, y0 + Inches(0.55), Inches(0.16), Inches(0.4),
                  size=14, colour=GREY, align=PP_ALIGN.CENTER)

    # key design decisions
    hrule(sl, Inches(3.1), l=Inches(0.35), w=Inches(12.5), colour=GREY)
    txbox(sl, "Key Design Decisions",
          Inches(0.35), Inches(3.2), Inches(5), Inches(0.4),
          size=16, bold=True, colour=ACCENT)

    bullet_box(sl,
        [
            ("· DuckDB memory_limit = 1,000 MB, threads = 2 — never raised", WHITE, False),
            ("· Resumable checkpoints: SQLite tracks ingested shards", WHITE, False),
            ("· Spill to D:\\ — C:\\ never touched for data or venv", WHITE, False),
            ("· No Pandas/Polars eager frames in the main pipeline", WHITE, False),
            ("· 38 anonymised model IDs — no real names, no cost figures", GREY, False),
        ],
        Inches(0.35), Inches(3.65), Inches(6.0), Inches(3.5),
        size=14, gap=Pt(5)
    )

    # resource table (right side)
    table_data = [
        ("Stage",       "Wall time",    "Peak RSS"),
        ("Ingest",      "3,027 s",      "1,077 MB"),
        ("Analysis",    "476 s",        "1,176 MB"),
        ("Benchmark",   "~30 s",        "< 250 MB"),
        ("Figures",     "< 60 s",       "—"),
    ]
    tx0, ty0 = Inches(6.6), Inches(3.3)
    rw, rh   = Inches(5.6), Inches(0.42)
    for r, row in enumerate(table_data):
        for c, cell in enumerate(row):
            cx2 = tx0 + c * Inches(1.87)
            bg_c = RGBColor(0x00, 0x60, 0x80) if r == 0 else RGBColor(0x14, 0x28, 0x3C)
            rect(sl, cx2, ty0 + r * rh, Inches(1.87), rh, bg_c)
            txbox(sl, cell, cx2 + Inches(0.05), ty0 + r * rh + Inches(0.05),
                  Inches(1.77), rh - Inches(0.05),
                  size=12, bold=(r == 0), colour=WHITE if r == 0 else GREY,
                  align=PP_ALIGN.CENTER)

    slide_number(sl, 2)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — Cache & Prompt Composition
# ══════════════════════════════════════════════════════════════════════════════
def slide3(prs):
    sl = blank_slide(prs)
    fill_bg(sl)
    rect(sl, Inches(0), Inches(0), Inches(0.07), H, GREEN)

    txbox(sl, "Finding 1 · Cache Efficiency & Prompt Composition",
          Inches(0.35), Inches(0.25), Inches(10), Inches(0.8),
          size=26, bold=True, colour=WHITE)
    hrule(sl, Inches(1.1), l=Inches(0.35), w=Inches(12.5), colour=GREEN)

    # headline stat
    rect(sl, Inches(0.35), Inches(1.2), Inches(3.4), Inches(1.3), RGBColor(0x00, 0x40, 0x30))
    txbox(sl, "85.7%", Inches(0.35), Inches(1.25), Inches(3.4), Inches(0.75),
          size=46, bold=True, colour=GREEN, align=PP_ALIGN.CENTER)
    txbox(sl, "of prompt tokens are cached\n(token-weighted, corpus-wide)",
          Inches(0.35), Inches(1.95), Inches(3.4), Inches(0.5),
          size=12, colour=GREY, align=PP_ALIGN.CENTER)

    # cache ramp bullets
    bullet_box(sl,
        [
            ("Cache ramp-up within a turn:", ACCENT, True),
            ("  Call 1   →  46.2% cached  (cold prefix)", GREY, False),
            ("  Call 2   →  85.1%  (prefix cache kicks in)", WHITE, False),
            ("  Call 3   →  90.9%", WHITE, False),
            ("  Call 4+  →  ~92%  (plateau)", GREEN, False),
            ("  6.2% of calls have zero cache hit", ORANGE, False),
        ],
        Inches(0.35), Inches(2.65), Inches(4.5), Inches(2.8),
        size=14, gap=Pt(5)
    )

    # prompt composition bar (vertical stacked visual)
    segments = [
        ("Tool history\n(tool calls + fn logs)", 48.3, ACCENT),
        ("Conversation history\n(user + assistant)",  31.3, GREEN),
        ("System / instructions",                      12.9, ORANGE),
        ("Other tracked",                               1.4, GREY),
        ("Untracked",                                   6.1, RGBColor(0x40, 0x40, 0x50)),
    ]
    bx, by = Inches(5.1), Inches(1.2)
    bw2, bh2 = Inches(2.0), Inches(5.5)
    total_pct = sum(p for _, p, _ in segments)
    cur = by
    for label, pct, col in segments:
        seg_h = bh2 * (pct / 100.0)
        rect(sl, bx, cur, bw2, seg_h, col)
        # label to right
        txbox(sl, f"{pct:.1f}%  {label}",
              bx + bw2 + Inches(0.1), cur + seg_h * 0.2,
              Inches(4.9), max(seg_h, Inches(0.3)),
              size=12, colour=col if col != GREY else WHITE)
        cur += seg_h

    txbox(sl, "Prompt segment breakdown\n(% of token volume)",
          bx, by - Inches(0.4), bw2, Inches(0.35),
          size=12, bold=True, colour=GREY, align=PP_ALIGN.CENTER)

    txbox(sl, "93.9% of prompt tokens covered by tracked segments",
          Inches(0.35), Inches(6.9), Inches(8), Inches(0.4),
          size=12, colour=GREY, italic=True)

    # figure (cache by call position)
    fig_path = os.path.join(FIGURES, "cache_by_call_position.png")
    add_picture(sl, fig_path, Inches(10.1), Inches(1.2), Inches(3.0))

    slide_number(sl, 3)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — Time & Concentration
# ══════════════════════════════════════════════════════════════════════════════
def slide4(prs):
    sl = blank_slide(prs)
    fill_bg(sl)
    rect(sl, Inches(0), Inches(0), Inches(0.07), H, ORANGE)

    txbox(sl, "Finding 2 · Time Decomposition & Usage Concentration",
          Inches(0.35), Inches(0.25), Inches(10), Inches(0.8),
          size=26, bold=True, colour=WHITE)
    hrule(sl, Inches(1.1), l=Inches(0.35), w=Inches(12.5), colour=ORANGE)

    # ----- LEFT: time -----
    # donut-like bars: LLM / Tool / Residual
    bars = [
        ("LLM inference",   40.8, ACCENT),
        ("Tool execution",  44.1, ORANGE),
        ("Residual/comm.",  15.1, GREY),
    ]
    bx2, by2 = Inches(0.35), Inches(1.3)
    bw3, bh3 = Inches(4.5), Inches(0.55)
    for i, (label, pct, col) in enumerate(bars):
        ty2 = by2 + i * (bh3 + Inches(0.15))
        rect(sl, bx2, ty2, bw3 * (pct / 100.0), bh3, col)
        txbox(sl, f"{label}  {pct}%",
              bx2 + bw3 + Inches(0.1), ty2 + Inches(0.1),
              Inches(2.5), bh3,
              size=14, colour=col)

    txbox(sl, "Share of turn wall-clock span (excl. far out-of-window)",
          bx2, by2 - Inches(0.35), Inches(6.5), Inches(0.3),
          size=12, colour=GREY, italic=True)

    bullet_box(sl,
        [
            ("Turn span   p50 = 49.8 s  ·  p90 = 337.8 s", WHITE, False),
            ("Idle between turns   p50 = 152 s (~2.5 min)", ORANGE, False),
            ("                        p90 = 1,843 s (~30 min)", ORANGE, False),
            ("73% of idle gaps > 1 min  —  human think-time", GREY, False),
            ("dominates session wall clock", GREY, False),
        ],
        bx2, Inches(3.3), Inches(6.0), Inches(2.0),
        size=14, gap=Pt(5)
    )

    # ----- RIGHT: concentration -----
    hrule(sl, Inches(1.1), l=Inches(6.6), w=Inches(6.5), colour=ORANGE)
    txbox(sl, "Usage Concentration  (Lorenz / Gini)",
          Inches(6.6), Inches(1.15), Inches(6.5), Inches(0.4),
          size=16, bold=True, colour=ORANGE)

    conc_items = [
        ("Prompt-token Gini coefficient",  "0.802", ACCENT),
        ("Cached-token Gini coefficient",  "0.818", ACCENT),
        ("", "", WHITE),
        ("Top 10% sessions consume",       "68.8%  of cached tokens", GREEN),
        ("Top 10% sessions consume",       "57.0%  of completions",   GREEN),
        ("Top   1% sessions consume",      "21.6%  of cached tokens", ORANGE),
    ]
    ty3 = Inches(1.65)
    for label, val, col in conc_items:
        if not label:
            ty3 += Inches(0.15)
            continue
        txbox(sl, label, Inches(6.6), ty3, Inches(3.6), Inches(0.4),
              size=13, colour=GREY)
        txbox(sl, val,   Inches(10.2), ty3, Inches(2.9), Inches(0.4),
              size=13, bold=True, colour=col)
        ty3 += Inches(0.42)

    # tool reliability table
    hrule(sl, Inches(4.0), l=Inches(6.6), w=Inches(6.5), colour=GREY)
    txbox(sl, "Tool Reliability",
          Inches(6.6), Inches(4.1), Inches(4), Inches(0.35),
          size=15, bold=True, colour=ORANGE)

    tool_rows = [
        ("Tool",              "Calls",    "Fail %",  "p50 latency"),
        ("get_file",          "3.08 M",   "2.4%",    "—"),
        ("run_command",       "1.39 M",   "11.4%",   "430 ms"),
        ("run_build",         "0.42 M",   "21.6% ⚠", "5,053 ms"),
    ]
    tx2, ty4 = Inches(6.6), Inches(4.5)
    cws = [Inches(2.0), Inches(1.3), Inches(1.2), Inches(1.8)]
    for r, row in enumerate(tool_rows):
        for c, cell in enumerate(row):
            cx3 = tx2 + sum(cws[:c])
            bg_c2 = RGBColor(0x00, 0x40, 0x60) if r == 0 else RGBColor(0x14, 0x28, 0x3C)
            rect(sl, cx3, ty4 + r * Inches(0.42), cws[c], Inches(0.42), bg_c2)
            col3 = WHITE if r == 0 else (RED if "⚠" in cell else GREY)
            txbox(sl, cell, cx3 + Inches(0.05), ty4 + r * Inches(0.42) + Inches(0.04),
                  cws[c] - Inches(0.05), Inches(0.34),
                  size=12, colour=col3, bold=(r == 0))

    # lorenz figure
    fig_path = os.path.join(FIGURES, "lorenz.png")
    add_picture(sl, fig_path, Inches(6.6), Inches(1.1), Inches(0.0) + Inches(6.5) - Inches(0.3),
                h=Inches(2.6))

    slide_number(sl, 4)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — Benchmark & Conclusions
# ══════════════════════════════════════════════════════════════════════════════
def slide5(prs):
    sl = blank_slide(prs)
    fill_bg(sl)
    rect(sl, Inches(0), Inches(0), Inches(0.07), H, ACCENT)

    txbox(sl, "DuckDB vs Polars Benchmark · Conclusions",
          Inches(0.35), Inches(0.25), Inches(10), Inches(0.8),
          size=26, bold=True, colour=WHITE)
    hrule(sl, Inches(1.1), l=Inches(0.35), w=Inches(12.5))

    # benchmark table
    headers = ["Query", "Engine", "Wall time", "Peak RSS", "Verdict"]
    rows = [
        ("7-day aggregation",    "DuckDB",  "5.67 s", "123.5 MB", "✓ low RAM"),
        ("7-day aggregation",    "Polars",  "1.99 s", "236.2 MB", "⚡ faster"),
        ("Group-by: session",    "DuckDB",  "2.14 s",  "98.3 MB", "✓ low RAM"),
        ("Group-by: session",    "Polars",  "0.87 s", "212.4 MB", "⚡ faster"),
        ("Group-by: model",      "DuckDB",  "1.03 s",  "89.1 MB", "✓ low RAM"),
        ("Group-by: model",      "Polars",  "0.44 s", "178.6 MB", "⚡ faster"),
    ]
    cws2 = [Inches(2.5), Inches(1.4), Inches(1.4), Inches(1.4), Inches(1.6)]
    tx3, ty5 = Inches(0.35), Inches(1.25)
    all_rows = [headers] + rows
    for r, row in enumerate(all_rows):
        for c, cell in enumerate(row):
            cx4 = tx3 + sum(cws2[:c])
            if r == 0:
                bg_c3 = RGBColor(0x00, 0x60, 0x80)
            elif r % 2 == 1:
                bg_c3 = RGBColor(0x14, 0x28, 0x3C)
            else:
                bg_c3 = RGBColor(0x0D, 0x1F, 0x30)
            rect(sl, cx4, ty5 + r * Inches(0.42), cws2[c], Inches(0.42), bg_c3)
            col4 = WHITE if r == 0 else (GREEN if "✓" in cell else (ACCENT if "⚡" in cell else GREY))
            txbox(sl, cell, cx4 + Inches(0.05), ty5 + r * Inches(0.42) + Inches(0.04),
                  cws2[c] - Inches(0.05), Inches(0.34),
                  size=12, colour=col4, bold=(r == 0))

    txbox(sl, "All checksums identical — DuckDB and Polars produce the same results.",
          Inches(0.35), Inches(4.3), Inches(8.5), Inches(0.4),
          size=13, colour=GREEN, italic=True)

    # conclusions
    hrule(sl, Inches(4.75), l=Inches(0.35), w=Inches(12.5), colour=GREY)
    txbox(sl, "Key Takeaways",
          Inches(0.35), Inches(4.85), Inches(5), Inches(0.4),
          size=16, bold=True, colour=ACCENT)

    conclusions = [
        ("Cache dominates prompt cost",     "85.7% cached (token-weighted); first call cold, all subsequent hot",         GREEN),
        ("Tool time ≈ LLM time",            "44% tool execution vs 41% LLM inference — agentic, not just generative",     ACCENT),
        ("Heavy usage skew",                "Gini ~0.80; top 10% of sessions consume ~69% of cached tokens",              ORANGE),
        ("Human idle time dominates",       "Median 2.5 min gap between turns; p90 = 30 min",                             GREY),
        ("DuckDB wins on memory",           "2× lower RSS vs Polars; viable on 1 GB constraint without sampling",         ACCENT),
        ("run_build most fragile tool",     "21.6% fail rate — highest-impact reliability gap in the corpus",             RED),
    ]
    ty6 = Inches(5.3)
    for title, detail, col in conclusions:
        txbox(sl, f"● {title}", Inches(0.35), ty6, Inches(4.0), Inches(0.3),
              size=13, bold=True, colour=col)
        txbox(sl, detail, Inches(4.5), ty6, Inches(8.6), Inches(0.3),
              size=12, colour=GREY)
        ty6 += Inches(0.33)

    slide_number(sl, 5)


# ══════════════════════════════════════════════════════════════════════════════
def main():
    prs = new_prs()
    slide1(prs)
    slide2(prs)
    slide3(prs)
    slide4(prs)
    slide5(prs)
    out = "ghcp_analysis_deck.pptx"
    prs.save(out)
    print(f"Saved -> {out}  ({os.path.getsize(out) // 1024} KB)")

if __name__ == "__main__":
    main()
