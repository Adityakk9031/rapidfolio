"""FastAPI router endpoints for SOP auditing and DAG compilation."""
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Dict, Any, List

from src.schemas.sop import SOPInput
from src.schemas.audit import AuditReport
from src.schemas.dag import RapidfolioDAG
from src.linter.engine import LinterEngine
from src.compiler.dag_exporter import DAGExporter

router = APIRouter(prefix="/api", tags=["SOP Linter & Compiler"])

linter_engine = LinterEngine(enable_llm=False)
dag_exporter = DAGExporter()

SAMPLES_DIR = Path(__file__).resolve().parent.parent.parent / "sample_sops"


@router.get("/health")
def health_check() -> Dict[str, str]:
    """Service health check endpoint."""
    return {"status": "healthy", "service": "Rapidfolio SOP Pre-Flight Linter"}


@router.get("/samples")
def list_samples() -> List[Dict[str, str]]:
    """Lists pre-loaded sample SOP files."""
    samples = []
    if SAMPLES_DIR.exists():
        for file in SAMPLES_DIR.glob("*.md"):
            name = file.name
            label = "Messy Bank KYB SOP (Fails Pre-Flight)" if "messy" in name else "Clean Codified KYB SOP (100% Ready)"
            samples.append({
                "id": name,
                "label": label,
                "filename": name
            })
    return samples


@router.get("/samples/{filename}")
def get_sample_content(filename: str) -> Dict[str, str]:
    """Retrieves content of a pre-loaded sample SOP."""
    target = SAMPLES_DIR / filename
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"Sample SOP '{filename}' not found.")
    content = target.read_text(encoding="utf-8")
    return {"filename": filename, "content": content}


@router.post("/audit", response_model=AuditReport)
def run_audit(sop_input: SOPInput) -> AuditReport:
    """Performs deterministic static & semantic linting on an SOP."""
    if not sop_input.content.strip():
        raise HTTPException(status_code=400, detail="SOP content cannot be empty.")
    report = linter_engine.audit(sop_input.content)
    return report


@router.post("/compile")
def compile_workflow(sop_input: SOPInput) -> Dict[str, Any]:
    """Compiles an SOP into a Rapidfolio DAG JSON specification."""
    if not sop_input.content.strip():
        raise HTTPException(status_code=400, detail="SOP content cannot be empty.")
    
    # Run audit first to check readiness
    report = linter_engine.audit(sop_input.content)
    dag, dag_json_str, metrics = dag_exporter.compile(sop_input.content, title=sop_input.title or "Compiled Workflow")
    
    return {
        "report": report.model_dump(),
        "dag": dag.model_dump(),
        "dag_json": dag_json_str,
        "metrics": metrics
    }
