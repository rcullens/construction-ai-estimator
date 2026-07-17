"""
LangGraph node implementations.
Each node is responsible for one stage of the analysis pipeline.
"""

from __future__ import annotations
import json
import uuid
from typing import Dict, Any, List
from pathlib import Path

from agents.state import AgentState
from agents.llm import LLMClient, load_prompt
from models.models import (
    ProjectAnalysis, ExtractedRequirement, TradePackage,
    TradeCode, DocumentMeta, SourceReference, DocumentType
)
from ingestion.digital_twin import load_digital_twin


llm = LLMClient()


def _safe_parse_requirements(raw: str) -> List[ExtractedRequirement]:
    """Best-effort parse of LLM output into ExtractedRequirement list."""
    try:
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start >= 0 and end > start:
            data = json.loads(raw[start:end])
            results = []
            for item in data:
                try:
                    req = ExtractedRequirement(
                        description=item.get("description", "No description"),
                        trade_code=TradeCode(item["trade_code"]) if item.get("trade_code") else None,
                        custom_trade=item.get("custom_trade"),
                        trade_name=item.get("trade_name") or item.get("custom_trade") or "Unknown",
                        suggested_trade_code=TradeCode(item["suggested_trade_code"]) if item.get("suggested_trade_code") else None,
                        suggested_trade_name=item.get("suggested_trade_name"),
                        assignment_override=item.get("assignment_override", False),
                        override_reason=item.get("override_reason"),
                        confidence=float(item.get("confidence", 0.7)),
                        flags=item.get("flags", []),
                        sources=[
                            SourceReference(
                                document_id=s.get("document_id", "unknown"),
                                document_type=DocumentType(s.get("document_type", "other")),
                                sheet_or_section=s.get("sheet_or_section", "unknown"),
                                page=s.get("page"),
                                original_text=s.get("original_text", ""),
                                confidence=float(s.get("confidence", 0.8)),
                            )
                            for s in item.get("sources", [])
                        ] or [
                            SourceReference(
                                document_id="unknown",
                                document_type=DocumentType.OTHER,
                                sheet_or_section="unknown",
                                original_text="No source captured",
                                confidence=0.3,
                            )
                        ],
                    )
                    results.append(req)
                except Exception:
                    continue
            return results
    except Exception:
        pass
    return []


def ingestion_node(state: AgentState) -> Dict[str, Any]:
    msg = f"Ingestion complete. {len(state.get('documents', []))} documents ready."
    return {"messages": [msg]}


def spec_manual_node(state: AgentState) -> Dict[str, Any]:
    system = load_prompt("spec_manual_agent")
    all_reqs: List[ExtractedRequirement] = []

    for doc in state.get("documents", []):
        if doc.type not in (DocumentType.SPECIFICATION, DocumentType.PROJECT_MANUAL,
                            DocumentType.ADDENDUM, DocumentType.GENERAL_CONDITIONS):
            continue
        if not doc.digital_twin_path:
            continue

        twin = load_digital_twin(doc.digital_twin_path)
        text_content = "\n\n".join(
            f"--- Page {p['page_index']} ---\n{p['text'][:4000]}"
            for p in twin.get("pages", [])[:15]
        )

        user = f"""Document: {doc.filename}
Type: {doc.type.value}

Content:
{text_content[:30000]}

Extract all requirements as a JSON array of objects matching the ExtractedRequirement schema.
Include suggested_trade_code / suggested_trade_name based on normal practice.
If the text reassigns work to a different trade, set assignment_override and override_reason.
"""
        raw = llm.chat(system=system, user=user)
        reqs = _safe_parse_requirements(raw)
        all_reqs.extend(reqs)

    return {
        "current_requirements": all_reqs,
        "messages": [f"Spec/Manual agent extracted {len(all_reqs)} requirements."]
    }


def drawing_analyst_node(state: AgentState) -> Dict[str, Any]:
    system = load_prompt("drawing_analyst")
    all_reqs: List[ExtractedRequirement] = []

    for doc in state.get("documents", []):
        if doc.type != DocumentType.DRAWING:
            continue
        if not doc.digital_twin_path:
            continue

        twin = load_digital_twin(doc.digital_twin_path)
        for page in twin.get("pages", [])[:8]:
            user = f"""Document: {doc.filename}
Page: {page['page_index']}
Image path: {page.get('image_path')}

Page text (OCR):
{page.get('text', '')[:6000]}

Extract notes, keynotes, general notes, detail callouts, and any scope language.
Return a JSON array of ExtractedRequirement objects.
Pay special attention to cross-trade assignment language.
"""
            raw = llm.chat(system=system, user=user)
            reqs = _safe_parse_requirements(raw)
            all_reqs.extend(reqs)

    return {
        "current_requirements": all_reqs,
        "messages": [f"Drawing Analyst extracted {len(all_reqs)} requirements."]
    }


def trade_scope_node(state: AgentState) -> Dict[str, Any]:
    system = load_prompt("trade_scope_agent").replace("{TRADE}", "All Trades")
    existing = state.get("current_requirements", [])

    summary = "\n".join(
        f"- [{r.trade_name}] {r.description[:120]} (conf={r.confidence:.2f})"
        for r in existing[:80]
    )

    user = f"""Current extracted requirements ({len(existing)} total):
{summary}

Review the list. 
- Confirm or correct trade assignments.
- Add any missing items you can infer from context.
- Ensure every cross-trade assignment has an override_reason.
- Return the full improved list as a JSON array of ExtractedRequirement objects.
"""
    raw = llm.chat(system=system, user=user)
    improved = _safe_parse_requirements(raw)

    final = improved if improved else existing

    return {
        "current_requirements": final,
        "messages": [f"Trade Scope pass produced {len(final)} requirements."]
    }


def completeness_auditor_node(state: AgentState) -> Dict[str, Any]:
    system = load_prompt("completeness_auditor")
    existing = state.get("current_requirements", [])

    summary = "\n".join(
        f"- id={r.id[:8]} | {r.trade_name} | override={r.assignment_override} | {r.description[:100]}"
        for r in existing[:100]
    )

    user = f"""Current requirements ({len(existing)} items):
{summary}

Attack this list. Find:
1. Missing requirements that should exist based on typical construction documents.
2. Undocumented cross-trade assignments (missing override_reason).
3. Conflicts or ambiguities.

Return a JSON array of new or corrected ExtractedRequirement objects for every issue you find.
If the list looks solid, return an empty array [].
"""
    raw = llm.chat(system=system, user=user)
    findings = _safe_parse_requirements(raw)

    needs = len(findings) > 0 or any(r.confidence < 0.85 for r in existing)

    return {
        "auditor_findings": findings,
        "current_requirements": findings,
        "needs_refinement": needs,
        "messages": [f"Auditor found {len(findings)} issues. needs_refinement={needs}"]
    }


def refinement_node(state: AgentState) -> Dict[str, Any]:
    return {
        "iteration": state.get("iteration", 0) + 1,
        "needs_refinement": False,
        "messages": [f"Refinement iteration {state.get('iteration', 0) + 1} complete."]
    }


def finalize_node(state: AgentState) -> Dict[str, Any]:
    project: ProjectAnalysis = state["project"]
    all_reqs = state.get("current_requirements", [])

    packages: Dict[str, TradePackage] = {}

    for req in all_reqs:
        key = req.trade_name
        if key not in packages:
            packages[key] = TradePackage(
                trade_code=req.trade_code,
                custom_trade=req.custom_trade,
                trade_name=req.trade_name,
            )
        packages[key].requirements.append(req)

    final_packages = []
    review_items = []
    for pkg in packages.values():
        pkg.recalculate()
        final_packages.append(pkg)
        for r in pkg.requirements:
            if r.confidence < 0.85 or r.assignment_override or "needs_review" in r.flags:
                review_items.append(r)

    project.trade_packages = sorted(final_packages, key=lambda p: p.trade_name)
    project.review_priority_items = review_items
    project.completeness_score = max(0.0, min(1.0, 1.0 - (len(review_items) / max(len(all_reqs), 1)) * 0.5))
    project.documents = state.get("documents", [])

    return {
        "project": project,
        "messages": [f"Finalized {len(final_packages)} trade packages. {len(review_items)} items need review."]
    }
