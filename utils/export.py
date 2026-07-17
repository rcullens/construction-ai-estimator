"""
Export helpers – JSON and Excel.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

import pandas as pd

from models.models import ProjectAnalysis


def export_json(analysis: ProjectAnalysis, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(analysis.model_dump_json(indent=2))
    return path


def export_excel(analysis: ProjectAnalysis, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for pkg in analysis.trade_packages:
        for req in pkg.requirements:
            rows.append({
                "Trade": pkg.trade_name,
                "Description": req.description,
                "Quantity": req.quantity,
                "Unit": req.unit,
                "Confidence": req.confidence,
                "Override": req.assignment_override,
                "Override Reason": req.override_reason or "",
                "Suggested Trade": req.suggested_trade_name or "",
                "Flags": ", ".join(req.flags),
                "Sources": " | ".join(
                    f"{s.sheet_or_section}: {s.original_text[:80]}"
                    for s in req.sources
                ),
            })

    df = pd.DataFrame(rows)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="All Requirements", index=False)

        summary = []
        for pkg in analysis.trade_packages:
            summary.append({
                "Trade": pkg.trade_name,
                "Items": pkg.total_items,
                "Low Confidence": pkg.low_confidence_count,
            })
        pd.DataFrame(summary).to_excel(writer, sheet_name="Trade Summary", index=False)

        review_rows = []
        for req in analysis.review_priority_items:
            review_rows.append({
                "Trade": req.trade_name,
                "Description": req.description,
                "Confidence": req.confidence,
                "Override": req.assignment_override,
                "Reason": req.override_reason or "",
                "Flags": ", ".join(req.flags),
            })
        if review_rows:
            pd.DataFrame(review_rows).to_excel(writer, sheet_name="Needs Review", index=False)

    return path
