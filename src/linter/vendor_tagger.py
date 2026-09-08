"""Vendor integration tagger and specification validator module."""
import re
from typing import List, Tuple
from src.schemas.audit import VendorIntegration, AuditIssue, IssueCategory, IssueSeverity
from src.linter.rules import VENDOR_SIGNATURES


class VendorTagger:
    """Detects financial back-office API integrations and validates specification completeness."""

    def __init__(self, signatures: dict = None):
        self.signatures = signatures or VENDOR_SIGNATURES

    def analyze(self, text: str) -> Tuple[List[VendorIntegration], List[AuditIssue]]:
        """Identifies vendor mentions and evaluates whether SLA, error codes, and payloads are declared."""
        integrations: List[VendorIntegration] = []
        issues: List[AuditIssue] = []

        # Split text into step blocks (separated by numbered items or tags)
        lines = text.splitlines()

        for vendor_name, spec in self.signatures.items():
            pattern = spec["pattern"]
            matches_found = []

            for line_idx, line in enumerate(lines, start=1):
                if re.search(pattern, line, re.IGNORECASE):
                    # Gather surrounding context block (±5 lines)
                    start_ctx = max(0, line_idx - 2)
                    end_ctx = min(len(lines), line_idx + 8)
                    block_text = "\n".join(lines[start_ctx:end_ctx])
                    matches_found.append((line_idx, line.strip(), block_text))

            if matches_found:
                first_line_no, first_snippet, _ = matches_found[0]
                full_vendor_context = "\n".join([m[2] for m in matches_found])

                has_timeout = bool(re.search(r"\b(timeout(?:\s*:\s*|\s+is\s+)?(\d+)s?|sla(?:\s+timeout)?(?:\s*:\s*|\s+of\s+)?(\d+))\b", full_vendor_context, re.IGNORECASE))
                has_error_handler = any(err in full_vendor_context.lower() for err in [
                    "500", "502", "503", "504", "retry", "fallback", "http_status", "circuitbreaker", "error_", "failed"
                ])
                has_payload_spec = any(kw in full_vendor_context.lower() for kw in [
                    "payload", "json", "post /", "get /", "parameters", "fields:", "template_id"
                ])

                missing_specs = []
                if not has_timeout:
                    missing_specs.append("Missing SLA Timeout Definition")
                if not has_error_handler:
                    missing_specs.append("Missing HTTP Error Code / Network Retry Policy")
                if not has_payload_spec and spec["type"] == "api_call":
                    missing_specs.append("Missing Input/Output Payload Schema")

                integration = VendorIntegration(
                    vendor_name=vendor_name,
                    detected_in_step=f"Line {first_line_no}",
                    operation=spec["domain"],
                    has_timeout=has_timeout,
                    has_error_handler=has_error_handler,
                    missing_specs=missing_specs
                )
                integrations.append(integration)

                if missing_specs:
                    issues.append(AuditIssue(
                        id=f"VENDOR_SPEC_{vendor_name.upper()}_L{first_line_no}",
                        category=IssueCategory.VENDOR_SPEC_GAP,
                        severity=IssueSeverity.WARNING,
                        line_number=first_line_no,
                        quoted_text=first_snippet,
                        title=f"Underspecified Vendor Integration: {vendor_name}",
                        description=f"Integration with {vendor_name} ({spec['domain']}) lacks formal runtime parameters: {', '.join(missing_specs)}.",
                        proposed_codification=f"vendor_call('{vendor_name}', endpoint='POST /v1', payload={spec['recommended_payload']}, timeout={spec['required_timeout_seconds']}s, fallback='{spec['default_fallback']}')",
                        vendor=vendor_name
                    ))

        return integrations, issues
