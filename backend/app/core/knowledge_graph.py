"""Lightweight GraphRAG scaffold for the scientific knowledge base."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import DATA_DIR
from app.core.schemas import RetrievedChunk

try:
    import networkx as nx
except Exception:  # pragma: no cover
    nx = None


_SEED_GRAPH: dict[str, dict[str, Any]] = {
    "quantum electrodynamics": {
        "aliases": ["qed", "quantum electrodynamics", "renormalization"],
        "summary": (
            "QED describes how light and charged particles interact. It is the "
            "place where Feynman diagrams become a practical bookkeeping tool."
        ),
        "neighbors": ["feynman diagrams", "path integrals"],
    },
    "feynman diagrams": {
        "aliases": ["feynman diagram", "feynman diagrams", "diagrams"],
        "summary": (
            "Feynman diagrams are visual accounting devices for terms in a "
            "calculation, not tiny photographs of particles moving in space."
        ),
        "neighbors": ["quantum electrodynamics", "path integrals"],
    },
    "path integrals": {
        "aliases": ["path integral", "path integrals", "sum over histories"],
        "summary": (
            "The path integral picture says the amplitude comes from adding "
            "contributions from every possible path, with phases deciding what survives."
        ),
        "neighbors": ["quantum electrodynamics", "double-slit experiment"],
    },
    "double-slit experiment": {
        "aliases": ["double slit", "double-slit", "two slit", "interference"],
        "summary": (
            "The double-slit experiment shows interference: alternatives combine "
            "as amplitudes first, then probabilities after squaring."
        ),
        "neighbors": ["path integrals", "quantum mechanics"],
    },
    "quantum mechanics": {
        "aliases": ["quantum mechanics", "quantum theory", "wavefunction"],
        "summary": (
            "Quantum mechanics replaces certain classical certainties with "
            "amplitudes, phases, and experimentally tested probability rules."
        ),
        "neighbors": ["double-slit experiment", "path integrals"],
    },
    "los alamos": {
        "aliases": ["los alamos", "manhattan project", "atomic bomb"],
        "summary": (
            "Los Alamos was a wartime scientific project, mixing technical work, "
            "moral pressure, secrecy, and unusually concentrated talent."
        ),
        "neighbors": ["manhattan project", "teaching"],
    },
    "teaching": {
        "aliases": ["teaching", "lectures", "feynman lectures", "caltech"],
        "summary": (
            "The teaching style starts with the simplest honest picture and only "
            "then builds the formal machinery."
        ),
        "neighbors": ["quantum mechanics", "feynman lectures"],
    },
}


class KnowledgeGraphStore:
    """NetworkX-backed concept graph with a JSON extension point."""

    def __init__(self, graph_path: Path | None = None):
        self.graph_path = graph_path or (Path(DATA_DIR) / "knowledge_graph.json")
        self.graph = self._load_graph()

    def query(self, query: str, top_k: int = 4) -> list[RetrievedChunk]:
        terms = set(_tokenize(query))
        scored: list[tuple[float, str]] = []

        for node_id, data in self._nodes():
            node_terms = set(_tokenize(node_id))
            for alias in data.get("aliases", []):
                node_terms.update(_tokenize(alias))
            overlap = len(terms & node_terms)
            if overlap:
                scored.append((float(overlap), node_id))

        scored.sort(reverse=True)
        chunks: list[RetrievedChunk] = []
        for score, node_id in scored[:top_k]:
            data = self._node_data(node_id)
            neighbor_text = self._neighbor_text(node_id)
            text = f"{data.get('summary', '')} Related concepts: {neighbor_text}."
            chunks.append(
                RetrievedChunk(
                    text=text.strip(),
                    source=f"knowledge_graph:{node_id}",
                    type="knowledge",
                    score=score,
                    metadata={"graph_node": node_id, "retrieval": "graphrag"},
                )
            )
        return chunks

    def _load_graph(self):
        graph_data = _SEED_GRAPH
        if self.graph_path.exists():
            try:
                graph_data = json.loads(self.graph_path.read_text(encoding="utf-8"))
            except Exception as exc:
                print(f"[KnowledgeGraph] Could not load graph JSON, using seed graph: {exc}")

        if nx is None:
            return graph_data

        graph = nx.Graph()
        for node_id, data in graph_data.items():
            graph.add_node(node_id, **data)
            for neighbor in data.get("neighbors", []):
                graph.add_edge(node_id, neighbor)
        return graph

    def _nodes(self):
        if nx is None:
            return self.graph.items()
        return ((node, self.graph.nodes[node]) for node in self.graph.nodes)

    def _node_data(self, node_id: str) -> dict[str, Any]:
        if nx is None:
            return self.graph.get(node_id, {})
        return dict(self.graph.nodes[node_id])

    def _neighbor_text(self, node_id: str) -> str:
        if nx is None:
            neighbors = self.graph.get(node_id, {}).get("neighbors", [])
        else:
            neighbors = list(self.graph.neighbors(node_id))
        return ", ".join(str(item) for item in neighbors) or "none yet"


def _tokenize(text: str) -> list[str]:
    return [token for token in text.lower().replace("-", " ").split() if len(token) > 2]
