"""
Generate a self-contained interactive HTML viewer for 2D plan review.
Shows annotated pages + trade-colored requirement list.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from models.models import ProjectAnalysis
from visualization.annotate_2d import trade_color, generate_annotated_pages


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{project_name} – Trade Breakdown Viewer</title>
<style>
  :root {{ --bg: #0f1115; --panel: #1a1d24; --border: #2a2f3a; --text: #e6e9ef; --muted: #8b93a7; --accent: #3b82f6; }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); height: 100vh; display: flex; flex-direction: column; }}
  header {{ background: var(--panel); border-bottom: 1px solid var(--border); padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; }}
  header h1 {{ font-size: 1.1rem; font-weight: 600; }}
  .main {{ flex: 1; display: grid; grid-template-columns: 320px 1fr 340px; overflow: hidden; }}
  .panel {{ background: var(--panel); border-right: 1px solid var(--border); overflow-y: auto; padding: 12px; }}
  .panel:last-child {{ border-right: none; border-left: 1px solid var(--border); }}
  .trade-item {{ display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: 6px; cursor: pointer; margin-bottom: 4px; font-size: 0.9rem; }}
  .trade-item:hover, .trade-item.active {{ background: #252a35; }}
  .swatch {{ width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; }}
  .viewer {{ display: flex; flex-direction: column; background: #111; overflow: hidden; }}
  .canvas-wrap {{ flex: 1; overflow: auto; display: flex; align-items: flex-start; justify-content: center; padding: 20px; }}
  .canvas-wrap img {{ max-width: 100%; height: auto; box-shadow: 0 8px 32px rgba(0,0,0,0.5); border-radius: 4px; }}
  .req-card {{ background: #252a35; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px; font-size: 0.85rem; border-left: 3px solid #555; }}
  .req-card.override {{ border-left-color: #f59e0b; }}
  .empty {{ color: var(--muted); font-size: 0.9rem; padding: 20px; text-align: center; }}
</style>
</head>
<body>
<header>
  <div><h1>{project_name}</h1><div style="color:var(--muted);font-size:0.85rem">Completeness: {completeness:.0%} · {total_reqs} requirements · {review_count} need review</div></div>
  <div style="color:var(--muted);font-size:0.85rem">{generated_at}</div>
</header>
<div class="main">
  <div class="panel"><h2 style="font-size:0.75rem;text-transform:uppercase;color:var(--muted);margin-bottom:10px">Trades</h2><div id="trade-list">{trade_list_html}</div></div>
  <div class="viewer">
    <div style="padding:8px 12px;background:var(--panel);border-bottom:1px solid var(--border)">
      <select id="page-select" onchange="showPage(this.value)">{page_options}</select>
    </div>
    <div class="canvas-wrap" id="canvas"><div class="empty">Select a page or trade</div></div>
  </div>
  <div class="panel"><h2 style="font-size:0.75rem;text-transform:uppercase;color:var(--muted);margin-bottom:10px">Requirements</h2><div id="req-list"><div class="empty">Click a trade or page</div></div></div>
</div>
<script>
const pages = {pages_json};
const packages = {packages_json};
function showPage(idx) {{ const p = pages[idx]; if (!p) return; document.getElementById('canvas').innerHTML = `<img src="${{p.annotated_image}}" alt="Page ${{p.page}}">`; }}
function filterTrade(name) {{
  document.querySelectorAll('.trade-item').forEach(el => el.classList.toggle('active', el.dataset.trade === name));
  const pkg = packages.find(p => p.trade_name === name);
  const list = document.getElementById('req-list');
  if (!pkg || !pkg.requirements.length) {{ list.innerHTML = '<div class="empty">No requirements</div>'; return; }}
  list.innerHTML = pkg.requirements.map(r => `
    <div class="req-card ${{r.assignment_override ? 'override' : ''}}">
      <div style="font-weight:600;margin-bottom:4px">${{r.trade_name}}</div>
      <div style="color:var(--muted)">${{r.description}}</div>
    </div>`).join('');
}}
if (pages.length) {{ document.getElementById('page-select').selectedIndex = 0; showPage(0); }}
</script>
</body>
</html>
"""


def build_html_viewer(
    analysis: ProjectAnalysis,
    annotated_pages: List[Dict[str, Any]],
    output_path: str | Path,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    trade_items = []
    colors = {}
    for pkg in analysis.trade_packages:
        c = trade_color(pkg.trade_name)
        hex_color = f"#{c[0]:02x}{c[1]:02x}{c[2]:02x}"
        colors[pkg.trade_name] = hex_color
        trade_items.append(
            f'<div class="trade-item" data-trade="{pkg.trade_name}" onclick="filterTrade(\'{pkg.trade_name}\')">'
            f'<div class="swatch" style="background:{hex_color}"></div>'
            f'<span>{pkg.trade_name}</span>'
            f'<span style="margin-left:auto;color:var(--muted)">{pkg.total_items}</span></div>'
        )

    page_options = "\n".join(
        f'<option value="{i}">{p["filename"]} – p{p["page"]}</option>'
        for i, p in enumerate(annotated_pages)
    ) or '<option>No annotated pages</option>'

    packages_data = []
    for pkg in analysis.trade_packages:
        packages_data.append({
            "trade_name": pkg.trade_name,
            "requirements": [
                {
                    "description": r.description,
                    "trade_name": r.trade_name,
                    "assignment_override": r.assignment_override,
                    "override_reason": r.override_reason,
                    "flags": r.flags,
                    "confidence": r.confidence,
                }
                for r in pkg.requirements
            ]
        })

    html = HTML_TEMPLATE.format(
        project_name=analysis.project_name or "Untitled Project",
        completeness=analysis.completeness_score,
        total_reqs=sum(p.total_items for p in analysis.trade_packages),
        review_count=len(analysis.review_priority_items),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        trade_list_html="\n".join(trade_items),
        page_options=page_options,
        pages_json=json.dumps(annotated_pages),
        packages_json=json.dumps(packages_data),
    )

    output_path.write_text(html, encoding="utf-8")
    return output_path
