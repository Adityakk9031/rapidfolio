"""Tests for Vendor Integration Tagger."""
import pytest
from src.linter.vendor_tagger import VendorTagger
from src.schemas.audit import IssueCategory


def test_vendor_tagger_identifies_missing_timeout_and_error_handling():
    tagger = VendorTagger()
    sop_text = """
    1.1 Run identity and biometric verification via Persona API.
    1.2 Submit entity name to ComplyAdvantage for global sanctions.
    """
    integrations, issues = tagger.analyze(sop_text)
    
    vendor_names = [v.vendor_name for v in integrations]
    assert "Persona" in vendor_names
    assert "ComplyAdvantage" in vendor_names
    
    persona_integration = next(v for v in integrations if v.vendor_name == "Persona")
    assert persona_integration.has_timeout is False
    assert len(persona_integration.missing_specs) > 0


def test_vendor_tagger_clean_sop_configured():
    tagger = VendorTagger()
    from pathlib import Path
    clean_sop_path = Path(__file__).resolve().parent.parent / "sample_sops" / "clean_kyb_sop.md"
    clean_text = clean_sop_path.read_text(encoding="utf-8")
    
    integrations, issues = tagger.analyze(clean_text)
    assert len(integrations) >= 4
    
    persona_int = next((v for v in integrations if v.vendor_name == "Persona"), None)
    assert persona_int is not None
    assert persona_int.has_timeout is True
    assert persona_int.has_error_handler is True
