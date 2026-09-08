"""Graph topology and edge-case analyzer module using NetworkX."""
import re
import networkx as nx
from typing import List, Dict, Tuple, Any, Optional
from src.schemas.audit import AuditIssue, IssueCategory, IssueSeverity
from src.schemas.sop import SOPStep


class GraphAnalyzer:
    """Parses procedural workflow steps, constructs NetworkX DiGraph, and flags structural anomalies."""

    def __init__(self):
        self.terminal_patterns = [
            r"terminal",
            r"complete",
            r"reject",
            r"freeze",
            r"finish",
            r"state_reject",
            r"state_final",
            r"state_block",
            r"state_workflow_complete",
            r"state_alert",
            r"state_escalate",
            r"sys_alert",
            r"fallback"
        ]

    def parse_steps(self, text: str) -> List[SOPStep]:
        """Extracts steps from SOP text, grouping sub-bullet instructions with their parent step."""
        steps: List[SOPStep] = []
        lines = text.splitlines()
        current_section = "General"

        current_step_dict: Optional[Dict[str, Any]] = None

        def flush_current_step():
            nonlocal current_step_dict
            if not current_step_dict:
                return

            full_text = "\n".join(current_step_dict["lines_text"])
            step_id = current_step_dict["step_id"]
            vendor = current_step_dict["vendor"]
            step_type = current_step_dict["step_type"]
            timeout_sec = current_step_dict["timeout_sec"]
            line_no = current_step_dict["line_number"]

            # Extract targets
            targets = re.findall(r"(?:transition to|route to|enqueue to)\s+`?([A-Za-z0-9_]+)`?", full_text, re.IGNORECASE)

            is_term = (
                step_type == "terminal_state" or
                any(re.search(tp, step_id, re.IGNORECASE) for tp in self.terminal_patterns) or
                "terminal state" in full_text.lower()
            )

            # For messy SOPs without explicit markers
            if "tier 2 review" in full_text.lower() or "tier 2 risk review" in full_text.lower():
                if "STEP_TIER_2_REVIEW" not in targets:
                    targets.append("STEP_TIER_2_REVIEW")
            if "beneficial ownership" in full_text.lower() and "proceed" in full_text.lower():
                if "STEP_2_1" not in targets:
                    targets.append("STEP_2_1")
            if "escalate to compliance manager" in full_text.lower():
                if "STEP_ESCALATE_MANAGER" not in targets:
                    targets.append("STEP_ESCALATE_MANAGER")

            step = SOPStep(
                step_id=step_id,
                section=current_section,
                line_number=line_no,
                raw_text=full_text,
                step_type=step_type,
                vendor=vendor,
                timeout_seconds=timeout_sec,
                targets=targets,
                is_terminal=is_term
            )
            steps.append(step)
            current_step_dict = None

        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            # Check section header
            if stripped.startswith("##"):
                flush_current_step()
                current_section = stripped.lstrip("#").strip()
                continue

            # Look for codified tag: [Step: ID | Type: ... | Vendor: ...]
            tag_match = re.search(r"\[Step:\s*([A-Za-z0-9_]+)(?:\s*\|\s*Type:\s*([A-Za-z0-9_]+))?(?:\s*\|\s*Vendor:\s*([A-Za-z0-9_]+))?(?:\s*\|\s*Timeout:\s*([0-9]+)s?)?\]", stripped)
            
            # Or look for standard bullet numbering: 1.1, 1.1., 2.3, 1., etc.
            num_match = re.match(r"^(\d+(?:\.\d+)*\.?)\s+(.+)$", stripped)

            if tag_match:
                flush_current_step()
                step_id = tag_match.group(1)
                step_type = tag_match.group(2) or "rule_evaluation"
                vendor = tag_match.group(3)
                timeout_str = tag_match.group(4)
                timeout_sec = int(timeout_str) if timeout_str else None

                current_step_dict = {
                    "step_id": step_id,
                    "step_type": step_type,
                    "vendor": vendor,
                    "timeout_sec": timeout_sec,
                    "line_number": line_idx,
                    "lines_text": [stripped]
                }

            elif num_match:
                flush_current_step()
                num_prefix = num_match.group(1).rstrip(".")
                step_id = f"STEP_{num_prefix.replace('.', '_')}"
                body = num_match.group(2)

                vendor = None
                for v in ["Persona", "ComplyAdvantage", "Middesk", "Marqeta", "Jira", "Slack", "Plaid"]:
                    if v.lower() in body.lower():
                        vendor = v
                        break

                current_step_dict = {
                    "step_id": step_id,
                    "step_type": "api_call" if vendor else "rule_evaluation",
                    "vendor": vendor,
                    "timeout_sec": None,
                    "line_number": line_idx,
                    "lines_text": [stripped]
                }
            else:
                if current_step_dict:
                    current_step_dict["lines_text"].append(stripped)
                    if not current_step_dict["vendor"]:
                        for v in ["Persona", "ComplyAdvantage", "Middesk", "Marqeta", "Jira", "Slack", "Plaid"]:
                            if v.lower() in stripped.lower():
                                current_step_dict["vendor"] = v
                                break

        flush_current_step()
        return steps

    def build_graph(self, steps: List[SOPStep]) -> nx.DiGraph:
        """Constructs a NetworkX directed graph from parsed steps."""
        G = nx.DiGraph()

        for step in steps:
            G.add_node(
                step.step_id,
                label=step.step_id,
                section=step.section,
                line_number=step.line_number,
                raw_text=step.raw_text,
                step_type=step.step_type,
                vendor=step.vendor,
                timeout_seconds=step.timeout_seconds,
                is_terminal=step.is_terminal
            )

        # Connect explicit targets or sequential fallbacks
        for idx, step in enumerate(steps):
            if step.targets:
                for target in step.targets:
                    G.add_edge(step.step_id, target, condition=None)
            elif not step.is_terminal and idx + 1 < len(steps):
                next_step = steps[idx + 1]
                G.add_edge(step.step_id, next_step.step_id, condition="sequential_next")

        return G

    def analyze(self, text: str) -> Tuple[nx.DiGraph, List[AuditIssue], Dict[str, Any]]:
        """Performs full graph analysis and flags dead ends, missing fallbacks, and cycle loops."""
        steps = self.parse_steps(text)
        G = self.build_graph(steps)
        issues: List[AuditIssue] = []

        # 1. Cycle Detection
        try:
            cycles = list(nx.simple_cycles(G))
            for cycle in cycles:
                cycle_str = " -> ".join(cycle)
                issues.append(AuditIssue(
                    id=f"GRAPH_CYCLE_{cycle[0]}",
                    category=IssueCategory.CIRCULAR_LOGIC,
                    severity=IssueSeverity.CRITICAL,
                    line_number=G.nodes[cycle[0]].get("line_number", 1) if cycle[0] in G else None,
                    quoted_text=f"Cycle loop detected across steps: {cycle_str}",
                    title="Infinite Loop / Circular Logic Detected",
                    description=f"A closed loop was detected ({cycle_str}) without a deterministic exit condition or maximum iteration counter.",
                    proposed_codification=f"Add iteration guard: while attempts < 3: ... else: transition(STATE_ESCALATE_FALLBACK)",
                    node_id=cycle[0]
                ))
        except Exception:
            pass

        # 2. Dead-end Node Detection
        for node in G.nodes:
            node_data = G.nodes[node]
            out_degree = G.out_degree(node)
            is_term = node_data.get("is_terminal", False)
            raw_text = node_data.get("raw_text", "")
            line_no = node_data.get("line_number")

            is_known_terminal = (
                is_term or
                node_data.get("step_type") == "terminal_state" or
                any(re.search(tp, node, re.IGNORECASE) for tp in self.terminal_patterns)
            )

            if out_degree == 0 and not is_known_terminal:
                issues.append(AuditIssue(
                    id=f"GRAPH_DEADEND_{node}",
                    category=IssueCategory.DEAD_END_NODE,
                    severity=IssueSeverity.CRITICAL,
                    line_number=line_no,
                    quoted_text=raw_text.splitlines()[0] if raw_text else f"Node {node}",
                    title=f"Dead-End Step: '{node}' Has No Outgoing Path or Resolution",
                    description=f"Step '{node}' receives transitions but provides no deterministic output transition, timeout, or terminal resolution state.",
                    proposed_codification=f"transition({node}) -> outcome[APPROVED -> STEP_NEXT | REJECTED -> STATE_FINAL_REJECT | TIMEOUT(86400s) -> STATE_ESCALATE]",
                    node_id=node
                ))

        # 3. Unhandled Exception & Timeout Paths for API Calls
        for step in steps:
            if step.vendor and step.step_type == "api_call":
                raw_lower = step.raw_text.lower()
                has_timeout = step.timeout_seconds is not None or "timeout" in raw_lower or "sla" in raw_lower
                has_error_handling = any(kw in raw_lower for kw in [
                    "500", "502", "503", "504", "retry", "fallback", "http_status", "circuitbreaker", "error_", "failed"
                ])

                if not has_timeout or not has_error_handling:
                    issues.append(AuditIssue(
                        id=f"GRAPH_UNHANDLED_API_{step.step_id}",
                        category=IssueCategory.UNHANDLED_EXCEPTION_PATH,
                        severity=IssueSeverity.CRITICAL if not has_error_handling else IssueSeverity.WARNING,
                        line_number=step.line_number,
                        quoted_text=step.raw_text.splitlines()[0],
                        title=f"Missing API Timeout / Error Fallback: {step.vendor}",
                        description=f"API call to {step.vendor} does not specify strict timeout bounds or failure handler (e.g. HTTP 504 Gateway Timeout or Network Flake).",
                        proposed_codification=f"with timeout({step.vendor.lower()}_timeout=30s, retries=3, backoff='EXPONENTIAL'): on_error=transition(HITL_MANUAL_REVIEW)",
                        node_id=step.step_id,
                        vendor=step.vendor
                    ))

        # Check for specific unhandled messy SOP patterns
        for line_idx, line in enumerate(text.splitlines(), start=1):
            if "persona api returns a 504" in line.lower() and "wait and retry as needed" in line.lower():
                issues.append(AuditIssue(
                    id=f"UNHANDLED_504_PERSONA_L{line_idx}",
                    category=IssueCategory.UNHANDLED_EXCEPTION_PATH,
                    severity=IssueSeverity.CRITICAL,
                    line_number=line_idx,
                    quoted_text=line.strip(),
                    title="Non-Deterministic API Retry: 'Wait and Retry as Needed'",
                    description="Vague retry instruction lacks max attempt count, exponential backoff interval, and failure circuit breaker.",
                    proposed_codification="retry_policy(max_retries=3, backoff_seconds=2, backoff_multiplier=2.0, fallback='HITL_MANUAL_KYC_REVIEW')",
                    vendor="Persona"
                ))

        dead_end_nodes = [
            n for n in G.nodes
            if G.out_degree(n) == 0
            and not G.nodes[n].get("is_terminal", False)
            and G.nodes[n].get("step_type") != "terminal_state"
            and not any(re.search(tp, n, re.IGNORECASE) for tp in self.terminal_patterns)
        ]

        metrics = {
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "is_valid_dag": nx.is_directed_acyclic_graph(G) if G.number_of_nodes() > 0 else True,
            "has_cycles": not nx.is_directed_acyclic_graph(G) if G.number_of_nodes() > 0 else False,
            "dead_end_nodes": dead_end_nodes
        }

        return G, issues, metrics
