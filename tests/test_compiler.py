"""Tests for Rapidfolio DAG Compiler and Exporter."""
import pytest
import json
from src.compiler.dag_exporter import DAGExporter
from src.schemas.dag import RapidfolioDAG, NodeType


def test_compiler_generates_valid_rapidfolio_dag():
    exporter = DAGExporter()
    sop_text = """
    ## 1. Intake
    1.1. [Step: INTAKE_01 | Type: rule_evaluation] Ingest entity payload. If valid, transition to `STEP_PERSONA_KYC`.
    1.2. [Step: STEP_PERSONA_KYC | Type: api_call | Vendor: Persona | Timeout: 30s] Verify identity. If passed, transition to `STATE_WORKFLOW_COMPLETE`.
    1.3. [Step: STATE_WORKFLOW_COMPLETE | Type: rule_evaluation] Terminal step.
    """
    dag, json_str, metrics = exporter.compile(sop_text, title="Test KYB DAG")
    
    assert isinstance(dag, RapidfolioDAG)
    assert dag.target_platform == "Rapidfolio Engine v2.4"
    assert len(dag.nodes) >= 3
    assert len(dag.edges) >= 2
    assert metrics["is_valid_dag"] is True
    
    # Parse json string to ensure valid JSON serialization
    parsed = json.loads(json_str)
    assert parsed["name"] == "Test KYB DAG"
    assert "nodes" in parsed
    assert "edges" in parsed
