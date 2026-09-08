"""DAG Exporter and NetworkX validation module."""
import json
import networkx as nx
from typing import Dict, Any, Tuple
from src.schemas.dag import RapidfolioDAG
from src.compiler.graph_builder import DAGGraphBuilder


class DAGExporter:
    """Exports and validates Rapidfolio-compliant DAG state-machine models."""

    def __init__(self):
        self.builder = DAGGraphBuilder()

    def compile(self, sop_text: str, title: str = "KYB Commercial Entity Onboarding Workflow") -> Tuple[RapidfolioDAG, str, Dict[str, Any]]:
        """Compiles SOP text into a validated Rapidfolio DAG and returns the DAG model, JSON string, and validation metrics."""
        dag = self.builder.build_dag(sop_text, workflow_name=title)

        # Build NetworkX representation to strictly validate DAG integrity
        G = nx.DiGraph()
        for node in dag.nodes:
            G.add_node(node.id, type=node.type.value if hasattr(node.type, 'value') else node.type)
        for edge in dag.edges:
            G.add_edge(edge.from_node, edge.to_node, condition=edge.condition)

        is_acyclic = nx.is_directed_acyclic_graph(G)
        has_cycles = not is_acyclic

        metrics = {
            "is_valid_dag": is_acyclic,
            "has_cycles": has_cycles,
            "node_count": len(dag.nodes),
            "edge_count": len(dag.edges),
            "hitl_gate_count": len(dag.hitl_checkpoints),
            "root_nodes": [n for n in G.nodes if G.in_degree(n) == 0],
            "terminal_nodes": [n for n in G.nodes if G.out_degree(n) == 0]
        }

        # Generate JSON representation
        json_output = dag.model_dump_json(indent=2)
        return dag, json_output, metrics
