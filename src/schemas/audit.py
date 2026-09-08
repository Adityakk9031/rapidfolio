"""Audit report and issue schemas for SOP linting."""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class IssueCategory(str, Enum):
    AMBIGUITY_SUBJECTIVITY = "AMBIGUITY_SUBJECTIVITY"
    DEAD_END_NODE = "DEAD_END_NODE"
    UNHANDLED_EXCEPTION_PATH = "UNHANDLED_EXCEPTION_PATH"
    UNDEFINED_VARIABLE_STATE = "UNDEFINED_VARIABLE_STATE"
    VENDOR_SPEC_GAP = "VENDOR_SPEC_GAP"
    CIRCULAR_LOGIC = "CIRCULAR_LOGIC"


class AuditIssue(BaseModel):
    """An identified issue or gap in the SOP."""
    id: str = Field(..., description="Unique issue identifier")
    category: IssueCategory = Field(..., description="Category of the issue")
    severity: IssueSeverity = Field(..., description="Severity level")
    line_number: Optional[int] = Field(None, description="1-indexed line number in source text")
    quoted_text: str = Field(..., description="Exact snippet or step text flagged")
    title: str = Field(..., description="Short descriptive title of the issue")
    description: str = Field(..., description="Detailed explanation of the risk/ambiguity")
    proposed_codification: str = Field(..., description="Deterministic programmatic/boolean rule replacement")
    node_id: Optional[str] = Field(None, description="Associated graph node ID if applicable")
    vendor: Optional[str] = Field(None, description="Associated vendor/API if applicable")


class VendorIntegration(BaseModel):
    """Details of a detected vendor API integration in the SOP."""
    vendor_name: str
    detected_in_step: str
    operation: str
    has_timeout: bool
    has_error_handler: bool
    missing_specs: List[str] = Field(default_factory=list)


class AuditReport(BaseModel):
    """Comprehensive readiness audit report produced by the linter."""
    readiness_score: int = Field(..., ge=0, le=100, description="Readiness score from 0 to 100")
    status: str = Field(..., description="READY_FOR_COMPILATION | REQUIRES_REMEDIATION | CRITICAL_BLOCKERS")
    total_gaps_found: int = Field(..., description="Total count of issues detected")
    critical_count: int = Field(..., description="Number of critical issues")
    warning_count: int = Field(..., description="Number of warning issues")
    info_count: int = Field(..., description="Number of info issues")
    category_breakdown: Dict[str, int] = Field(default_factory=dict)
    issues: List[AuditIssue] = Field(default_factory=list)
    vendor_integrations: List[VendorIntegration] = Field(default_factory=list)
    graph_metrics: Dict[str, Any] = Field(default_factory=dict)
    summary: str = Field(..., description="Executive summary for compliance and engineering teams")
