"""
Upgraded 3D visualization engine.

Capabilities:
- Multi-level detection from drawing text
- Room / region approximation from text blocks and bounding boxes
- Proper stacked floor plates + extruded volumes
- Trade-colored masses with hover details
- Clean interactive Plotly scene
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import colorsys

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from models.models import ProjectAnalysis


def _trade_color(name: str) -> str:
    h = int(hashlib.md5(name.encode()).hexdigest()[:6], 16)
    hue = (h % 360) / 360.0
    r, g, b = colorsys.hsv_to_rgb(hue, 0.65, 0.90)
    return f"rgb({int(r*255)},{int(g*255)},{int(b*255)})"


def _detect_levels(text: str) -> List[str]:
    patterns = [
        r"(?i)\b(level\s*[0-9]{1,2}[a-z]?)\b",
        r"(?i)\b(lvl\.?\s*[0-9]{1,2})\b",
        r"(?i)\b(floor\s*[0-9]{1,2})\b",
        r"(?i)\b((?:first|second|third|fourth|fifth|ground|basement|mezzanine|roof)\s+floor)\b",
        r"(?i)\b(level\s+(?:one|two|three|four|five|ground|basement))\b",
    ]
    found = set()
    for pat in patterns:
        for m in re.finditer(pat, text):
            found.add(m.group(1).strip().title())
    return sorted(found) if found else ["Level 1"]


def _normalize_bbox(bb: Dict, page_w: float, page_h: float) -> Tuple[float, float, float, float]:
    x0 = bb.get("x0", 0)
    y0 = bb.get("y0", 0)
    x1 = bb.get("x1", 0.05)
    y1 = bb.get("y1", 0.05)
    if x1 > 1.5 or y1 > 1.5:
        x0 /= max(page_w, 1)
        x1 /= max(page_w, 1)
        y0 /= max(page_h, 1)
        y1 /= max(page_h, 1)
    x0, x1 = max(0.0, min(x0, 1.0)), max(0.0, min(x1, 1.0))
    y0, y1 = max(0.0, min(y0, 1.0)), max(0.0, min(y1, 1.0))
    if x1 <= x0: x1 = x0 + 0.02
    if y1 <= y0: y1 = y0 + 0.02
    return x0, y0, x1, y1


def _box_mesh(x0, y0, x1, y1, z0, z1, color, name, hover):
    x = [x0, x1, x1, x0, x0, x1, x1, x0]
    y = [y0, y0, y1, y1, y0, y0, y1, y1]
    z = [z0, z0, z0, z0, z1, z1, z1, z1]
    return go.Mesh3d(
        x=x, y=y, z=z,
        i=[0, 0, 4, 4, 0, 0, 1, 1, 2, 2, 3, 3],
        j=[1, 2, 5, 6, 1, 5, 2, 6, 3, 7, 0, 4],
        k=[2, 3, 6, 7, 5, 4, 6, 5, 7, 6, 4, 7],
        color=color, opacity=0.72, name=name,
        hovertext=hover, hoverinfo="text", flatshading=True, showlegend=True,
    )


def _floor_plate(x_min, x_max, y_min, y_max, z, color="rgb(60,60,70)", name="Floor"):
    return go.Mesh3d(
        x=[x_min, x_max, x_max, x_min], y=[y_min, y_min, y_max, y_max],
        z=[z, z, z, z], i=[0, 0], j=[1, 2], k=[2, 3],
        color=color, opacity=0.45, name=name, hoverinfo="name", showlegend=False,
    )


def create_advanced_massing(
    analysis: ProjectAnalysis,
    digital_twins_dir: str | Path,
    output_path: str | Path,
    default_floor_height: float = 3.5,
) -> Optional[Path]:
    if not HAS_PLOTLY:
        print("Plotly not installed – skipping 3D. pip install plotly")
        return None

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    twins_dir = Path(digital_twins_dir)

    level_heights: Dict[str, float] = {}
    level_order: List[str] = []
    masses: List[Dict[str, Any]] = []

    all_levels = set()
    twin_cache = {}

    for twin_file in twins_dir.glob("*.json"):
        try:
            with open(twin_file, encoding="utf-8") as f:
                twin = json.load(f)
            twin_cache[twin["document_id"]] = twin
            for page in twin.get("pages", []):
                for lvl in _detect_levels(page.get("text", "")):
                    all_levels.add(lvl)
        except Exception:
            continue

    if not all_levels:
        all_levels = {"Level 1"}
    level_order = sorted(all_levels)
    for i, lvl in enumerate(level_order):
        level_heights[lvl] = i * default_floor_height

    for pkg in analysis.trade_packages:
        color = _trade_color(pkg.trade_name)
        for req in pkg.requirements:
            for src in req.sources:
                if not src.bounding_box:
                    continue
                twin = twin_cache.get(src.document_id)
                if not twin:
                    continue
                page = next((p for p in twin["pages"] if p["page_index"] == src.page), None)
                if not page:
                    continue
                page_w = page.get("width", 1000)
                page_h = page.get("height", 1000)
                x0, y0, x1, y1 = _normalize_bbox(src.bounding_box, page_w, page_h)
                page_text = page.get("text", "")
                page_levels = _detect_levels(page_text)
                level = page_levels[0] if page_levels else level_order[0]
                z0 = level_heights.get(level, 0.0)
                z1 = z0 + default_floor_height * 0.85
                masses.append({
                    "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                    "z0": z0, "z1": z1, "level": level,
                    "trade": pkg.trade_name, "color": color,
                    "label": f"{pkg.trade_name}<br>{req.description[:60]}",
                    "override": req.assignment_override,
                })

    for doc_id, twin in twin_cache.items():
        for page in twin.get("pages", []):
            page_w = page.get("width", 1000)
            page_h = page.get("height", 1000)
            page_levels = _detect_levels(page.get("text", ""))
            level = page_levels[0] if page_levels else level_order[0]
            z0 = level_heights.get(level, 0.0)
            for block in page.get("blocks", []):
                bbox = block.get("bbox")
                if not bbox or len(bbox) < 4:
                    continue
                x0, y0, x1, y1 = bbox[0] / page_w, bbox[1] / page_h, bbox[2] / page_w, bbox[3] / page_h
                w, h = x1 - x0, y1 - y0
                if w < 0.04 or h < 0.03 or w > 0.6 or h > 0.5:
                    continue
                masses.append({
                    "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                    "z0": z0, "z1": z0 + 0.18, "level": level,
                    "trade": "Detected Region", "color": "rgb(80,90,110)",
                    "label": f"Region on {level}", "override": False,
                })

    fig = go.Figure()
    if not masses:
        fig.add_trace(go.Scatter3d(x=[0, 1], y=[0, 1], z=[0, 0], mode="markers",
            marker=dict(size=1, color="rgba(0,0,0,0)"), showlegend=False))
        fig.update_layout(title="3D Massing – No usable geometry found yet", template="plotly_dark",
            scene=dict(xaxis_title="X", yaxis_title="Y", zaxis_title="Height (m)"), margin=dict(l=0, r=0, t=40, b=0))
    else:
        for lvl, z in level_heights.items():
            fig.add_trace(_floor_plate(0, 1, 0, 1, z, name=f"{lvl} plate"))
        seen_trades = set()
        for i, m in enumerate(masses[:140]):
            show_leg = m["trade"] not in seen_trades
            if show_leg: seen_trades.add(m["trade"])
            mesh = _box_mesh(m["x0"], m["y0"], m["x1"], m["y1"], m["z0"], m["z1"],
                color=m["color"], name=m["trade"], hover=m["label"] + f"<br>Level: {m['level']}")
            mesh.showlegend = show_leg
            fig.add_trace(mesh)
        fig.update_layout(
            title=dict(text=f"3D Massing – {analysis.project_name or 'Project'}<br><sup>{len(level_order)} level(s) · {len(masses)} masses · {len(analysis.trade_packages)} trades</sup>", x=0.5),
            template="plotly_dark",
            scene=dict(xaxis_title="X (normalized)", yaxis_title="Y (normalized)", zaxis_title="Height (m)",
                aspectmode="manual", aspectratio=dict(x=1, y=1, z=0.55),
                camera=dict(eye=dict(x=1.7, y=1.7, z=0.95))),
            margin=dict(l=0, r=0, t=70, b=0),
            legend=dict(title="Trades / Regions", itemsizing="constant", bgcolor="rgba(20,20,25,0.85)"),
            height=800,
        )

    fig.write_html(str(output_path), include_plotlyjs=True, full_html=True)
    return output_path


def create_simple_massing(analysis, output_path, default_height=3.5):
    out = Path(output_path)
    twins_dir = out.parent.parent / "digital_twins"
    if not twins_dir.exists():
        twins_dir = out.parent / "digital_twins"
    return create_advanced_massing(analysis, twins_dir, output_path, default_height)


def create_3d_placeholder_note(output_path: str | Path) -> Path:
    output_path = Path(output_path)
    content = """# 3D Visualization – Upgraded Engine

## Current Capabilities
- Multi-level detection
- Stacked floor plates
- Trade-colored extruded masses
- Region approximation from text blocks
- Interactive Plotly viewer

## Realistic Expectations
This is a solid spatial review aid, not a full BIM model.
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path
