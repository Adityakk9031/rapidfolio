"""Tests for Scoring Calculator & Readiness Evaluation."""
import pytest
from src.linter.scoring import ScoringCalculator
from src.schemas.audit import AuditIssue, IssueCategory, IssueSeverity


def test_scoring_clean_sop_reaches_100_percent():
    calculator = ScoringCalculator()
    score, status, breakdown, summary = calculator.calculate([], {"has_cycles": False, "dead_end_nodes": []})
    
    assert score == 100
    assert status == "READY_FOR_COMPILATION"


def test_scoring_penalties_on_critical_blockers():
    calculator = ScoringCalculator()
    mock_issues = [
        AuditIssue(
            id="CRIT_1",
            category=IssueCategory.DEAD_END_NODE,
            severity=IssueSeverity.CRITICAL,
            quoted_text="Dead end",
            title="Dead end",
            description="Dead end description",
            proposed_codification="codification"
        ),
        AuditIssue(
            id="CRIT_2",
            category=IssueCategory.AMBIGUITY_SUBJECTIVITY,
            severity=IssueSeverity.CRITICAL,
            quoted_text="Looks sketchy",
            title="Sketchy",
            description="Subjective description",
            proposed_codification="risk_score > 75"
        )
    ]
    score, status, breakdown, summary = calculator.calculate(mock_issues, {"has_cycles": False, "dead_end_nodes": []})
    
    assert score <= 88
    assert status == "REQUIRES_REMEDIATION"
