"""Ambiguity and subjectivity scanner module."""
import re
from typing import List
from src.schemas.audit import AuditIssue, IssueCategory, IssueSeverity
from src.linter.rules import AMBIGUITY_RULES


class AmbiguityScanner:
    """Scans SOP text for subjective language, vague human judgment calls, and undefined bounds."""

    def __init__(self, rules: List[dict] = None):
        self.rules = rules or AMBIGUITY_RULES

    def scan(self, text: str) -> List[AuditIssue]:
        """Scans the provided SOP text and returns detected ambiguity issues."""
        issues: List[AuditIssue] = []
        lines = text.splitlines()

        # Track already flagged spans to avoid duplicate issues on same line & rule
        flagged_keys = set()

        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") and len(stripped.split()) <= 4:
                # Skip top headers unless substantive content
                continue

            for rule in self.rules:
                pattern = rule["pattern"]
                match = re.search(pattern, stripped, re.IGNORECASE)
                if match:
                    key = f"{rule['id']}_{line_idx}"
                    if key in flagged_keys:
                        continue
                    flagged_keys.add(key)

                    # Extract context snippet around match
                    matched_text = match.group(0)
                    snippet = stripped

                    # Construct detailed issue
                    issue = AuditIssue(
                        id=f"{rule['id']}_L{line_idx}",
                        category=IssueCategory(rule["category"]),
                        severity=IssueSeverity(rule["severity"]),
                        line_number=line_idx,
                        quoted_text=snippet,
                        title=rule["title"],
                        description=rule["description"],
                        proposed_codification=rule["proposed_codification"],
                        vendor=None
                    )
                    issues.append(issue)

        return issues
