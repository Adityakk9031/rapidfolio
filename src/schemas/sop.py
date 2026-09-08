"""SOP input and parsed data schemas."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SOPInput(BaseModel):
    """Raw SOP input from user."""
    content: str = Field(..., description="Raw text or markdown content of the SOP")
    title: Optional[str] = Field("Uploaded SOP", description="Optional title or filename")


class SOPStep(BaseModel):
    """Structured procedural step parsed from an SOP."""
    step_id: str
    section: str
    line_number: int
    raw_text: str
    step_type: Optional[str] = "rule_evaluation"
    vendor: Optional[str] = None
    timeout_seconds: Optional[int] = None
    conditions: List[str] = Field(default_factory=list)
    targets: List[str] = Field(default_factory=list)
    is_terminal: bool = False


class SOPSection(BaseModel):
    """A section within an SOP."""
    section_id: str
    title: str
    line_start: int
    line_end: int
    steps: List[SOPStep] = Field(default_factory=list)
