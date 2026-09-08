"""Tests for FastAPI HTTP endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_samples_endpoint():
    response = client.get("/api/samples")
    assert response.status_code == 200
    samples = response.json()
    assert len(samples) >= 2
    filenames = [s["filename"] for s in samples]
    assert "messy_kyb_sop.md" in filenames
    assert "clean_kyb_sop.md" in filenames


def test_audit_endpoint_messy_sop():
    sample_res = client.get("/api/samples/messy_kyb_sop.md")
    assert sample_res.status_code == 200
    content = sample_res.json()["content"]

    audit_res = client.post("/api/audit", json={"content": content, "title": "Messy KYB"})
    assert audit_res.status_code == 200
    data = audit_res.json()
    
    assert data["readiness_score"] < 70
    assert data["critical_count"] > 0
    assert len(data["issues"]) > 0


def test_compile_endpoint_clean_sop():
    sample_res = client.get("/api/samples/clean_kyb_sop.md")
    assert sample_res.status_code == 200
    content = sample_res.json()["content"]

    compile_res = client.post("/api/compile", json={"content": content, "title": "Clean KYB"})
    assert compile_res.status_code == 200
    data = compile_res.json()
    
    assert data["report"]["readiness_score"] == 100
    assert data["metrics"]["is_valid_dag"] is True
    assert len(data["dag"]["nodes"]) > 0
