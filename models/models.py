"""
Core data models for the Construction AI Estimator.
Supports standard trades, custom trades, editable display names,
and explicit cross-trade assignment overrides.
"""

from __future__ import annotations
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid


class DocumentType(str, Enum):
    DRAWING = "drawing"
    SPECIFICATION = "specification"
    PROJECT_MANUAL = "project_manual"
    ADDENDUM = "addendum"
    TECHNICAL_SHEET = "technical_sheet"
    SCHEDULE = "schedule"
    GENERAL_CONDITIONS = "general_conditions"
    OTHER = "other"


class TradeCode(str, Enum):
    """Stable internal identifiers for standard trades. Do not change these values."""
    GENERAL = "GENERAL"
    DEMOLITION = "DEMOLITION"
    CONCRETE = "CONCRETE"
    MASONRY = "MASONRY"
    STRUCTURAL_STEEL = "STRUCTURAL_STEEL"
    MILLWORK = "MILLWORK"
    THERMAL_MOISTURE = "THERMAL_MOISTURE"
    OPENINGS = "OPENINGS"
    FINISHES = "FINISHES"
    SPECIALTIES = "SPECIALTIES"
    EQUIPMENT = "EQUIPMENT"
    FURNISHINGS = "FURNISHINGS"
    SPECIAL_CONSTRUCTION = "SPECIAL_CONSTRUCTION"
    CONVEYING = "CONVEYING"
    FIRE_SUPPRESSION = "FIRE_SUPPRESSION"
    PLUMBING = "PLUMBING"
    HVAC = "HVAC"
    ELECTRICAL = "ELECTRICAL"
    COMMUNICATIONS = "COMMUNICATIONS"
    ELECTRONIC_SAFETY = "ELECTRONIC_SAFETY"
    EARTHWORK = "EARTHWORK"
    EXTERIOR_IMPROVEMENTS = "EXTERIOR_IMPROVEMENTS"
    UTILITIES = "UTILITIES"
    OTHER = "OTHER"


class CSIDivision(str, Enum):
    DIV_00 = "00 - Procurement and Contracting Requirements"
    DIV_01 = "01 - General Requirements"
    DIV_02 = "02 - Existing Conditions"
    DIV_03 = "03 - Concrete"
    DIV_04 = "04 - Masonry"
    DIV_05 = "05 - Metals"
    DIV_06 = "06 - Wood, Plastics, and Composites"
    DIV_07 = "07 - Thermal and Moisture Protection"
    DIV_08 = "08 - Openings"
    DIV_09 = "09 - Finishes"
    DIV_10 = "10 - Specialties"
    DIV_11 = "11 - Equipment"
    DIV_12 = "12 - Furnishings"
    DIV_13 = "13 - Special Construction"
    DIV_14 = "14 - Conveying Equipment"
    DIV_21 = "21 - Fire Suppression"
    DIV_22 = "22 - Plumbing"
    DIV_23 = "23 - Heating, Ventilating, and Air Conditioning (HVAC)"
    DIV_25 = "25 - Integrated Automation"
    DIV_26 = "26 - Electrical"
    DIV_27 = "27 - Communications"
    DIV_28 = "28 - Electronic Safety and Security"
    DIV_31 = "31 - Earthwork"
    DIV_32 = "32 - Exterior Improvements"
    DIV_33 = "33 - Utilities"
    DIV_34 = "34 - Transportation"
    DIV_35 = "35 - Waterway and Marine Construction"
    DIV_40 = "40 - Process Interconnections"
    DIV_41 = "41 - Material Processing and Handling Equipment"
    DIV_42 = "42 - Process Heating, Cooling, and Drying Equipment"
    DIV_43 = "43 - Process Gas and Liquid Handling, Purification, and Storage Equipment"
    DIV_44 = "44 - Pollution and Waste Control Equipment"
    DIV_45 = "45 - Industry-Specific Manufacturing Equipment"
    DIV_46 = "46 - Water and Wastewater Equipment"
    DIV_48 = "48 - Electrical Power Generation"


class SourceReference(BaseModel):
    document_id: str
    document_type: DocumentType
    sheet_or_section: str = Field(..., description="e.g. 'A-201', 'Section 22 11 16', 'Addendum 3'")
    page: Optional[int] = None
    detail_or_note_id: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None
    original_text: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.9)

    class Config:
        extra = "forbid"


class DocumentMeta(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    type: DocumentType
    page_count: int = 0
    revision: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    digital_twin_path: Optional[str] = None


class TradeDefinition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: Optional[TradeCode] = None
    display_name: str
    is_custom: bool = False
    csi_divisions: List[CSIDivision] = Field(default_factory=list)
    description: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def validate_custom_vs_standard(self):
        if self.is_custom and self.code is not None:
            raise ValueError("Custom trades must not have a TradeCode")
        if not self.is_custom and self.code is None:
            raise ValueError("Standard trades must have a TradeCode")
        return self

    def touch(self):
        self.updated_at = datetime.utcnow()


class ProjectTradeSettings(BaseModel):
    project_id: Optional[str] = None
    trades: List[TradeDefinition] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_active_trades(self) -> List[TradeDefinition]:
        return sorted([t for t in self.trades if t.is_active], key=lambda t: t.sort_order)

    def add_custom_trade(self, display_name: str, description: Optional[str] = None, csi_divisions: Optional[List[CSIDivision]] = None, sort_order: Optional[int] = None) -> TradeDefinition:
        new_trade = TradeDefinition(display_name=display_name, is_custom=True, description=description, csi_divisions=csi_divisions or [], sort_order=sort_order if sort_order is not None else len(self.trades))
        self.trades.append(new_trade)
        self.updated_at = datetime.utcnow()
        return new_trade

    def rename_trade(self, trade_id: str, new_display_name: str) -> bool:
        for trade in self.trades:
            if trade.id == trade_id:
                trade.display_name = new_display_name
                trade.touch()
                self.updated_at = datetime.utcnow()
                return True
        return False

    def deactivate_trade(self, trade_id: str) -> bool:
        for trade in self.trades:
            if trade.id == trade_id:
                trade.is_active = False
                trade.touch()
                self.updated_at = datetime.utcnow()
                return True
        return False


class ExtractedRequirement(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    trade_code: Optional[TradeCode] = None
    custom_trade: Optional[str] = None
    trade_name: str
    suggested_trade_code: Optional[TradeCode] = None
    suggested_trade_name: Optional[str] = None
    assignment_override: bool = False
    override_reason: Optional[str] = None
    csi_division: Optional[CSIDivision] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    responsibility_notes: List[str] = Field(default_factory=list)
    sources: List[SourceReference] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    flags: List[str] = Field(default_factory=list)
    related_requirements: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_trade_identity(self):
        has_code = self.trade_code is not None
        has_custom = bool(self.custom_trade and self.custom_trade.strip())
        if has_code and has_custom:
            raise ValueError("Provide either trade_code or custom_trade, not both")
        if not has_code and not has_custom:
            raise ValueError("Either trade_code or custom_trade must be provided")
        if not self.trade_name:
            self.trade_name = self.custom_trade if has_custom else self.trade_code.value
        if (self.suggested_trade_code and self.trade_code and self.suggested_trade_code != self.trade_code):
            self.assignment_override = True
        return self


class TradePackage(BaseModel):
    trade_code: Optional[TradeCode] = None
    custom_trade: Optional[str] = None
    trade_name: str
    requirements: List[ExtractedRequirement] = Field(default_factory=list)
    summary: str = ""
    total_items: int = 0
    low_confidence_count: int = 0
    missing_potential: List[str] = Field(default_factory=list)
    sources_covered: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_trade_identity(self):
        has_code = self.trade_code is not None
        has_custom = bool(self.custom_trade and self.custom_trade.strip())
        if has_code and has_custom:
            raise ValueError("Provide either trade_code or custom_trade, not both")
        if not has_code and not has_custom:
            raise ValueError("Either trade_code or custom_trade must be provided")
        return self

    def recalculate(self):
        self.total_items = len(self.requirements)
        self.low_confidence_count = sum(1 for r in self.requirements if r.confidence < 0.85)
        return self


class ProjectAnalysis(BaseModel):
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_name: Optional[str] = None
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    documents: List[DocumentMeta] = Field(default_factory=list)
    trade_packages: List[TradePackage] = Field(default_factory=list)
    global_flags: List[str] = Field(default_factory=list)
    completeness_score: float = Field(ge=0.0, le=1.0, default=0.0)
    review_priority_items: List[ExtractedRequirement] = Field(default_factory=list)

    def get_package(self, trade_code: TradeCode) -> Optional[TradePackage]:
        for pkg in self.trade_packages:
            if pkg.trade_code == trade_code:
                return pkg
        return None
