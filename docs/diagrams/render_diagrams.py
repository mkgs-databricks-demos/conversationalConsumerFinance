#!/usr/bin/env python3
"""
render_diagrams.py - Generate Databricks-branded interactive HTML from Mermaid sources.

Run from the docs/diagrams/ directory:
    python render_diagrams.py

Generates:
    html/  - Databricks-branded interactive HTML (dark theme, hover tooltips, responsive)
    svg/   - Lightweight self-rendering HTML for SVG export

Colors: Databricks palette
    #FF3621 (red), #1B3139 (dark), #00A972 (green), #FFAB00 (amber), #077A9D (teal)

Requires: Mermaid source files in mermaid/ directory (17 files, 01-17)
Uses: Mermaid.js CDN for client-side rendering
"""
import pathlib, os

TITLES = {
    "01": "Six-Layer Architecture",
    "02": "Three-Bundle Deployment",
    "03": "Consumer Request Flow",
    "04": "Two-Layer Metric View Pattern",
    "05": "Layered Security Model",
    "06": "Account Lifecycle State Machine",
    "07": "Transaction Processing State Machine",
    "08": "Product Relationship State Machine",
    "09": "State Machine Coupling Points",
    "10": "Medallion Architecture",
    "11": "Lakebase Session Lifecycle",
    "12": "Genie Code Data Mapping Workflow",
    "13": "Locale Abstraction",
    "14": "Daily Simulation Execution Flow",
    "15": "Agent Orchestration Routing",
    "16": "Two-Layer MV Data Flow",
    "17": "Genie Code Mapping Workflow",
}

CSS = """
body{font-family:system-ui,sans-serif;background:#0D1B22;color:#E8EAED;margin:0;min-height:100vh;display:flex;flex-direction:column}
header{background:linear-gradient(135deg,#1B3139,#0F2028);border-bottom:3px solid #FF3621;padding:20px 40px;display:flex;align-items:center;gap:16px}
.logo{width:32px;height:32px;background:#FF3621;border-radius:4px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:18px;color:#fff}
h1{font-size:18px;font-weight:600}
.badge{background:#077A9D;color:#fff;padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;text-transform:uppercase}
.num{color:#FFAB00;font-size:14px;font-weight:700;margin-left:auto}
.sub{background:#162730;padding:12px 40px;font-size:13px;color:#9AA0A6;border-bottom:1px solid rgba(255,255,255,.06)}
main{flex:1;display:flex;align-items:center;justify-content:center;padding:40px}
.mermaid{background:#162730;border-radius:12px;padding:40px;box-shadow:0 4px 24px rgba(0,0,0,.3);max-width:100%;overflow-x:auto}
.mermaid svg{max-width:100%;height:auto}
.node:hover{filter:brightness(1.2);cursor:pointer}
footer{background:#162730;border-top:1px solid rgba(255,255,255,.06);padding:12px 40px;font-size:11px;color:#9AA0A6;display:flex;justify-content:space-between}
@media(max-width:768px){header,main,.sub,footer{padding:16px 20px}.mermaid{padding:20px}}
"""

MERMAID_INIT = (
    "mermaid.initialize({startOnLoad:true,theme:'dark',"
    "themeVariables:{primaryColor:'#077A9D',primaryTextColor:'#E8EAED',"
    "primaryBorderColor:'#077A9D',lineColor:'#9AA0A6',secondaryColor:'#1B3139',"
    "tertiaryColor:'#162730',noteBkgColor:'#2A3A44',noteTextColor:'#E8EAED',"
    "noteBorderColor:'#077A9D',actorBkg:'#077A9D',actorTextColor:'#fff',"
    "actorBorder:'#077A9D',signalColor:'#E8EAED',signalTextColor:'#E8EAED'},"
    "flowchart:{curve:'basis',htmlLabels:true},"
    "sequence:{mirrorActors:false,actorMargin:50}});"
)

def extract_mermaid(text):
    i = text.find("```mermaid")
    if i < 0: return text.strip()
    i = text.index("\n", i) + 1
    j = text.find("```", i)
    return text[i:j].strip()

def render_all():
    mdir = pathlib.Path("mermaid")
    hdir = pathlib.Path("html")
    sdir = pathlib.Path("svg")
    hdir.mkdir(exist_ok=True)
    sdir.mkdir(exist_ok=True)
    
    for md in sorted(mdir.glob("*.md")):
        num = md.name[:2]
        title = TITLES.get(num, md.stem)
        src = extract_mermaid(md.read_text())
        
        # Interactive HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title} - Conversational Consumer Finance</title>
<style>{CSS}</style>
</head>
<body>
<header>
<div class="logo">D</div>
<h1>{title}</h1>
<span class="badge">Phase 1</span>
<span class="num">Diagram {num} of 17</span>
</header>
<div class="sub">Conversational Consumer Finance &mdash; FIBO-Aligned &bull; 12 State Machines &bull; 14 Silver Tables &bull; 3 Metric Views &bull; Single Agent per Locale</div>
<main>
<div class="mermaid">
{src}
</div>
</main>
<footer>
<span>Author: Matthew Giglia &bull; Databricks Field Engineering</span>
<span>Updated: Oct 7, 2026 &bull; v2 (Expanded Architecture)</span>
</footer>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>{MERMAID_INIT}</script>
</body>
</html>"""
        (hdir / (md.stem + ".html")).write_text(html)
        
        # SVG renderer (lightweight)
        svg = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{title}</title></head>
<body style="background:#0D1B22;display:flex;justify-content:center;padding:40px">
<div class="mermaid">
{src}
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>{MERMAID_INIT}</script>
</body></html>"""
        (sdir / (md.stem + ".html")).write_text(svg)
        
        print(f"  {num}: {md.stem}")
    
    print(f"\nDone! {len(list(hdir.glob('*.html')))} HTML + {len(list(sdir.glob('*.html')))} SVG files generated.")

if __name__ == "__main__":
    render_all()
