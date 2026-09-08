"""Extended tests for edge cases, cycle traps, and invariant validations."""
import pytest
from src.linter.engine import LinterEngine
from src.schemas.audit import IssueCategory, IssueSeverity


def test_linter_detects_infinite_loops_and_cycles():
    engine = LinterEngine()
    cycle_sop = """
    ## 1. Looping Steps
    1.1. [Step: STEP_A | Type: rule_evaluation] Perform check. If retry needed, transition to `STEP_B`.
    1.2. [Step: STEP_B | Type: rule_evaluation] Re-evaluate. If still failing, transition to `STEP_A`.
    """
    report = engine.audit(cycle_sop)
    
    assert report.graph_metrics["has_cycles"] is True
    cycle_issues = [i for i in report.issues if i.category == IssueCategory.CIRCULAR_LOGIC]
    assert len(cycle_issues) >= 1
    assert cycle_issues[0].severity == IssueSeverity.CRITICAL


def test_linter_detects_equity_mismatch_rule():
    engine = LinterEngine()
    text = """
    2.2 Verify equity. If ownership percentages sum to less than 100%, investigate further at analyst discretion.
    """
    report = engine.audit(text)
    
    equity_issues = [i for i in report.issues if i.id.startswith("AMB_009") or "equity" in i.title.lower()]
    assert len(equity_issues) >= 1
    assert any("assert sum" in i.proposed_codification for i in equity_issues)


def test_audit_empty_content_handling():
    engine = LinterEngine()
    report = engine.audit("   \n\n  ")
    assert report.readiness_score == 100
    assert report.total_gaps_found == 0
