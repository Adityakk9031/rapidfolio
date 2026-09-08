"""Tests for Ambiguity & Subjectivity Scanner."""
import pytest
from src.linter.ambiguity_scanner import AmbiguityScanner
from src.schemas.audit import IssueCategory, IssueSeverity


def test_ambiguity_scanner_detects_subjective_terms():
    scanner = AmbiguityScanner()
    sample_text = """
    1.1 Ingest application.
    1.2 If entity looks sketchy or high risk, escalate to manager.
    1.3 Review at analyst discretion.
    1.4 Attempt with reasonable effort to resolve.
    1.5 Send response promptly.
    """
    issues = scanner.scan(sample_text)
    
    assert len(issues) >= 4
    categories = [i.category for i in issues]
    assert IssueCategory.AMBIGUITY_SUBJECTIVITY in categories
    
    # Check that sketchy and discretion are marked CRITICAL
    sketchy_issue = next(i for i in issues if "sketchy" in i.quoted_text.lower())
    assert sketchy_issue.severity == IssueSeverity.CRITICAL
    assert "risk_engine.score" in sketchy_issue.proposed_codification


def test_ambiguity_scanner_clean_text_no_issues():
    scanner = AmbiguityScanner()
    clean_text = """
    1.1 If middesk.status == "ACTIVE": transition(STEP_UBO_PARSE)
    1.2 If risk_score > 75: transition(STATE_REJECT_HIGH_RISK)
    """
    issues = scanner.scan(clean_text)
    assert len(issues) == 0
