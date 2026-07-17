"""
LangGraph state definition.
"""

from __future__ import annotations
from typing import TypedDict, Annotated, List, Dict, Any, Optional
import operator

from models.models import ProjectAnalysis, ExtractedRequirement, DocumentMeta


class AgentState(TypedDict):
    project: ProjectAnalysis
    documents: List[DocumentMeta]
    current_requirements: Annotated[List[ExtractedRequirement], operator.add]
    auditor_findings: List[ExtractedRequirement]
    iteration: int
    max_iterations: int
    needs_refinement: bool
    messages: Annotated[List[str], operator.add]
    errors: List[str]
