"""Deterministic Linter Engine orchestrator."""
import os
from typing import Optional
from src.schemas.audit import AuditReport, IssueSeverity
from src.linter.ambiguity_scanner import AmbiguityScanner
from src.linter.graph_analyzer import GraphAnalyzer
from src.linter.vendor_tagger import VendorTagger
from src.linter.scoring import ScoringCalculator
from src.llm.client import LLMClient


class LinterEngine:
    """Core Linter Engine that executes multi-stage static and semantic analysis on SOPs."""

    def __init__(self, enable_llm: bool = False):
        self.ambiguity_scanner = AmbiguityScanner()
        self.graph_analyzer = GraphAnalyzer()
        self.vendor_tagger = VendorTagger()
        self.scoring_calculator = ScoringCalculator()
        self.llm_client = LLMClient() if enable_llm else None

    def audit(self, text: str) -> AuditReport:
        """Executes full linting pipeline on SOP text."""
        # 1. Ambiguity & Subjectivity Scanning
        ambiguity_issues = self.ambiguity_scanner.scan(text)

        # 2. Graph & Topology Analysis
        G, graph_issues, graph_metrics = self.graph_analyzer.analyze(text)

        # 3. Vendor Integration & Spec Verification
        vendor_integrations, vendor_issues = self.vendor_tagger.analyze(text)

        # Combine all issues and deduplicate by ID
        all_issues_dict = {}
        for issue in ambiguity_issues + graph_issues + vendor_issues:
            if issue.id not in all_issues_dict:
                all_issues_dict[issue.id] = issue
        
        all_issues = list(all_issues_dict.values())

        # Sort issues: CRITICAL first, then WARNING, then INFO, then by line number
        severity_order = {IssueSeverity.CRITICAL: 0, IssueSeverity.WARNING: 1, IssueSeverity.INFO: 2}
        all_issues.sort(key=lambda x: (severity_order.get(x.severity, 3), x.line_number or 99999))

        # 4. Scoring & Summary
        readiness_score, status, category_breakdown, summary = self.scoring_calculator.calculate(
            all_issues, graph_metrics
        )

        critical_count = sum(1 for i in all_issues if i.severity == IssueSeverity.CRITICAL)
        warning_count = sum(1 for i in all_issues if i.severity == IssueSeverity.WARNING)
        info_count = sum(1 for i in all_issues if i.severity == IssueSeverity.INFO)

        return AuditReport(
            readiness_score=readiness_score,
            status=status,
            total_gaps_found=len(all_issues),
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            category_breakdown=category_breakdown,
            issues=all_issues,
            vendor_integrations=vendor_integrations,
            graph_metrics=graph_metrics,
            summary=summary
        )
