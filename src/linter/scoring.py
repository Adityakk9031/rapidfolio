"""Scoring calculator module for Deterministic Readiness Score."""
from typing import List, Dict, Any, Tuple
from src.schemas.audit import AuditIssue, IssueSeverity


class ScoringCalculator:
    """Calculates weighted Deterministic Readiness Score (0-100%) based on detected gaps."""

    def __init__(
        self,
        critical_penalty: int = 6,
        warning_penalty: int = 2,
        info_penalty: int = 1
    ):
        self.critical_penalty = critical_penalty
        self.warning_penalty = warning_penalty
        self.info_penalty = info_penalty

    def calculate(self, issues: List[AuditIssue], metrics: Dict[str, Any]) -> Tuple[int, str, Dict[str, int], str]:
        """Calculates score, status, category breakdown, and executive summary."""
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        warning_count = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)
        info_count = sum(1 for i in issues if i.severity == IssueSeverity.INFO)

        # Base deduction calculation
        deduction = (
            (critical_count * self.critical_penalty) +
            (warning_count * self.warning_penalty) +
            (info_count * self.info_penalty)
        )

        # Graph specific penalties
        if metrics.get("has_cycles", False):
            deduction += 15
        if metrics.get("dead_end_nodes"):
            deduction += min(len(metrics["dead_end_nodes"]) * 4, 12)

        raw_score = max(0, 100 - deduction)
        readiness_score = int(min(100, raw_score))

        # Status categorization
        if readiness_score >= 90 and critical_count == 0:
            status = "READY_FOR_COMPILATION"
        elif readiness_score >= 60:
            status = "REQUIRES_REMEDIATION"
        else:
            status = "CRITICAL_BLOCKERS"

        # Breakdown by category
        category_breakdown: Dict[str, int] = {}
        for issue in issues:
            cat_name = issue.category.value if hasattr(issue.category, "value") else str(issue.category)
            category_breakdown[cat_name] = category_breakdown.get(cat_name, 0) + 1

        # Formulate executive summary
        if status == "READY_FOR_COMPILATION":
            summary = (
                f"SOP passes deterministic pre-flight checks with a score of {readiness_score}%. "
                "All procedural branches, SLA timeouts, API error fallbacks, and human-in-the-loop gates "
                "are formally declared and ready for Rapidfolio DAG compilation."
            )
        elif status == "REQUIRES_REMEDIATION":
            summary = (
                f"SOP scored {readiness_score}% with {len(issues)} gaps identified ({critical_count} critical, {warning_count} warnings). "
                "Remediation is required to resolve ambiguous phrases and unhandled fallback conditions before automated DAG execution."
            )
        else:
            summary = (
                f"SOP scored {readiness_score}% - NOT READY FOR COMPILATION ({critical_count} critical blockers, {warning_count} warnings). "
                "Document contains non-deterministic human judgment calls ('sketchy', 'analyst discretion'), dead-end escalations, "
                "or unhandled vendor API timeout states that will cause runtime workflow halts."
            )

        return readiness_score, status, category_breakdown, summary
