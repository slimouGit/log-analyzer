from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


Severity = Literal["low", "medium", "high", "critical"]
IncidentType = Literal[
    "application_error",
    "database_error",
    "network_error",
    "configuration_error",
    "performance_issue",
    "security_related",
    "unknown",
]


class LogInput(BaseModel):
    title: str = Field(..., min_length=3, max_length=160)
    raw_log: str = Field(..., min_length=20, max_length=20_000)
    language: str = Field(default="unknown", max_length=50)
    source: str = Field(default="unknown", max_length=80)


class LogAnalysis(BaseModel):
    incident_type: IncidentType
    severity: Severity
    affected_component: str = Field(..., min_length=1, max_length=160)
    short_summary: str = Field(..., min_length=1, max_length=500)
    probable_root_cause: str = Field(..., min_length=1, max_length=1000)
    important_log_lines: list[str] = Field(default_factory=list, max_length=8)
    recommended_debug_steps: list[str] = Field(default_factory=list, max_length=10)
    possible_fix_direction: str = Field(..., min_length=1, max_length=1000)
    test_cases: list[str] = Field(default_factory=list, max_length=10)
    confidence: float = Field(..., ge=0.0, le=1.0)


class LogAnalysisResponse(BaseModel):
    analysis_id: int
    analysis: LogAnalysis


class StoredLogAnalysis(BaseModel):
    id: int
    title: str
    raw_log: str
    language: str
    source: str
    analysis: LogAnalysis
    created_at: datetime
