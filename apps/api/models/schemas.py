from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum
from datetime import datetime
import uuid


# ============================================================
# Enums
# ============================================================

class MeasureType(str, Enum):
    bruksendring = "bruksendring"
    tilbygg = "tilbygg"
    påbygg = "påbygg"
    garasje = "garasje"
    carport = "carport"
    kjeller_innredning = "kjeller_innredning"
    loft_innredning = "loft_innredning"
    fasadeendring = "fasadeendring"
    terrenginngrep = "terrenginngrep"
    støttemur = "støttemur"
    veranda = "veranda"
    tomtedeling = "tomtedeling"
    annet = "annet"
    ukjent = "ukjent"


class RuleStatus(str, Enum):
    pass_ = "pass"
    warn = "warn"
    fail = "fail"
    unknown = "unknown"


class RiskLevel(str, Enum):
    lav = "lav"
    middels = "middels"
    høy = "høy"
    ukjent = "ukjent"


class ProjectStatus(str, Enum):
    draft = "draft"
    analyzing = "analyzing"
    analyzed = "analyzed"
    preparing = "preparing"
    ready = "ready"
    submitted = "submitted"


class PlanStatus(str, Enum):
    regulert = "regulert"
    kommuneplan = "kommuneplan"
    uregulert = "uregulert"
    ukjent = "ukjent"


class HazardLevel(str, Enum):
    ingen = "ingen"
    lav = "lav"
    middels = "middels"
    høy = "høy"
    ukjent = "ukjent"


# ============================================================
# Address
# ============================================================

class AddressSuggestion(BaseModel):
    id: str
    text: str
    addressText: str
    municipality: str
    municipalityNumber: str
    postalCode: Optional[str] = None
    postalPlace: Optional[str] = None
    lat: float
    lng: float


# ============================================================
# Property
# ============================================================

class PropertyData(BaseModel):
    id: str
    municipalityNumber: str
    municipality: str
    gnr: int
    bnr: int
    fnr: Optional[int] = None
    snr: Optional[int] = None
    areal: Optional[float] = None
    buildingStatus: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None
    address: Optional[str] = None


# ============================================================
# Plan
# ============================================================

class PlanLayerResult(BaseModel):
    planId: Optional[str] = None
    planName: Optional[str] = None
    planStatus: PlanStatus = PlanStatus.ukjent
    arealFormål: str = "ukjent"
    hensynssoner: List[str] = []
    byggegrense: Optional[float] = None
    utnyttelsesgrad: Optional[str] = None
    planUrl: Optional[str] = None
    geometry: Optional[Dict[str, Any]] = None


# ============================================================
# Hazard
# ============================================================

class HazardResult(BaseModel):
    flomFare: HazardLevel = HazardLevel.ukjent
    skredFare: HazardLevel = HazardLevel.ukjent
    flomSoneId: Optional[str] = None
    skredSoneId: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# Classification
# ============================================================

class MeasureClassification(BaseModel):
    measureType: MeasureType
    confidence: float = Field(ge=0, le=1)
    requiresPermit: Optional[bool] = None
    requiresResponsibility: Optional[bool] = None
    notes: Optional[str] = None


# ============================================================
# Rule Engine
# ============================================================

class RuleResult(BaseModel):
    ruleCode: str
    ruleName: str
    ruleGroup: str
    status: RuleStatus
    explanation: str
    evidenceRefs: List[str] = []
    blocking: bool = False
    sourceVersion: str = "1.0"


# ============================================================
# Project
# ============================================================

class CreateProjectRequest(BaseModel):
    addressText: str
    lat: float
    lng: float
    intentText: str


class Project(BaseModel):
    id: str
    addressText: str
    lat: float
    lng: float
    intentText: str
    measureType: Optional[MeasureType] = None
    status: ProjectStatus
    riskLevel: Optional[RiskLevel] = None
    applicationRequired: Optional[bool] = None
    createdAt: str
    updatedAt: str


# ============================================================
# Analysis Result
# ============================================================

class AnalysisResult(BaseModel):
    projectId: str
    property: Optional[PropertyData] = None
    planLayer: Optional[PlanLayerResult] = None
    hazard: Optional[HazardResult] = None
    classification: Optional[MeasureClassification] = None
    ruleResults: List[RuleResult] = []
    riskLevel: RiskLevel = RiskLevel.ukjent
    applicationRequired: Optional[bool] = None
    aiSummary: Optional[str] = None
    nextSteps: List[str] = []
    documentRequirements: List[str] = []
    warnings: List[str] = []
    analyzedAt: str


# ============================================================
# API Response wrapper
# ============================================================

class ApiResponse(BaseModel):
    data: Any
    success: bool = True
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None
