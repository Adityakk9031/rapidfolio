"""Rapidfolio DAG state-machine specification schemas."""
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    API_CALL = "api_call"
    RULE_EVALUATION = "rule_evaluation"
    HITL_GATE = "human_in_the_loop_gate"
    TERMINAL_STATE = "terminal_state"


class DAGNode(BaseModel):
    """A single execution node in the Rapidfolio DAG workflow."""
    id: str = Field(..., description="Unique node ID, e.g. STEP_PERSONA_KYC")
    name: str = Field(..., description="Human-readable step name")
    type: NodeType = Field(..., description="Type of node execution")
    vendor: Optional[str] = Field(None, description="External vendor API if applicable")
    description: str = Field(..., description="Functional purpose of this step")
    input_payload: Dict[str, Any] = Field(default_factory=dict, description="Required payload parameters")
    output_variables: List[str] = Field(default_factory=list, description="Variables produced by node")
    timeout_seconds: Optional[int] = Field(None, description="Maximum execution SLA timeout")
    retry_policy: Optional[Dict[str, Any]] = Field(None, description="Retry configuration on network failure")


class DAGEdge(BaseModel):
    """A directed transition between two workflow nodes."""
    from_node: str = Field(..., description="Source node ID")
    to_node: str = Field(..., description="Destination node ID")
    condition: Optional[str] = Field(None, description="Boolean conditional logic string")
    is_fallback: bool = Field(False, description="Whether this transition is an error/timeout fallback")
    description: Optional[str] = Field(None, description="Human description of condition")


class HITLCheckpoint(BaseModel):
    """A human compliance gate with explicit SLA and decision outcomes."""
    node_id: str = Field(..., description="Target node ID")
    title: str = Field(..., description="Checkpoint name")
    mandate_rationale: str = Field(..., description="Regulatory or compliance justification")
    assigned_role: str = Field(..., description="Authorized role, e.g., Senior AML Analyst")
    sla_timeout_seconds: int = Field(..., description="SLA duration before escalation")
    possible_decisions: List[str] = Field(default_factory=list, description="Explicit allowable outcomes")


class RapidfolioDAG(BaseModel):
    """Full Rapidfolio-compatible state-machine DAG specification."""
    workflow_id: str = Field(..., description="Standardized workflow ID")
    version: str = Field(..., description="Workflow version string")
    name: str = Field(..., description="Workflow title")
    description: str = Field(..., description="Workflow summary")
    target_platform: str = Field("Rapidfolio Engine v2.4", description="Target execution runtime")
    compiled_at: str = Field(..., description="ISO 8601 timestamp of compilation")
    nodes: List[DAGNode] = Field(default_factory=list)
    edges: List[DAGEdge] = Field(default_factory=list)
    hitl_checkpoints: List[HITLCheckpoint] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
