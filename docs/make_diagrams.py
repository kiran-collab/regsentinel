#!/usr/bin/env python3
"""Generate RegSentinel's publication-quality architecture diagrams as SVG.

Hand-tuned, vector, flat design (no filters — survives GitHub's SVG sanitizer).
Run:  python docs/make_diagrams.py   -> writes docs/architecture.svg, docs/eval_pipeline.svg
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Design tokens
# --------------------------------------------------------------------------- #
INK = "#16202e"
SUB = "#5b6678"
RULE = "#dbe2ec"
PANEL_F = "#f7f9fc"
PANEL_S = "#e4eaf3"
PANEL_L = "#94a0b3"
WHITE = "#ffffff"

ORCH_S, ORCH_F = "#4338ca", "#eef0fd"
AG_S, AG_F = "#0f766e", "#e7f4f1"
MCP_S, MCP_F = "#b45309", "#fdf4e7"
GOV_S, GOV_F = "#be123c", "#fdeef1"
EXT_S, EXT_F = "#46556b", "#eef2f7"
OUT_S, OUT_F = "#15803d", "#ecf6ef"

SANS = "Helvetica, 'Helvetica Neue', Arial, sans-serif"
MONO = "'SF Mono', 'Menlo', 'DejaVu Sans Mono', monospace"


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class SVG:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.el: list[str] = []

    def add(self, s: str):
        self.el.append(s)

    def rect(self, x, y, w, h, fill, stroke=None, sw=1.4, rx=10, dash=None, opacity=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        op = f' opacity="{opacity}"' if opacity is not None else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
                 f'fill="{fill}"{st}{d}{op}/>')

    def line(self, x1, y1, x2, y2, stroke, sw=1.4, dash=None, marker=True, cap="round"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#arrow)"' if marker else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linecap="{cap}"{d}{m}/>')

    def path(self, d, stroke, sw=1.4, dash=None, marker=True, fill="none"):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        m = ' marker-end="url(#arrow)"' if marker else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
                 f'stroke-linecap="round" stroke-linejoin="round"{da}{m}/>')

    def text(self, x, y, s, size=13, fill=INK, weight="400", anchor="start",
             family=SANS, spacing=None, italic=False):
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        it = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
                 f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{ls}{it}>'
                 f'{esc(s)}</text>')

    def circle(self, cx, cy, r, fill, stroke=None, sw=1.4):
        st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"{st}/>')

    def panel(self, x, y, w, h, label, accent):
        self.rect(x, y, w, h, PANEL_F, PANEL_S, sw=1.3, rx=14)
        # accent tab on the label
        self.circle(x + 16, y + 18, 3.2, accent)
        self.text(x + 26, y + 22, label, size=11, fill=PANEL_L, weight="700",
                  spacing="1.4")

    def render(self) -> str:
        defs = (
            '<defs>'
            '<marker id="arrow" markerWidth="9" markerHeight="9" refX="7.2" refY="3.4" '
            'orient="auto" markerUnits="userSpaceOnUse">'
            f'<path d="M0,0 L7.6,3.4 L0,6.8 Z" fill="{INK}"/></marker>'
            '<marker id="arrowG" markerWidth="9" markerHeight="9" refX="7.2" refY="3.4" '
            'orient="auto" markerUnits="userSpaceOnUse">'
            f'<path d="M0,0 L7.6,3.4 L0,6.8 Z" fill="{GOV_S}"/></marker>'
            '</defs>'
        )
        body = "\n".join(self.el)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}" '
                f'font-family="{SANS}">\n'
                f'<rect width="{self.w}" height="{self.h}" fill="{WHITE}"/>\n'
                f'{defs}\n{body}\n</svg>\n')


def shield(svg: SVG, cx, cy, scale, fill, stroke):
    """Small shield glyph for the egress guard."""
    s = scale
    d = (f"M{cx},{cy-7*s} L{cx+6*s},{cy-4*s} L{cx+6*s},{cy+2*s} "
         f"Q{cx+6*s},{cy+7*s} {cx},{cy+9*s} "
         f"Q{cx-6*s},{cy+7*s} {cx-6*s},{cy+2*s} L{cx-6*s},{cy-4*s} Z")
    svg.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="1.3"/>')


# --------------------------------------------------------------------------- #
# Architecture diagram
# --------------------------------------------------------------------------- #
def build_architecture() -> str:
    W, H = 1500, 1010
    s = SVG(W, H)

    # ---- header ----
    s.text(48, 56, "RegSentinel", size=30, weight="700")
    s.text(232, 56, "· System Architecture", size=21, weight="400", fill=SUB)
    s.text(48, 84,
           "Orchestrator-led multi-agent regulatory compliance audit — least-"
           "privilege subagents, a deterministic in-process MCP core, and a "
           "model-independent governance layer.",
           size=13.5, fill=SUB)
    s.line(48, 100, W - 48, 100, RULE, sw=1.2, marker=False)

    # ---- external sources (left) ----
    ext_x, ext_y, ext_w, ext_h = 48, 130, 256, 150
    s.panel(ext_x, ext_y, ext_w, ext_h, "EXTERNAL SOURCES", EXT_S)
    s.rect(ext_x + 16, ext_y + 40, ext_w - 32, ext_h - 56, WHITE, EXT_S, sw=1.4, rx=9)
    s.text(ext_x + 28, ext_y + 64, "Authoritative regulators", size=12.5, weight="700",
           fill=EXT_S)
    for i, dom in enumerate(["eur-lex.europa.eu   ·   gdpr.eu",
                             "csrc.nist.gov   ·   www.iso.org",
                             "federalregister.gov   ·   aicpa.org"]):
        s.text(ext_x + 28, ext_y + 86 + i * 18, dom, size=10.5, fill=SUB, family=MONO)

    # ---- inputs (left, below external) ----
    in_x, in_y, in_w, in_h = 48, 300, 256, 150
    s.panel(in_x, in_y, in_w, in_h, "INPUTS", EXT_S)
    s.rect(in_x + 16, in_y + 40, in_w - 32, 40, WHITE, EXT_S, sw=1.4, rx=9)
    s.text(in_x + 28, in_y + 58, "regulations", size=12, weight="700", fill=INK, family=MONO)
    s.text(in_x + 28, in_y + 73, '"EU AI Act Art 9; GDPR Art 30"', size=9.5, fill=SUB)
    s.rect(in_x + 16, in_y + 90, in_w - 32, 40, WHITE, EXT_S, sw=1.4, rx=9)
    s.text(in_x + 28, in_y + 108, "controls_inventory.md", size=12, weight="700",
           fill=INK, family=MONO)
    s.text(in_x + 28, in_y + 123, "organization's internal controls", size=9.5, fill=SUB)

    # ---- orchestrator (control plane) ----
    orch_x, orch_y, orch_w, orch_h = 360, 138, 740, 96
    s.text(orch_x, orch_y - 8, "CONTROL PLANE", size=11, fill=PANEL_L, weight="700",
           spacing="1.4")
    s.rect(orch_x, orch_y, orch_w, orch_h, ORCH_F, ORCH_S, sw=1.8, rx=12)
    s.circle(orch_x + 30, orch_y + 34, 13, ORCH_S)
    s.text(orch_x + 30, orch_y + 39, "Σ", size=16, fill=WHITE, weight="700", anchor="middle")
    s.text(orch_x + 54, orch_y + 33, "Orchestrator", size=18, weight="700", fill=ORCH_S)
    s.text(orch_x + 54, orch_y + 53,
           "decomposes the audit into phases · delegates each to a specialist via the "
           "Agent tool · never analyzes directly", size=11.5, fill=SUB)
    s.rect(orch_x + 54, orch_y + 64, 560, 22, "#e3e6fb", rx=6)
    s.text(orch_x + 64, orch_y + 79,
           "tools:  Agent  ·  Read/Glob/Grep  ·  Write  ·  WebSearch/WebFetch  ·  "
           "compliance.*", size=10.5, fill=ORCH_S, family=MONO)

    # invocation arrow: inputs -> orchestrator
    s.path(f"M{in_x + in_w},{in_y + 20} C340,{in_y + 20} 330,{orch_y + 48} "
           f"{orch_x},{orch_y + 58}", INK, sw=1.5)
    s.text(316, orch_y + 104, "audit request", size=10, fill=SUB, italic=True, anchor="middle")

    # ---- specialist subagents panel ----
    ag_px, ag_py, ag_pw, ag_ph = 318, 296, 824, 214
    s.panel(ag_px, ag_py, ag_pw, ag_ph, "SPECIALIST SUBAGENTS — LEAST PRIVILEGE", AG_S)

    agents = [
        ("regulation", "researcher", "fetch CURRENT verbatim", "regulatory text",
         ["WebSearch", "WebFetch"]),
        ("obligation", "extractor", "split text into atomic", "obligations",
         ["extract_obligations"]),
        ("control", "mapper", "map obligations to", "internal controls",
         ["Read/Glob/Grep", "map_control"]),
        ("risk", "assessor", "score every gap via", "the fixed matrix",
         ["score_risk"]),
        ("report", "writer", "compile the final", "Markdown report",
         ["Read · Write", "verify_citation"]),
    ]
    n = len(agents)
    pad = 18
    gap = 16
    inner = ag_pw - 2 * pad - (n - 1) * gap
    cw = inner / n
    ch = 150
    cy = ag_py + 44
    card_cx = []
    for i, (n1, n2, r1, r2, tools) in enumerate(agents):
        cx = ag_px + pad + i * (cw + gap)
        card_cx.append(cx + cw / 2)
        s.rect(cx, cy, cw, ch, WHITE, AG_S, sw=1.5, rx=10)
        # phase badge
        s.circle(cx + 17, cy + 17, 11, AG_S)
        s.text(cx + 17, cy + 21.5, str(i + 1), size=12, fill=WHITE, weight="700",
               anchor="middle")
        # name (two lines)
        s.text(cx + cw / 2, cy + 50, n1, size=13.5, weight="700", fill=INK, anchor="middle")
        s.text(cx + cw / 2, cy + 67, n2, size=13.5, weight="700", fill=INK, anchor="middle")
        # role
        s.text(cx + cw / 2, cy + 88, r1, size=10, fill=SUB, anchor="middle")
        s.text(cx + cw / 2, cy + 101, r2, size=10, fill=SUB, anchor="middle")
        # tools chip(s)
        ty = cy + 116
        for t in tools:
            s.rect(cx + 10, ty, cw - 20, 17, AG_F, rx=5)
            s.text(cx + cw / 2, ty + 12.5, t, size=9.3, fill=AG_S, anchor="middle",
                   family=MONO)
            ty += 20

    # fan-out arrows: orchestrator -> each agent (phase order)
    ob = orch_y + orch_h  # orchestrator bottom
    ocx = orch_x + orch_w / 2
    for i, cx in enumerate(card_cx):
        s.path(f"M{ocx},{ob} C{ocx},{ob + 26} {cx},{cy - 30} {cx},{cy}",
               ORCH_S, sw=1.4)
    s.rect(ocx - 110, ob + 6, 220, 22, WHITE, ORCH_S, sw=1.1, rx=11)
    s.text(ocx, ob + 21, "delegate in phase order  1 → 5", size=10.5, fill=ORCH_S,
           anchor="middle", weight="700")

    # controls_inventory.md -> control-mapper, routed through the clean corridor
    # between the agent panel and the MCP panel (avoids cutting across cards).
    corridor_y = ag_py + ag_ph + 25  # midway to the MCP panel below
    mapper_left = card_cx[2] - cw / 2
    s.path(f"M{in_x + in_w},{in_y + 105} C{in_x + in_w + 26},{in_y + 105} "
           f"330,{corridor_y} 362,{corridor_y} L{mapper_left - 26},{corridor_y} "
           f"C{mapper_left - 8},{corridor_y} {mapper_left},{cy + 96} "
           f"{mapper_left},{cy + 78}", EXT_S, sw=1.3, dash="5 4")
    s.text(372, corridor_y - 8, "controls inventory", size=9.5, fill=SUB, italic=True)

    # researcher -> external sources (egress-guarded)
    res_cx = card_cx[0]
    s.path(f"M{res_cx - cw/2},{cy + 40} C{ag_px - 24},{cy + 40} "
           f"{ext_x + ext_w + 30},{ext_y + ext_h} {ext_x + ext_w/2},{ext_y + ext_h}",
           GOV_S, sw=1.5, dash="6 4", marker=True)
    # shield on that path
    shield(s, ext_x + ext_w/2 + 70, ext_y + ext_h + 26, 1.25, GOV_F, GOV_S)
    s.text(ext_x + ext_w/2 + 70, ext_y + ext_h + 52, "egress", size=8.5, fill=GOV_S,
           anchor="middle", weight="700")
    s.text(ext_x + ext_w/2 + 70, ext_y + ext_h + 62, "guard", size=8.5, fill=GOV_S,
           anchor="middle", weight="700")

    # ---- deterministic core (MCP) ----
    mcp_px, mcp_py, mcp_pw, mcp_ph = 318, 560, 824, 150
    s.panel(mcp_px, mcp_py, mcp_pw, mcp_ph,
            "DETERMINISTIC CORE — IN-PROCESS MCP SERVER  “compliance”", MCP_S)
    # Tools are ORDERED to sit directly beneath the agent that calls them
    # (agents 2..5), so every connector is a clean vertical with no crossings.
    tools = [
        ("extract_obligations", "clause split +", "sha-256 fingerprint"),
        ("map_control", "coverage →", "gap derivation"),
        ("score_risk", "fixed likelihood ×", "impact matrix"),
        ("verify_citation", "snippet ⊆ source", "(normalized)"),
    ]
    th = 72
    tty = mcp_py + 50
    tw = 152
    tool_cx = []
    for i, (name, d1, d2) in enumerate(tools):
        cxc = card_cx[i + 1]
        tool_cx.append(cxc)
        tx = cxc - tw / 2
        s.rect(tx, tty, tw, th, MCP_F, MCP_S, sw=1.5, rx=9)
        s.text(cxc, tty + 26, name, size=12.5, weight="700", fill=MCP_S,
               anchor="middle", family=MONO)
        s.text(cxc, tty + 45, d1, size=10, fill=SUB, anchor="middle")
        s.text(cxc, tty + 59, d2, size=10, fill=SUB, anchor="middle")

    # the researcher calls no deterministic tool — annotate its empty column
    rc = card_cx[0]
    s.rect(rc - tw / 2, tty, tw, th, WHITE, PANEL_L, sw=1.2, rx=9, dash="4 4")
    s.text(rc, tty + 31, "web research only", size=10.5, fill=PANEL_L,
           anchor="middle", italic=True)
    s.text(rc, tty + 48, "(no deterministic tool)", size=9.5, fill=PANEL_L,
           anchor="middle", italic=True)

    # agent -> tool connectors (vertical: agent i+1 -> tool i)
    for i in range(4):
        ax = card_cx[i + 1]
        s.path(f"M{ax},{cy + ch} C{ax},{cy + ch + 22} {ax},{tty - 22} {ax},{tty}",
               MCP_S, sw=1.3)

    # ---- governance hooks (right, tall) ----
    g_x, g_y, g_w, g_h = 1162, 130, 290, 580
    s.panel(g_x, g_y, g_w, g_h, "GOVERNANCE HOOKS", GOV_S)
    s.text(g_x + 26, g_y + 38, "deterministic · model-independent", size=10.5,
           fill=SUB, italic=True)

    # PreToolUse: egress guard
    eg_y = g_y + 56
    s.rect(g_x + 18, eg_y, g_w - 36, 132, GOV_F, GOV_S, sw=1.6, rx=10)
    shield(s, g_x + 42, eg_y + 34, 1.5, WHITE, GOV_S)
    s.text(g_x + 64, eg_y + 28, "PreToolUse", size=10, fill=GOV_S, weight="700",
           family=MONO)
    s.text(g_x + 64, eg_y + 46, "Egress Guard", size=15, weight="700", fill=INK)
    s.text(g_x + 30, eg_y + 74, "Intercepts every WebFetch.", size=11, fill=SUB)
    s.text(g_x + 30, eg_y + 92, "Host ∈ regulator allowlist?", size=11, fill=SUB)
    s.rect(g_x + 30, eg_y + 102, 80, 20, "#e8f6ee", rx=5)
    s.text(g_x + 70, eg_y + 116, "ALLOW", size=10, fill=OUT_S, weight="700", anchor="middle")
    s.text(g_x + 118, eg_y + 116, "else", size=10, fill=SUB)
    s.rect(g_x + 150, eg_y + 102, 70, 20, "#fbe2e8", rx=5)
    s.text(g_x + 185, eg_y + 116, "DENY", size=10, fill=GOV_S, weight="700", anchor="middle")

    # PostToolUse: audit logger
    au_y = eg_y + 156
    s.rect(g_x + 18, au_y, g_w - 36, 124, GOV_F, GOV_S, sw=1.6, rx=10)
    s.circle(g_x + 42, au_y + 34, 11, GOV_S)
    s.text(g_x + 42, au_y + 38.5, "✓", size=12, fill=WHITE, anchor="middle", weight="700")
    s.text(g_x + 64, au_y + 28, "PostToolUse", size=10, fill=GOV_S, weight="700",
           family=MONO)
    s.text(g_x + 64, au_y + 46, "Audit Logger", size=15, weight="700", fill=INK)
    s.text(g_x + 30, au_y + 74, "Appends a structured record", size=11, fill=SUB)
    s.text(g_x + 30, au_y + 92, "of EVERY tool call to a", size=11, fill=SUB)
    s.text(g_x + 30, au_y + 110, "tamper-evident trail.", size=11, fill=SUB)

    # bracket: hooks wrap the whole agent + tool region
    bx = g_x - 14
    s.path(f"M{ag_px + ag_pw + 6},{ag_py + 18} L{bx},{ag_py + 18} "
           f"L{bx},{au_y + 62} L{g_x + 18},{au_y + 62}", GOV_S, sw=1.3, dash="4 4",
           marker=True)
    s.text(bx - 6, ag_py + 8, "every tool call", size=9.5, fill=GOV_S, anchor="end",
           italic=True)

    # ---- outputs ----
    o_px, o_py, o_pw, o_ph = 318, 762, 1134, 116
    s.panel(o_px, o_py, o_pw, o_ph, "OUTPUTS — AUDITABLE ARTIFACTS", OUT_S)
    # report (the deliverable) — centered
    r_x, r_w = 705, 360
    s.rect(r_x, o_py + 42, r_w, 56, OUT_F, OUT_S, sw=1.6, rx=9)
    s.text(r_x + 20, o_py + 69, "compliance_report.md", size=13.5, weight="700",
           fill=OUT_S, family=MONO)
    s.text(r_x + 20, o_py + 88,
           "exec summary · risk register · coverage · citation appendix", size=9.8,
           fill=SUB)
    # audit log — under the governance column
    a_x, a_w = 1142, 300
    s.rect(a_x, o_py + 42, a_w, 56, "#eef2f7", EXT_S, sw=1.6, rx=9)
    s.text(a_x + 20, o_py + 69, "audit_trail.jsonl", size=13.5, weight="700",
           fill=EXT_S, family=MONO)
    s.text(a_x + 20, o_py + 88, "one record per tool invocation",
           size=9.8, fill=SUB)

    # verify_citation -> report (writer's verified findings become the report)
    vc_cx = tool_cx[3]
    rep_cx = r_x + r_w / 2
    s.path(f"M{vc_cx},{tty + th} C{vc_cx},{tty + th + 64} {rep_cx},{o_py - 12} "
           f"{rep_cx},{o_py + 42}", OUT_S, sw=1.5)
    s.text(rep_cx + 96, o_py + 6, "verified findings", size=9.5, fill=OUT_S,
           italic=True, anchor="middle")
    # audit logger -> audit trail
    au_cx = g_x + g_w / 2
    s.path(f"M{au_cx},{au_y + 124} C{au_cx},{o_py - 40} {a_x + a_w/2},{o_py - 20} "
           f"{a_x + a_w/2},{o_py + 42}", EXT_S, sw=1.4, dash="5 4")

    # ---- legend ----
    ly = H - 38
    s.line(48, ly - 18, W - 48, ly - 18, RULE, sw=1.1, marker=False)
    items = [
        (ORCH_S, "control flow / delegation", False),
        (MCP_S, "deterministic tool call", False),
        (GOV_S, "governance interception", True),
        (EXT_S, "data / artifact flow", True),
    ]
    lx = 48
    for color, label, dash in items:
        s.line(lx, ly, lx + 30, ly, color, sw=2.0, dash="5 4" if dash else None, marker=True)
        s.text(lx + 38, ly + 4, label, size=11, fill=SUB)
        lx += 38 + len(label) * 6.4 + 40
    s.text(W - 48, ly + 4, "Generated from docs/make_diagrams.py", size=10, fill=PANEL_L,
           anchor="end", italic=True)

    return s.render()


# --------------------------------------------------------------------------- #
# Evaluation-pipeline diagram
# --------------------------------------------------------------------------- #
def build_eval_pipeline() -> str:
    W, H = 1500, 600
    s = SVG(W, H)

    s.text(48, 54, "RegSentinel", size=28, weight="700")
    s.text(218, 54, "· Evaluation Pipeline", size=20, fill=SUB)
    s.text(48, 82,
           "Four layers, cheapest-and-most-deterministic first. The unit and "
           "guardrail layers gate every push with no API key; the model-driven "
           "layers run when a key is configured.", size=13.5, fill=SUB)
    s.line(48, 98, W - 48, 98, RULE, sw=1.2, marker=False)

    layers = [
        (AG_S, AG_F, "UNIT", "deterministic MCP tools",
         ["risk matrix · 9 cells + bad input", "citation: valid vs fabricated",
          "control coverage → gap", "obligation recall + no-invention"],
         "no API key", OUT_S),
        (MCP_S, MCP_F, "GUARDRAIL", "governance hooks",
         ["allow authoritative regulators", "deny off-list domains",
          "deny lookalike subdomains", "non-WebFetch passthrough"],
         "no API key", OUT_S),
        (ORCH_S, ORCH_F, "AGENT", "subagents in isolation",
         ["each agent promoted to top loop", "audit-trail verifies tool use",
          "researcher → authoritative host", "least-privilege respected"],
         "needs API key", GOV_S),
        (GOV_S, GOV_F, "END-TO-END", "full orchestrated audit",
         ["report sections present", "phase order: research→…→write",
          "min recorded gap count", "obligation terms in report"],
         "needs API key", GOV_S),
    ]
    n = len(layers)
    pad, gap = 0, 28
    x0 = 48
    avail = (W - 96) - (n - 1) * gap
    cw = avail / n
    cy, ch = 150, 300
    centers = []
    for i, (st, fl, title, sub, bullets, badge, bcol) in enumerate(layers):
        x = x0 + i * (cw + gap)
        centers.append((x, x + cw))
        s.rect(x, cy, cw, ch, WHITE, st, sw=1.8, rx=12)
        s.rect(x, cy, cw, 54, fl, rx=12)
        s.rect(x, cy + 40, cw, 14, fl, rx=0)
        s.circle(x + 26, cy + 27, 12, st)
        s.text(x + 26, cy + 31.5, str(i + 1), size=13, fill=WHITE, weight="700",
               anchor="middle")
        s.text(x + 46, cy + 25, title, size=16, weight="700", fill=st)
        s.text(x + 46, cy + 44, sub, size=10.5, fill=SUB)
        by = cy + 86
        for b in bullets:
            s.circle(x + 24, by - 4, 2.2, st)
            s.text(x + 34, by, b, size=10.8, fill=INK)
            by += 26
        # badge
        bf = "#e8f6ee" if badge == "no API key" else "#fdeef1"
        s.rect(x + 18, cy + ch - 44, cw - 36, 28, bf, bcol, sw=1.3, rx=7)
        s.text(x + cw / 2, cy + ch - 25, badge, size=11, fill=bcol, weight="700",
               anchor="middle")

    # flow arrows between layers
    for i in range(n - 1):
        x2 = centers[i][1]
        s.line(x2 + 4, cy + ch / 2, x2 + gap - 4, cy + ch / 2, INK, sw=1.6)

    # CI footer
    fy = cy + ch + 46
    s.rect(48, fy - 26, W - 96, 44, PANEL_F, PANEL_S, sw=1.3, rx=10)
    s.circle(74, fy - 4, 4, ORCH_S)
    s.text(88, fy, "GitHub Actions  ·  pytest + unit + guardrail gate every push  ·  "
           "agent + e2e run on ANTHROPIC_API_KEY  ·  results rolled up to "
           "eval_summary.md", size=12, fill=INK)

    return s.render()


def main():
    out = Path(__file__).parent
    (out / "architecture.svg").write_text(build_architecture(), encoding="utf-8")
    (out / "eval_pipeline.svg").write_text(build_eval_pipeline(), encoding="utf-8")
    print("wrote", out / "architecture.svg")
    print("wrote", out / "eval_pipeline.svg")


if __name__ == "__main__":
    main()
