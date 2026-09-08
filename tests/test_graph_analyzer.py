"""Tests for NetworkX Graph & Edge-Case Analyzer."""
import pytest
from src.linter.graph_analyzer import GraphAnalyzer
from src.schemas.audit import IssueCategory


def test_graph_analyzer_detects_dead_ends():
    analyzer = GraphAnalyzer()
    text_with_deadend = """
    1.1 Ingest application.
    1.2 Route to Tier 2 Review in Jira.
    """
    G, issues, metrics = analyzer.analyze(text_with_deadend)
    
    assert metrics["total_nodes"] >= 2
    dead_end_issues = [i for i in issues if i.category == IssueCategory.DEAD_END_NODE]
    assert len(dead_end_issues) >= 1
    assert any("TIER_2_REVIEW" in i.node_id or "STEP_1_2" in i.node_id for i in dead_end_issues)


def test_graph_analyzer_clean_sop_has_no_deadends():
    analyzer = GraphAnalyzer()
    from pathlib import Path
    clean_sop_path = Path(__file__).resolve().parent.parent / "sample_sops" / "clean_kyb_sop.md"
    clean_text = clean_sop_path.read_text(encoding="utf-8")
    
    G, issues, metrics = analyzer.analyze(clean_text)
    dead_ends = [i for i in issues if i.category == IssueCategory.DEAD_END_NODE]
    assert len(dead_ends) == 0
    assert metrics["is_valid_dag"] is True
