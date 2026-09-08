"""Rapidfolio DAG Graph Builder module."""
import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple
from src.schemas.dag import RapidfolioDAG, DAGNode, DAGEdge, HITLCheckpoint, NodeType
from src.schemas.sop import SOPStep
from src.linter.graph_analyzer import GraphAnalyzer


class DAGGraphBuilder:
    """Builds a structured Rapidfolio-compliant DAG from parsed SOP definitions."""

    def __init__(self):
        self.graph_analyzer = GraphAnalyzer()

    def build_dag(self, text: str, workflow_name: str = "KYB Commercial Entity Onboarding Workflow") -> RapidfolioDAG:
        """Translates SOP text into a fully qualified Rapidfolio DAG specification."""
        steps = self.graph_analyzer.parse_steps(text)
        nodes: List[DAGNode] = []
        edges: List[DAGEdge] = []
        hitl_checkpoints: List[HITLCheckpoint] = []

        node_ids_created = set()

        for step in steps:
            node_id = step.step_id
            node_ids_created.add(node_id)

            # Determine Node Type
            n_type = NodeType.RULE_EVALUATION
            if step.is_terminal:
                n_type = NodeType.TERMINAL_STATE
            elif step.step_type == "human_in_the_loop_gate" or "hitl" in node_id.lower() or "tier 2 review" in step.raw_text.lower():
                n_type = NodeType.HITL_GATE
            elif step.vendor or step.step_type == "api_call":
                n_type = NodeType.API_CALL

            # Payload defaults based on vendor/type
            payload: Dict[str, Any] = {}
            outputs: List[str] = []
            if step.vendor == "Persona":
                payload = {"inquiry_template_id": "itmpl_kyc_commercial", "fields": ["name", "ssn", "dob", "selfie"]}
                outputs = ["persona_score", "id_verified", "inquiry_status"]
            elif step.vendor == "ComplyAdvantage":
                payload = {"entity_name": "{{entity.legal_name}}", "ubos": "{{entity.ubos}}", "search_types": ["sanction", "pep", "adverse_media"]}
                outputs = ["ofac_sanctions_match", "pep_match", "adverse_media_match", "matches_count"]
            elif step.vendor == "Middesk":
                payload = {"business_name": "{{entity.legal_name}}", "tin": "{{entity.ein}}", "state": "{{entity.state_of_inc}}"}
                outputs = ["middesk.status", "middesk.standing", "filing_records"]
            elif step.vendor == "Marqeta":
                payload = {"user_token": "{{entity.primary_ubo_token}}", "card_product_token": "cp_commercial_corp"}
                outputs = ["marqeta.card_token", "marqeta.status"]
            elif step.vendor == "Slack":
                payload = {"channel": "#customer-onboarding-feed", "message": "KYB Onboarding Successful for {{entity.legal_name}}"}
                outputs = ["webhook_delivered"]
            elif step.vendor == "Jira":
                payload = {"project": "KYB_COMPLIANCE", "summary": "Manual Review Required for {{entity.legal_name}}"}
                outputs = ["compliance_officer.decision", "decision_notes"]

            # Retry policy
            retry_policy = None
            if n_type == NodeType.API_CALL:
                retry_policy = {
                    "max_attempts": 3,
                    "backoff_multiplier": 2.0,
                    "initial_interval_seconds": 2,
                    "retryable_status_codes": [500, 502, 503, 504]
                }

            # Build Node
            node = DAGNode(
                id=node_id,
                name=step.section + " - " + node_id.replace("_", " ").title(),
                type=n_type,
                vendor=step.vendor,
                description=step.raw_text[:120] + ("..." if len(step.raw_text) > 120 else ""),
                input_payload=payload,
                output_variables=outputs,
                timeout_seconds=step.timeout_seconds or (30 if n_type == NodeType.API_CALL else (86400 if n_type == NodeType.HITL_GATE else 5)),
                retry_policy=retry_policy
            )
            nodes.append(node)

            # Build HITL Checkpoint if applicable
            if n_type == NodeType.HITL_GATE:
                hitl_checkpoints.append(HITLCheckpoint(
                    node_id=node_id,
                    title=f"Manual Compliance Gate: {node_id}",
                    mandate_rationale="BSA/AML FinCEN mandatory review requirement for elevated risk or exception overrides.",
                    assigned_role="BSA/AML Compliance Officer",
                    sla_timeout_seconds=step.timeout_seconds or 86400,
                    possible_decisions=["APPROVED", "REJECTED", "ESCALATE_DIRECTOR"]
                ))

            # Extract Edge Transitions
            if step.targets:
                for target_id in step.targets:
                    # Create target node stub if not already existing
                    if target_id not in node_ids_created:
                        node_ids_created.add(target_id)
                        is_target_term = any(k in target_id.lower() for k in ["reject", "complete", "block", "alert", "fail"])
                        nodes.append(DAGNode(
                            id=target_id,
                            name=target_id.replace("_", " ").title(),
                            type=NodeType.TERMINAL_STATE if is_target_term else NodeType.RULE_EVALUATION,
                            description=f"Destination step for {target_id}",
                            input_payload={},
                            output_variables=[],
                            timeout_seconds=5
                        ))

                    is_fallback_edge = "error" in target_id.lower() or "fallback" in target_id.lower() or "reject" in target_id.lower()
                    edges.append(DAGEdge(
                        from_node=node_id,
                        to_node=target_id,
                        condition=f"evaluation_matches_{target_id.lower()}",
                        is_fallback=is_fallback_edge,
                        description=f"Transition from {node_id} to {target_id}"
                    ))

        # If sequential flow without explicit targets, generate linear transitions
        if len(edges) == 0 and len(nodes) > 1:
            for i in range(len(nodes) - 1):
                edges.append(DAGEdge(
                    from_node=nodes[i].id,
                    to_node=nodes[i + 1].id,
                    condition="payload.step_passed == true",
                    is_fallback=False,
                    description="Sequential step progression"
                ))

        # Construct full Rapidfolio DAG
        return RapidfolioDAG(
            workflow_id="wf_kyb_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
            version="2.4.0-RAPIDFOLIO",
            name=workflow_name,
            description="Compiled deterministic DAG state-machine specification for back-office banking orchestration.",
            target_platform="Rapidfolio Engine v2.4",
            compiled_at=datetime.now(timezone.utc).isoformat(),
            nodes=nodes,
            edges=edges,
            hitl_checkpoints=hitl_checkpoints,
            metadata={
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "hitl_count": len(hitl_checkpoints),
                "compiler_version": "Rapidfolio-SOP-Linter-v1.0"
            }
        )
