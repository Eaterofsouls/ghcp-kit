"""
make_slides_v2.py  —  GHCP analysis deck, redesigned to match SaaS-Pulse design language.
Design system: Inter font, #f6f7f9 bg, white panel cards, #2457c5 accent, clean borders.
Run: D:\\ghcp\\venv\\Scripts\\python.exe make_slides_v2.py
Output: ghcp_analysis_deck_v2.pptx
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── SaaS-Pulse design tokens ──────────────────────────────────────────────────
BG      = RGBColor(0xF6, 0xF7, 0xF9)   # slide background  #f6f7f9
PANEL   = RGBColor(0xFF, 0xFF, 0xFF)   # card / panel      #ffffff
INK     = RGBColor(0x16, 0x20, 0x2C)   # primary text      #16202c
MUTED   = RGBColor(0x5B, 0x66, 0x75)   # secondary text    #5b6675
LINE    = RGBColor(0xDF, 0xE3, 0xE8)   # borders           #dfe3e8
ACCENT  = RGBColor(0x24, 0x57, 0xC5)   # blue accent       #2457c5
ACCENT2 = RGBColor(0x7A, 0x8C, 0xA6)   # softer blue-grey  #7a8ca6
OK      = RGBColor(0x16, 0x7A, 0x4A)   # green             #167a4a
WARN    = RGBColor(0xC9, 0x8A, 0x12)   # amber             #c98a12
BAD     = RGBColor(0xB3, 0x26, 0x1E)   # red               #b3261e

W = Inches(13.33)
H = Inches(7.5)

FIGURES = "D:\\ghcp\\data\\figures"


# ── helpers ───────────────────────────────────────────────────────────────────
def new_prs():
    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H
    return prs

def blank_slide(prs):
    return prs.slides.add_slide(prs.slide_layouts[6])

def fill_bg(slide, colour=BG):
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = colour

def rect(slide, l, t, w, h, fill, line_col=None, line_w=Pt(1)):
    shp = slide.shapes.add_shape(1, l, t, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    if line_col:
        shp.line.color.rgb = line_col
        shp.line.width = line_w
    else:
        shp.line.fill.background()
    return shp

def card(slide, l, t, w, h):
    """White rounded card with LINE border."""
    shp = slide.shapes.add_shape(
        5,   # rounded rectangle
        l, t, w, h
    )
    shp.fill.solid()
    shp.fill.fore_color.rgb = PANEL
    shp.line.color.rgb = LINE
    shp.line.width = Pt(0.75)
    # corner radius
    shp.adjustments[0] = 0.04
    return shp

def tb(slide, text, l, t, w, h,
       size=14, bold=False, colour=INK,
       align=PP_ALIGN.LEFT, italic=False):
    box = slide.shapes.add_textbox(l, t, w, h)
    tf  = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = "Inter"
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = colour
    return box

def tb_multi(slide, lines, l, t, w, h, size=14, gap=Pt(4)):
    """
    lines: list of (text, colour, bold)
    """
    box = slide.shapes.add_textbox(l, t, w, h)
    tf  = box.text_frame
    tf.word_wrap = True
    for i, (text, colour, bold) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = gap
        run = p.add_run()
        run.text = text
        run.font.name = "Inter"
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = colour

def hrule(slide, t, l=Inches(0.5), w=Inches(12.33), colour=LINE, thickness=Pt(0.75)):
    ln = slide.shapes.add_shape(1, l, t, w, Inches(0))
    ln.line.color.rgb = colour
    ln.line.width = thickness
    ln.fill.background()

def slide_header(slide, title, subtitle=None):
    """Standard slide header: title + divider."""
    tb(slide, title,
       Inches(0.55), Inches(0.3), Inches(11.5), Inches(0.75),
       size=28, bold=True, colour=INK)
    if subtitle:
        tb(slide, subtitle,
           Inches(0.55), Inches(0.98), Inches(11.5), Inches(0.4),
           size=14, colour=MUTED)
    hrule(slide, Inches(1.35) if subtitle else Inches(1.05),
          l=Inches(0.55), w=Inches(12.2))

def add_pic(slide, path, l, t, w, h=None):
    if not os.path.exists(path):
        return
    if h:
        slide.shapes.add_picture(path, l, t, w, h)
    else:
        slide.shapes.add_picture(path, l, t, w)

def slide_num(slide, n, total=5):
    tb(slide, f"{n} / {total}",
       Inches(12.5), Inches(7.15), Inches(0.75), Inches(0.25),
       size=10, colour=MUTED, align=PP_ALIGN.RIGHT)

def kpi_card(slide, l, t, w, h, number, label, num_colour=ACCENT):
    card(slide, l, t, w, h)
    tb(slide, number,
       l + Inches(0.15), t + Inches(0.12), w - Inches(0.3), Inches(0.6),
       size=26, bold=True, colour=num_colour, align=PP_ALIGN.CENTER)
    tb(slide, label,
       l + Inches(0.1), t + Inches(0.65), w - Inches(0.2), Inches(0.4),
       size=11, colour=MUTED, align=PP_ALIGN.CENTER)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1  —  Title / Dataset
# ══════════════════════════════════════════════════════════════════════════════
def slide1(prs):
    sl = blank_slide(prs)
    fill_bg(sl)

    # top accent bar (3px)
    rect(sl, Inches(0), Inches(0), W, Inches(0.055), ACCENT)

    # title area (white card centred)
    card(sl, Inches(0.55), Inches(0.4), Inches(12.23), Inches(2.5))

    tb(sl, "Analysing GitHub Copilot\nAgentic Sessions at Scale",
       Inches(0.8), Inches(0.52), Inches(11.7), Inches(1.5),
       size=36, bold=True, colour=INK)

    tb(sl, "Azure Public Dataset  ghcp-coding-agent-2026  ·  CC BY 4.0  ·  7 days, June 2026",
       Inches(0.8), Inches(1.98), Inches(11.0), Inches(0.4),
       size=14, colour=MUTED)

    # 6 KPI cards (2 rows × 3)
    kpis = [
        ("301,026",    "Sessions",           ACCENT),
        ("1.19 M",     "Turns",              INK),
        ("9.31 M",     "LLM Calls",          INK),
        ("8.68 M",     "Tool Calls",         INK),
        ("886 M",      "Prompt Segments",    INK),
        ("3.22 GB",    "Compressed Source",  MUTED),
    ]
    cw, ch = Inches(1.98), Inches(1.2)
    gap    = Inches(0.17)
    x0, y0 = Inches(0.55), Inches(3.1)
    for i, (num, label, col) in enumerate(kpis):
        cx = x0 + i * (cw + gap)
        kpi_card(sl, cx, y0, cw, ch, num, label, col)

    # pipeline constraint note
    card(sl, Inches(0.55), Inches(4.5), Inches(12.23), Inches(2.7))

    tb(sl, "Pipeline constraint",
       Inches(0.8), Inches(4.62), Inches(4), Inches(0.35),
       size=13, bold=True, colour=ACCENT)

    items = [
        ("1 GB RAM hard limit on consumer laptop — DuckDB memory_limit = 1,000 MB, 2 threads, spill to D:\\",  MUTED, False),
        ("606 shards ingested shard-by-shard with SQLite resumable checkpoint",                                  INK, False),
        ("Ingest: 50 min · Analysis: 476 s · 7 SQL files → 28 CSV outputs · Peak RSS 1,077 MB (never tripped)", INK, False),
        ("38 anonymised model IDs · no real model names · no cost figures",                                      MUTED, False),
    ]
    tb_multi(sl, items,
             Inches(0.8), Inches(5.0), Inches(11.7), Inches(2.0),
             size=13, gap=Pt(6))

    slide_num(sl, 1)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2  —  Architecture
# ══════════════════════════════════════════════════════════════════════════════
def slide2(prs):
    sl = blank_slide(prs)
    fill_bg(sl)
    rect(sl, Inches(0), Inches(0), W, Inches(0.055), ACCENT)

    slide_header(sl,
                 "System Architecture & Pipeline",
                 "Streaming, memory-bounded, fully resumable")

    # pipeline stage boxes
    stages = [
        ("Download",        "7 ZIPs\n3.22 GB",         True),
        ("Ingest",          "606 shards\n50 min",       False),
        ("Validate",        "Row counts\ndiag probes",  False),
        ("Analyse",         "8 SQL files\n476 s",       True),
        ("Benchmark",       "DuckDB vs\nPolars",        False),
        ("Report / Bundle", "7 PNGs · MD\n0.4 MB zip", True),
    ]
    bw, bh = Inches(1.85), Inches(1.5)
    gx = Inches(0.19)
    x0, y0 = Inches(0.55), Inches(1.5)

    for i, (title, body, highlight) in enumerate(stages):
        cx = x0 + i * (bw + gx)
        if highlight:
            # highlighted: accent fill
            shp = slide.shapes.add_shape(5, cx, y0, bw, bh) if False else \
                  sl.shapes.add_shape(5, cx, y0, bw, bh)
            shp.fill.solid()
            shp.fill.fore_color.rgb = ACCENT
            shp.line.fill.background()
            shp.adjustments[0] = 0.04
            tc = PANEL
            lc = PANEL
        else:
            shp = sl.shapes.add_shape(5, cx, y0, bw, bh)
            shp.fill.solid()
            shp.fill.fore_color.rgb = PANEL
            shp.line.color.rgb = LINE
            shp.line.width = Pt(0.75)
            shp.adjustments[0] = 0.04
            tc = INK
            lc = MUTED

        tb(sl, title, cx + Inches(0.1), y0 + Inches(0.1),
           bw - Inches(0.2), Inches(0.45),
           size=13, bold=True, colour=tc, align=PP_ALIGN.CENTER)
        tb(sl, body,  cx + Inches(0.1), y0 + Inches(0.55),
           bw - Inches(0.2), Inches(0.85),
           size=11, colour=lc, align=PP_ALIGN.CENTER)

        if i < len(stages) - 1:
            ax = cx + bw + Inches(0.04)
            tb(sl, "→", ax, y0 + Inches(0.6), Inches(0.15), Inches(0.35),
               size=14, colour=MUTED, align=PP_ALIGN.CENTER)

    # two columns of info below
    # left: design decisions
    card(sl, Inches(0.55), Inches(3.2), Inches(5.9), Inches(3.95))
    tb(sl, "Key Design Decisions",
       Inches(0.75), Inches(3.32), Inches(5.5), Inches(0.35),
       size=13, bold=True, colour=ACCENT)
    tb_multi(sl, [
        ("· DuckDB memory_limit = 1,000 MB · threads = 2 · never raised", INK, False),
        ("· Spill to D:\\ — C:\\ untouched for data or venv",              INK, False),
        ("· SQLite checkpoint: each shard recorded before next fetch",     INK, False),
        ("· No Pandas/Polars eager frames in the main pipeline",           INK, False),
        ("· All anomalies kept — negatives, duplicates counted & reported",MUTED, False),
    ], Inches(0.75), Inches(3.72), Inches(5.6), Inches(2.4), size=13, gap=Pt(7))

    # right: resource table
    card(sl, Inches(6.65), Inches(3.2), Inches(6.1), Inches(3.95))
    tb(sl, "Resource Usage by Stage",
       Inches(6.85), Inches(3.32), Inches(5.7), Inches(0.35),
       size=13, bold=True, colour=ACCENT)

    headers = ["Stage", "Wall time", "Peak RSS", "Guard"]
    rows = [
        ("Ingest",      "3,027 s (~50 min)", "1,077 MB", "✓ clear"),
        ("Analysis",    "476 s",             "1,176 MB", "✓ clear"),
        ("Benchmark",   "~30 s",             "< 250 MB", "✓ clear"),
        ("Plots+Report","< 60 s",            "—",        "✓ clear"),
    ]
    cws = [Inches(1.4), Inches(1.65), Inches(1.3), Inches(1.2)]
    ty = Inches(3.75)
    for r, row in enumerate([headers] + rows):
        is_hdr = r == 0
        for c, cell in enumerate(row):
            cx2 = Inches(6.75) + sum(cws[:c])
            bg_c = ACCENT if is_hdr else (PANEL if r % 2 == 1 else BG)
            rect(sl, cx2, ty + r * Inches(0.44), cws[c], Inches(0.44), bg_c)
            col = PANEL if is_hdr else (OK if "✓" in cell else MUTED)
            tb(sl, cell, cx2 + Inches(0.06), ty + r * Inches(0.44) + Inches(0.06),
               cws[c] - Inches(0.07), Inches(0.33),
               size=12, bold=is_hdr, colour=col)

    slide_num(sl, 2)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3  —  Cache & Prompt Composition
# ══════════════════════════════════════════════════════════════════════════════
def slide3(prs):
    sl = blank_slide(prs)
    fill_bg(sl)
    rect(sl, Inches(0), Inches(0), W, Inches(0.055), ACCENT)

    slide_header(sl,
                 "Finding 1: Cache Efficiency & Prompt Composition",
                 "85.7% of prompt tokens are cached (token-weighted, corpus-wide)")

    # ---- LEFT half ----
    # big headline card
    card(sl, Inches(0.55), Inches(1.5), Inches(3.5), Inches(1.6))
    tb(sl, "85.7%",
       Inches(0.55), Inches(1.6), Inches(3.5), Inches(0.9),
       size=52, bold=True, colour=ACCENT, align=PP_ALIGN.CENTER)
    tb(sl, "prompt tokens cached\n(token-weighted)",
       Inches(0.55), Inches(2.42), Inches(3.5), Inches(0.6),
       size=12, colour=MUTED, align=PP_ALIGN.CENTER)

    # cache ramp card
    card(sl, Inches(0.55), Inches(3.25), Inches(3.5), Inches(2.1))
    tb(sl, "Cache ramp-up within a turn",
       Inches(0.75), Inches(3.37), Inches(3.1), Inches(0.3),
       size=12, bold=True, colour=ACCENT)
    ramp = [
        ("Call 1   →   46.2%  (cold prefix)", MUTED, False),
        ("Call 2   →   85.1%  (prefix warms)", INK, False),
        ("Call 3   →   90.9%",                 INK, False),
        ("Call 4+  →   ~92%  (plateau)",       OK, True),
        ("6.2% of calls: zero cache hit",      BAD, False),
    ]
    tb_multi(sl, ramp, Inches(0.75), Inches(3.72), Inches(3.1), Inches(1.5),
             size=13, gap=Pt(6))

    # coverage note
    tb(sl, "93.9% of prompt tokens covered by tracked segments",
       Inches(0.55), Inches(5.5), Inches(3.5), Inches(0.4),
       size=11, colour=MUTED, italic=True)

    # ---- MIDDLE: stacked bar  ----
    segments = [
        ("Tool history\n(calls + fn logs)", 48.3, ACCENT),
        ("Conversation history\n(user + asst.)", 31.3, RGBColor(0x24, 0x9C, 0x7F)),
        ("System / instructions", 12.9, WARN),
        ("Other tracked", 1.4, ACCENT2),
        ("Untracked", 6.1, LINE),
    ]
    bx, by = Inches(4.3), Inches(1.5)
    bw2, bh2 = Inches(1.5), Inches(5.6)
    cur = by
    tb(sl, "Prompt segment\nbreakdown (% tokens)",
       bx, by - Inches(0.5), bw2 + Inches(0.1), Inches(0.45),
       size=11, colour=MUTED, align=PP_ALIGN.CENTER)
    for label, pct, col in segments:
        seg_h = bh2 * (pct / 100.0)
        rect(sl, bx, cur, bw2, seg_h, col)
        # label to right
        tb(sl, f"{pct:.1f}%",
           bx + bw2 + Inches(0.1), cur + seg_h * 0.1,
           Inches(0.6), max(seg_h * 0.8, Inches(0.3)),
           size=12, bold=True, colour=col if col != LINE else MUTED)
        tb(sl, label,
           bx + bw2 + Inches(0.75), cur + seg_h * 0.1,
           Inches(1.8), max(seg_h, Inches(0.3)),
           size=11, colour=INK)
        cur += seg_h

    # ---- RIGHT: figure ----
    fig = os.path.join(FIGURES, "cache_by_call_position.png")
    add_pic(sl, fig, Inches(7.5), Inches(1.5), Inches(5.5), Inches(5.6))

    slide_num(sl, 3)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4  —  Time & Concentration
# ══════════════════════════════════════════════════════════════════════════════
def slide4(prs):
    sl = blank_slide(prs)
    fill_bg(sl)
    rect(sl, Inches(0), Inches(0), W, Inches(0.055), ACCENT)

    slide_header(sl,
                 "Finding 2: Time Decomposition & Usage Concentration",
                 "Tool execution and LLM inference consume equal shares of turn wall-clock")

    # ---- LEFT: time bars ----
    card(sl, Inches(0.55), Inches(1.5), Inches(5.9), Inches(4.6))

    tb(sl, "Share of turn wall-clock span",
       Inches(0.75), Inches(1.62), Inches(5.5), Inches(0.3),
       size=12, bold=True, colour=ACCENT)
    tb(sl, "excl. far out-of-window, 1.19 M turns",
       Inches(0.75), Inches(1.9), Inches(5.5), Inches(0.25),
       size=11, colour=MUTED)

    bars = [
        ("LLM inference",  40.8, ACCENT),
        ("Tool execution", 44.1, WARN),
        ("Residual/comm.", 15.1, ACCENT2),
    ]
    bx, by = Inches(0.75), Inches(2.25)
    bw3, bh3 = Inches(4.4), Inches(0.55)
    for i, (label, pct, col) in enumerate(bars):
        ty2 = by + i * (bh3 + Inches(0.18))
        rect(sl, bx, ty2, bw3 * (pct / 100.0), bh3, col)
        rect(sl, bx + bw3 * (pct / 100.0), ty2,
             bw3 * (1 - pct / 100.0), bh3, LINE)
        tb(sl, f"{pct}%  {label}",
           bx, ty2 + Inches(0.14), bw3 + Inches(0.5), bh3 - Inches(0.1),
           size=13, colour=INK)

    tb_multi(sl, [
        ("Turn span   p50 = 49.8 s  ·  p90 = 337.8 s",        INK, False),
        ("Idle gap    p50 = 152 s (2.5 min)  ·  p90 = 30 min", WARN, True),
        ("73% of idle gaps > 1 min  —  human think-time",       MUTED, False),
        ("dominates session wall-clock",                          MUTED, False),
    ], Inches(0.75), Inches(3.9), Inches(5.5), Inches(2.0), size=13, gap=Pt(7))

    # ---- RIGHT: concentration + tool table ----
    # Gini card
    card(sl, Inches(6.65), Inches(1.5), Inches(6.1), Inches(2.7))
    tb(sl, "Usage Concentration  —  Lorenz / Gini",
       Inches(6.85), Inches(1.62), Inches(5.7), Inches(0.3),
       size=12, bold=True, colour=ACCENT)

    conc = [
        ("Prompt-token Gini",     "0.802",                    ACCENT,  True),
        ("Cached-token Gini",     "0.818",                    ACCENT,  True),
        ("",                      "",                          INK,     False),
        ("Top 10% sessions",      "68.8% of cached tokens",  OK,      False),
        ("Top 10% sessions",      "57.0% of completions",    OK,      False),
        ("Top  1% sessions",      "21.6% of cached tokens",  WARN,    False),
    ]
    ty3 = Inches(1.98)
    for label, val, col, bold in conc:
        if not label:
            ty3 += Inches(0.1)
            continue
        tb(sl, label, Inches(6.85), ty3, Inches(2.9), Inches(0.33),
           size=12, colour=MUTED)
        tb(sl, val,   Inches(9.8),  ty3, Inches(2.7), Inches(0.33),
           size=12, bold=bold, colour=col)
        ty3 += Inches(0.37)

    # tool reliability
    card(sl, Inches(6.65), Inches(4.35), Inches(6.1), Inches(1.8))
    tb(sl, "Tool Reliability",
       Inches(6.85), Inches(4.47), Inches(5.7), Inches(0.3),
       size=12, bold=True, colour=ACCENT)

    t_rows = [
        ("Tool",         "Calls",   "Fail %",   "p50 latency"),
        ("get_file",     "3.08 M",  "2.4%",     "—"),
        ("run_command",  "1.39 M",  "11.4%",    "430 ms"),
        ("run_build",    "0.42 M",  "21.6% ⚠",  "5,053 ms"),
    ]
    cws2 = [Inches(1.6), Inches(1.1), Inches(1.1), Inches(1.9)]
    ty4 = Inches(4.85)
    for r, row in enumerate(t_rows):
        is_hdr = r == 0
        for c, cell in enumerate(row):
            cx2 = Inches(6.75) + sum(cws2[:c])
            bg_c = ACCENT if is_hdr else (PANEL if r % 2 == 1 else BG)
            rect(sl, cx2, ty4 + r * Inches(0.38), cws2[c], Inches(0.38), bg_c)
            col = PANEL if is_hdr else (BAD if "⚠" in cell else MUTED)
            tb(sl, cell, cx2 + Inches(0.05), ty4 + r * Inches(0.38) + Inches(0.04),
               cws2[c] - Inches(0.06), Inches(0.3),
               size=11, bold=is_hdr, colour=col)

    # lorenz figure (small, bottom-right)
    add_pic(sl, os.path.join(FIGURES, "lorenz.png"),
            Inches(6.65), Inches(1.52), Inches(0.0) + Inches(2.6), h=Inches(2.68))

    slide_num(sl, 4)


# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5  —  Benchmark & Conclusions
# ══════════════════════════════════════════════════════════════════════════════
def slide5(prs):
    sl = blank_slide(prs)
    fill_bg(sl)
    rect(sl, Inches(0), Inches(0), W, Inches(0.055), ACCENT)

    slide_header(sl,
                 "DuckDB vs Polars Benchmark · Conclusions",
                 "Identical results (all checksums match) — the choice is RSS vs wall time")

    # benchmark table
    card(sl, Inches(0.55), Inches(1.5), Inches(7.4), Inches(4.0))
    tb(sl, "Query benchmark  (3 queries × 2 engines, 7-day corpus)",
       Inches(0.75), Inches(1.62), Inches(7.0), Inches(0.3),
       size=12, bold=True, colour=ACCENT)

    headers = ["Query", "Engine", "Wall time", "Peak RSS", "Verdict"]
    rows = [
        ("7-day aggregation",  "DuckDB",  "5.67 s",  "123.5 MB", "low RAM  ✓"),
        ("7-day aggregation",  "Polars",  "1.99 s",  "236.2 MB", "faster"),
        ("Group-by: session",  "DuckDB",  "2.14 s",   "98.3 MB", "low RAM  ✓"),
        ("Group-by: session",  "Polars",  "0.87 s",  "212.4 MB", "faster"),
        ("Group-by: model",    "DuckDB",  "1.03 s",   "89.1 MB", "low RAM  ✓"),
        ("Group-by: model",    "Polars",  "0.44 s",  "178.6 MB", "faster"),
    ]
    cws3 = [Inches(2.1), Inches(1.1), Inches(1.1), Inches(1.1), Inches(1.6)]
    ty5 = Inches(2.0)
    for r, row in enumerate([headers] + rows):
        is_hdr = r == 0
        for c, cell in enumerate(row):
            cx2 = Inches(0.65) + sum(cws3[:c])
            bg_c = ACCENT if is_hdr else (PANEL if r % 2 == 1 else BG)
            rect(sl, cx2, ty5 + r * Inches(0.42), cws3[c], Inches(0.42), bg_c)
            col = PANEL if is_hdr else \
                  (OK if "✓" in cell else (ACCENT if cell == "faster" else MUTED))
            tb(sl, cell, cx2 + Inches(0.06), ty5 + r * Inches(0.42) + Inches(0.06),
               cws3[c] - Inches(0.07), Inches(0.33),
               size=12, bold=is_hdr, colour=col)

    tb(sl, "All checksums identical — DuckDB and Polars produce the same results on every query.",
       Inches(0.75), Inches(5.6), Inches(7.0), Inches(0.35),
       size=12, colour=OK, italic=True)

    # conclusions (right column)
    card(sl, Inches(8.15), Inches(1.5), Inches(5.0), Inches(5.65))
    tb(sl, "Key Takeaways",
       Inches(8.35), Inches(1.62), Inches(4.6), Inches(0.3),
       size=13, bold=True, colour=ACCENT)

    conclusions = [
        ("Cache dominates prompt cost",  "85.7% cached; first call cold, all subsequent hot",         ACCENT),
        ("Tool time ≈ LLM time",         "44% tool execution vs 41% LLM — truly agentic",             WARN),
        ("Heavy usage skew",             "Gini ~0.80; top 10% → 69% of cached tokens",               INK),
        ("Idle time dominates wall-clock","p50 2.5 min gap; p90 30 min — human pace sets the clock",  INK),
        ("DuckDB wins on memory",        "2× lower RSS vs Polars — viable at 1 GB constraint",        OK),
        ("run_build most fragile",       "21.6% fail rate — highest-impact reliability gap",          BAD),
    ]
    ty6 = Inches(2.05)
    for title, detail, col in conclusions:
        tb(sl, f"● {title}",
           Inches(8.35), ty6, Inches(4.6), Inches(0.28),
           size=12, bold=True, colour=col)
        tb(sl, detail,
           Inches(8.35), ty6 + Inches(0.28), Inches(4.6), Inches(0.33),
           size=11, colour=MUTED)
        ty6 += Inches(0.72)

    slide_num(sl, 5)


# ══════════════════════════════════════════════════════════════════════════════
def main():
    prs = new_prs()
    slide1(prs)
    slide2(prs)
    slide3(prs)
    slide4(prs)
    slide5(prs)
    out = "ghcp_analysis_deck_v2.pptx"
    prs.save(out)
    sz = os.path.getsize(out)
    print(f"Saved -> {out}  ({sz // 1024} KB)")

if __name__ == "__main__":
    main()
