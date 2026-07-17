#!/usr/bin/env python3
"""
Main entry point for the Construction AI Estimator.
Usage:
    python run_analysis.py /path/to/pdf1.pdf /path/to/pdf2.pdf ...
    python run_analysis.py --project-name "My Job" ./plans/*.pdf
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import List, Optional
import uuid
from datetime import datetime

import typer
from rich.console import Console
from rich.table import Table

from models.models import ProjectAnalysis
from config.default_trades import DEFAULT_TRADE_DEFINITIONS
from ingestion.digital_twin import DigitalTwinBuilder
from agents.graph import build_graph
from agents.state import AgentState
from utils.export import export_json, export_excel
from visualization.annotate_2d import generate_annotated_pages
from visualization.viewer_html import build_html_viewer
from visualization.view_3d import create_advanced_massing, create_3d_placeholder_note

app = typer.Typer(help="Construction AI Estimator – trade responsibility breakdown")
console = Console()


@app.command()
def analyze(
    files: List[Path] = typer.Argument(..., help="PDF files to analyze"),
    project_name: Optional[str] = typer.Option(None, "--project-name", "-n"),
    output_dir: Path = typer.Option("./output", "--output", "-o"),
    max_iterations: int = typer.Option(2, "--max-iterations"),
):
    """Run full analysis pipeline on one or more construction PDFs."""

    console.print("\n[bold blue]Construction AI Estimator[/bold blue]")
    console.print(f"Project : {project_name or 'Untitled'}")
    console.print(f"Files   : {len(files)}\n")

    console.print("[bold]1. Building Digital Twins...[/bold]")
    builder = DigitalTwinBuilder(output_dir=output_dir / "digital_twins")
    documents = builder.ingest_package(files)

    project = ProjectAnalysis(
        project_id=str(uuid.uuid4()),
        project_name=project_name or f"Analysis {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    )

    initial_state: AgentState = {
        "project": project,
        "documents": documents,
        "current_requirements": [],
        "auditor_findings": [],
        "iteration": 0,
        "max_iterations": max_iterations,
        "needs_refinement": False,
        "messages": [],
        "errors": [],
    }

    console.print("\n[bold]2. Running multi-agent analysis...[/bold]")
    graph = build_graph()
    config = {"configurable": {"thread_id": project.project_id}}

    final_state = graph.invoke(initial_state, config=config)

    analysis: ProjectAnalysis = final_state["project"]

    console.print("\n[bold]3. Exporting results...[/bold]")
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = export_json(analysis, output_dir / f"analysis_{stamp}.json")
    xlsx_path = export_excel(analysis, output_dir / f"analysis_{stamp}.xlsx")

    console.print("\n[bold]4. Generating visualizations...[/bold]")
    vis_dir = output_dir / "visualization"
    annotated = generate_annotated_pages(
        analysis,
        digital_twins_dir=output_dir / "digital_twins",
        output_dir=vis_dir / "annotated",
    )
    html_path = build_html_viewer(
        analysis,
        annotated_pages=annotated,
        output_path=vis_dir / f"viewer_{stamp}.html",
    )
    massing_path = create_advanced_massing(
        analysis,
        digital_twins_dir=output_dir / "digital_twins",
        output_path=vis_dir / f"massing_3d_{stamp}.html",
    )
    create_3d_placeholder_note(vis_dir / "3d_notes.md")

    table = Table(title="Trade Packages")
    table.add_column("Trade", style="cyan")
    table.add_column("Items", justify="right")
    table.add_column("Low Conf", justify="right")
    table.add_column("Overrides", justify="right")

    for pkg in analysis.trade_packages:
        overrides = sum(1 for r in pkg.requirements if r.assignment_override)
        table.add_row(
            pkg.trade_name,
            str(pkg.total_items),
            str(pkg.low_confidence_count),
            str(overrides),
        )

    console.print(table)
    console.print(f"\nCompleteness score : {analysis.completeness_score:.2f}")
    console.print(f"Items needing review: {len(analysis.review_priority_items)}")
    console.print(f"\nJSON     \u2192 {json_path}")
    console.print(f"Excel    \u2192 {xlsx_path}")
    console.print(f"2D Viewer\u2192 {html_path}")
    if massing_path:
        console.print(f"3D Massing\u2192 {massing_path}")
    console.print("\n[green]Done.[/green]")


if __name__ == "__main__":
    app()
