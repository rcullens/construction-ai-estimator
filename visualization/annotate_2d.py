"""
2D visualization: annotate drawing pages with extracted requirements.
Color-coded by trade. Produces both static images and data for interactive HTML.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import colorsys
import hashlib

from PIL import Image, ImageDraw, ImageFont

from models.models import ProjectAnalysis, ExtractedRequirement, TradePackage


def trade_color(trade_name: str) -> Tuple[int, int, int]:
    """Deterministic bright color from trade name."""
    h = int(hashlib.md5(trade_name.encode()).hexdigest()[:6], 16)
    hue = (h % 360) / 360.0
    r, g, b = colorsys.hsv_to_rgb(hue, 0.75, 0.95)
    return int(r * 255), int(g * 255), int(b * 255)


def annotate_page(
    image_path: str | Path,
    requirements: List[ExtractedRequirement],
    output_path: str | Path,
    page_width: float = 1.0,
    page_height: float = 1.0,
) -> Path:
    img = Image.open(image_path).convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except Exception:
        font = ImageFont.load_default()
        font_small = font

    w, h = img.size

    for req in requirements:
        color = trade_color(req.trade_name)
        for src in req.sources:
            if not src.bounding_box:
                continue
            bb = src.bounding_box
            x0 = bb.get("x0", 0)
            y0 = bb.get("y0", 0)
            x1 = bb.get("x1", 0)
            y1 = bb.get("y1", 0)

            if x1 <= 1.0 and y1 <= 1.0:
                x0, y0, x1, y1 = x0 * w, y0 * h, x1 * w, y1 * h

            draw.rectangle([x0, y0, x1, y1], outline=color + (220,), width=3)
            label = f"{req.trade_name[:18]}"
            if req.assignment_override:
                label = "\u26a1 " + label
            bbox = draw.textbbox((x0, y0 - 18), label, font=font_small)
            draw.rectangle(bbox, fill=color + (200,))
            draw.text((x0, y0 - 18), label, fill=(0, 0, 0, 255), font=font_small)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(output_path, quality=92)
    return output_path


def generate_annotated_pages(
    analysis: ProjectAnalysis,
    digital_twins_dir: str | Path,
    output_dir: str | Path,
) -> List[Dict[str, Any]]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    twins_dir = Path(digital_twins_dir)

    by_page: Dict[Tuple[str, int], List[ExtractedRequirement]] = defaultdict(list)

    for pkg in analysis.trade_packages:
        for req in pkg.requirements:
            for src in req.sources:
                if src.page is not None and src.bounding_box:
                    by_page[(src.document_id, src.page)].append(req)

    results = []
    for (doc_id, page_idx), reqs in by_page.items():
        twin_files = list(twins_dir.glob(f"{doc_id}.json"))
        if not twin_files:
            continue
        with open(twin_files[0]) as f:
            twin = json.load(f)

        page_info = next((p for p in twin.get("pages", []) if p["page_index"] == page_idx), None)
        if not page_info or not page_info.get("image_path"):
            continue

        out_name = f"annotated_{doc_id[:8]}_p{page_idx:03d}.jpg"
        out_path = output_dir / out_name
        annotate_page(page_info["image_path"], reqs, out_path)

        results.append({
            "document_id": doc_id,
            "filename": twin.get("filename", ""),
            "page": page_idx,
            "annotated_image": str(out_path),
            "original_image": page_info["image_path"],
            "requirement_count": len(reqs),
            "trades": list({r.trade_name for r in reqs}),
        })

    return results
