#!/usr/bin/env python3
"""
Python Sidecar for Tauri 2
Exposes the Construction AI Estimator via a local FastAPI server.
"""

from __future__ import annotations
import sys
import os
from pathlib import Path
import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import shutil

from models.models import ProjectAnalysis
from ingestion.digital_twin import DigitalTwinBuilder
from agents.graph import build_graph
from agents.state import AgentState
from agents.llm import LLMClient, load_prompt
from utils.export import export_json, export_excel
from visualization.annotate_2d import generate_annotated_pages
from visualization.viewer_html import build_html_viewer
from visualization.view_3d import create_advanced_massing

app = FastAPI(title="Construction AI Estimator Sidecar", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

STATE: Dict[str, Any] = {
    "project": None, "documents": [], "chat_history": [],
    "project_name": "Untitled Project",
    "output_dir": Path.home() / "ConstructionAI_Output",
    "last_viewer": None, "last_massing": None,
}
STATE["output_dir"].mkdir(parents=True, exist_ok=True)
llm = LLMClient()

class ChatRequest(BaseModel):
    message: str

class ProjectNameRequest(BaseModel):
    name: str

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/state")
def get_state():
    project = STATE["project"]
    if not project:
        return {"has_project": False, "project_name": STATE["project_name"], "chat_history": STATE["chat_history"]}
    return {
        "has_project": True,
        "project_name": project.project_name,
        "completeness": project.completeness_score,
        "trade_count": len(project.trade_packages),
        "review_count": len(project.review_priority_items),
        "packages": [{"trade_name": p.trade_name, "total_items": p.total_items, "low_confidence": p.low_confidence_count} for p in project.trade_packages],
        "chat_history": STATE["chat_history"],
        "viewer": str(STATE["last_viewer"]) if STATE["last_viewer"] else None,
        "massing": str(STATE["last_massing"]) if STATE["last_massing"] else None,
    }

@app.post("/project-name")
def set_project_name(body: ProjectNameRequest):
    STATE["project_name"] = body.name
    if STATE["project"]:
        STATE["project"].project_name = body.name
    return {"ok": True}

@app.post("/analyze")
async def analyze(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, "No files uploaded")
    upload_dir = STATE["output_dir"] / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for f in files:
        dest = upload_dir / f.filename
        with open(dest, "wb") as out:
            shutil.copyfileobj(f.file, out)
        paths.append(dest)

    builder = DigitalTwinBuilder(output_dir=STATE["output_dir"] / "digital_twins")
    documents = builder.ingest_package(paths)
    STATE["documents"] = documents

    project = ProjectAnalysis(project_id=str(uuid.uuid4()), project_name=STATE["project_name"])
    initial_state: AgentState = {
        "project": project, "documents": documents, "current_requirements": [],
        "auditor_findings": [], "iteration": 0, "max_iterations": 2,
        "needs_refinement": False, "messages": [], "errors": [],
    }
    graph = build_graph()
    final_state = graph.invoke(initial_state, config={"configurable": {"thread_id": project.project_id}})
    analysis = final_state["project"]

    vis_dir = STATE["output_dir"] / "visualization"
    annotated = generate_annotated_pages(analysis, STATE["output_dir"] / "digital_twins", vis_dir / "annotated")
    STATE["last_viewer"] = build_html_viewer(analysis, annotated, vis_dir / "viewer.html")
    STATE["last_massing"] = create_advanced_massing(analysis, STATE["output_dir"] / "digital_twins", vis_dir / "massing_3d.html")

    STATE["project"] = analysis
    STATE["chat_history"] = [{"role": "assistant", "content": f"Analysis complete for **{analysis.project_name}**.\n\n• {len(analysis.trade_packages)} trade packages\n• Completeness: {analysis.completeness_score:.0%}\n• {len(analysis.review_priority_items)} items need review"}]
    return {"ok": True, "project_name": analysis.project_name, "completeness": analysis.completeness_score, "trade_count": len(analysis.trade_packages), "review_count": len(analysis.review_priority_items)}

@app.post("/chat")
def chat(body: ChatRequest):
    project = STATE["project"]
    if not project:
        raise HTTPException(400, "No project loaded")
    lines = [f"Project: {project.project_name}", f"Completeness: {project.completeness_score:.2f}", f"Packages: {len(project.trade_packages)}"]
    for pkg in project.trade_packages:
        lines.append(f"\n## {pkg.trade_name} ({pkg.total_items} items)")
        for r in pkg.requirements[:8]:
            lines.append(f"- {r.description[:90]}")
    system = load_prompt("orchestrator") + "\nYou are in interactive chat mode. Be concise and practical."
    user = f"Current state:\n{chr(10).join(lines)}\n\nUser: {body.message}"
    reply = llm.chat(system=system, user=user, temperature=0.3)
    STATE["chat_history"].append({"role": "user", "content": body.message})
    STATE["chat_history"].append({"role": "assistant", "content": reply})
    return {"reply": reply, "history": STATE["chat_history"]}

@app.get("/packages")
def get_packages():
    project = STATE["project"]
    if not project: return {"packages": []}
    return {"packages": [{"trade_name": p.trade_name, "total_items": p.total_items, "low_confidence": p.low_confidence_count, "requirements": [{"description": r.description, "confidence": r.confidence, "override": r.assignment_override, "override_reason": r.override_reason, "flags": r.flags} for r in p.requirements]} for p in project.trade_packages]}

@app.get("/review")
def get_review():
    project = STATE["project"]
    if not project: return {"items": []}
    return {"items": [{"trade_name": r.trade_name, "description": r.description, "confidence": r.confidence, "override": r.assignment_override, "override_reason": r.override_reason, "flags": r.flags} for r in project.review_priority_items]}

@app.post("/export")
def export():
    project = STATE["project"]
    if not project: raise HTTPException(400, "No project")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    j = export_json(project, STATE["output_dir"] / f"analysis_{stamp}.json")
    x = export_excel(project, STATE["output_dir"] / f"analysis_{stamp}.xlsx")
    return {"json": str(j), "excel": str(x)}

@app.get("/viewer")
def open_viewer():
    path = STATE.get("last_viewer")
    if not path or not Path(path).exists(): raise HTTPException(404, "Viewer not generated")
    return FileResponse(path)

@app.get("/massing")
def open_massing():
    path = STATE.get("last_massing")
    if not path or not Path(path).exists(): raise HTTPException(404, "3D massing not generated")
    return FileResponse(path)

if __name__ == "__main__":
    port = int(os.environ.get("SIDECAR_PORT", "17865"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
