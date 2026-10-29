import os
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
from dataclasses import dataclass, field, asdict

from collective.weights import RelationshipWeights, operational_engine
from collective.config import collective_config

logger = logging.getLogger("research_duel.collective.graph")

NODE_LABELS = {
    "Problem", "Hypothesis", "Evidence", "Source", "Conclusion",
    "Contradiction", "Dependency", "Experiment", "Result", "Agent",
    "Generation", "Strategy", "ReasoningPath"
}

RELATION_TYPES = {
    "SUPPORTS", "REFUTES", "CONTRADICTS", "DEPENDS_ON", "INVESTIGATES",
    "PRODUCED_BY", "VERIFIED_BY", "CONSUMES", "TESTS", "DERIVED_FROM", "ADDRESSES"
}

@dataclass
class KnowledgeNode:
    id: str
    label: str
    title: str
    description: str = ""
    provenance: str = "system" # Agente gerador ou fonte
    version: int = 1
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    validation_status: str = "PROPOSED" # PROPOSED, INVESTIGATING, VERIFIED, REFUTED, CONTRADICTORY
    epistemic_class: str = "HYPOTHESIS" # PROBLEM, HYPOTHESIS, EMPIRICAL_FACT, FALSIFIED, CONTRADICTION
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "title": self.title,
            "description": self.description,
            "provenance": self.provenance,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "validation_status": self.validation_status,
            "epistemic_class": self.epistemic_class,
            "properties": self.properties
        }

@dataclass
class KnowledgeEdge:
    id: str
    source_id: str
    target_id: str
    relation_type: str
    weights: RelationshipWeights = field(default_factory=RelationshipWeights)
    provenance: str = "system"
    version: int = 1
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "weights": self.weights.to_dict(),
            "provenance": self.provenance,
            "version": self.version,
            "created_at": self.created_at,
            "metadata": self.metadata
        }


class EmbeddedGraphEngine:
    """
    Grafo de Conhecimento Transacional Integrado (Memória Persistente em JSON / SQLite).
    Oferece compatibilidade com o modelo de dados Neo4j mesmo na ausência temporária do servidor.
    """
    def __init__(self, state_file: Optional[str] = None):
        self.state_file = Path(state_file or collective_config.knowledge_graph.state_file)
        self.nodes: Dict[str, KnowledgeNode] = {}
        self.edges: Dict[str, KnowledgeEdge] = {}
        self.adjacency: Dict[str, Set[str]] = {}       # node_id -> {edge_ids}
        self.reverse_adjacency: Dict[str, Set[str]] = {} # target_id -> {edge_ids}
        self.load_state()

    def add_node(self, node: KnowledgeNode) -> bool:
        if node.id in self.nodes:
            existing = self.nodes[node.id]
            existing.version += 1
            existing.updated_at = time.time()
            existing.title = node.title or existing.title
            existing.description = node.description or existing.description
            existing.validation_status = node.validation_status or existing.validation_status
            existing.properties.update(node.properties)
            self._save_state()
            return True

        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = set()
        if node.id not in self.reverse_adjacency:
            self.reverse_adjacency[node.id] = set()
        self._save_state()
        return True

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        return self.nodes.get(node_id)

    def add_edge(self, edge: KnowledgeEdge) -> bool:
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            logger.warning(f"[GraphEngine] Aresta inválida: nós {edge.source_id} ou {edge.target_id} não existem.")
            return False

        self.edges[edge.id] = edge
        self.adjacency.setdefault(edge.source_id, set()).add(edge.id)
        self.reverse_adjacency.setdefault(edge.target_id, set()).add(edge.id)
        self._save_state()
        return True

    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        return self.edges.get(edge_id)

    def find_nodes(self, label: Optional[str] = None, validation_status: Optional[str] = None) -> List[KnowledgeNode]:
        res = []
        for n in self.nodes.values():
            if label and n.label != label:
                continue
            if validation_status and n.validation_status != validation_status:
                continue
            res.append(n)
        return res

    def get_connected_subgraph(
        self,
        center_node_ids: List[str],
        max_depth: int = 2,
        min_weight_score: float = 0.05
    ) -> Tuple[List[KnowledgeNode], List[KnowledgeEdge]]:
        """Extrai um subgrafo contextual ao redor dos nós centrais ponderado por arestas."""
        visited_nodes: Set[str] = set(center_node_ids)
        visited_edges: Set[str] = set()
        queue: List[Tuple[str, int]] = [(nid, 0) for nid in center_node_ids if nid in self.nodes]

        while queue:
            curr_id, depth = queue.pop(0)
            if depth >= max_depth:
                continue

            # Arestas de saída e de entrada
            all_edge_ids = self.adjacency.get(curr_id, set()) | self.reverse_adjacency.get(curr_id, set())
            for eid in all_edge_ids:
                edge = self.edges.get(eid)
                if not edge:
                    continue
                score = edge.weights.calculate_decision_score()
                if score < min_weight_score:
                    continue

                visited_edges.add(eid)
                neighbor_id = edge.target_id if edge.source_id == curr_id else edge.source_id
                if neighbor_id not in visited_nodes and neighbor_id in self.nodes:
                    visited_nodes.add(neighbor_id)
                    queue.append((neighbor_id, depth + 1))

        nodes = [self.nodes[nid] for nid in visited_nodes if nid in self.nodes]
        edges = [self.edges[eid] for eid in visited_edges if eid in self.edges]
        return nodes, edges

    def record_contradiction(
        self,
        hypothesis_a_id: str,
        hypothesis_b_id: str,
        reason: str,
        detected_by: str,
        generation_id: str
    ) -> str:
        """Registra explicitamente uma contradição no grafo entre duas hipóteses."""
        c_id = f"contra_{int(time.time()*1000)}_{abs(hash(hypothesis_a_id + hypothesis_b_id)) % 10000}"
        contra_node = KnowledgeNode(
            id=c_id,
            label="Contradiction",
            title=f"Contradição entre {hypothesis_a_id} e {hypothesis_b_id}",
            description=reason,
            provenance=detected_by,
            validation_status="OPEN",
            epistemic_class="CONTRADICTION",
            properties={"gen_id": generation_id, "nodes": [hypothesis_a_id, hypothesis_b_id]}
        )
        self.add_node(contra_node)

        # Atualiza status das hipóteses para CONTRADICTORY
        for hid in (hypothesis_a_id, hypothesis_b_id):
            if hid in self.nodes:
                self.nodes[hid].validation_status = "CONTRADICTORY"

        # Conecta as arestas
        e1 = KnowledgeEdge(
            id=f"e_{c_id}_to_{hypothesis_a_id}",
            source_id=c_id,
            target_id=hypothesis_a_id,
            relation_type="CONTRADICTS",
            weights=RelationshipWeights(weight_semantic=0.9, weight_epistemic=0.8, weight_operational=0.1)
        )
        e2 = KnowledgeEdge(
            id=f"e_{c_id}_to_{hypothesis_b_id}",
            source_id=c_id,
            target_id=hypothesis_b_id,
            relation_type="CONTRADICTS",
            weights=RelationshipWeights(weight_semantic=0.9, weight_epistemic=0.8, weight_operational=0.1)
        )
        self.add_edge(e1)
        self.add_edge(e2)
        return c_id

    def load_state(self):
        if not self.state_file.exists():
            return
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for nd in data.get("nodes", []):
                node = KnowledgeNode(**nd)
                self.nodes[node.id] = node
                self.adjacency[node.id] = set()
                self.reverse_adjacency[node.id] = set()

            for ed in data.get("edges", []):
                weights_dict = ed.pop("weights", {})
                edge = KnowledgeEdge(
                    weights=RelationshipWeights.from_dict(weights_dict),
                    **ed
                )
                self.edges[edge.id] = edge
                self.adjacency.setdefault(edge.source_id, set()).add(edge.id)
                self.reverse_adjacency.setdefault(edge.target_id, set()).add(edge.id)

            logger.info(f"[GraphEngine] Estado restaurado: {len(self.nodes)} nós e {len(self.edges)} arestas de {self.state_file.name}.")
        except Exception as e:
            logger.error(f"[GraphEngine] Erro ao carregar estado: {e}")

    def _save_state(self):
        try:
            data = {
                "nodes": [n.to_dict() for n in self.nodes.values()],
                "edges": [e.to_dict() for e in self.edges.values()],
                "saved_at": time.time()
            }
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[GraphEngine] Erro ao salvar estado: {e}")


class KnowledgeGraphManager:
    """
    Controlador Mestre do Grafo de Conhecimento (Neo4j com Fallback Embutido).
    """
    def __init__(self):
        self.config = collective_config.knowledge_graph
        self.embedded = EmbeddedGraphEngine(self.config.state_file)
        self.neo4j_driver = None
        self.is_neo4j_online = False
        self._try_connect_neo4j()

    def _try_connect_neo4j(self) -> bool:
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.user, self.config.password),
                connection_timeout=2.0
            )
            # Testa conexão
            with driver.session(database=self.config.database) as session:
                session.run("RETURN 1 as test")
            self.neo4j_driver = driver
            self.is_neo4j_online = True
            logger.info("✅ Conexão ativa estabelecida com Neo4j Server!")
            return True
        except Exception as e:
            self.is_neo4j_online = False
            self.neo4j_driver = None
            logger.info(f"[GraphManager] Neo4j Bolt offline ({e}). Operando via Embedded Graph Engine resiliente.")
            return False

    def add_node(self, node: KnowledgeNode) -> bool:
        ok = self.embedded.add_node(node)
        if self.is_neo4j_online and self.neo4j_driver:
            try:
                with self.neo4j_driver.session(database=self.config.database) as session:
                    cypher = f"""
                    MERGE (n:{node.label} {{id: $id}})
                    SET n.title = $title,
                        n.description = $description,
                        n.provenance = $provenance,
                        n.version = $version,
                        n.validation_status = $validation_status,
                        n.epistemic_class = $epistemic_class,
                        n.updated_at = $updated_at
                    """
                    session.run(
                        cypher,
                        id=node.id,
                        title=node.title,
                        description=node.description,
                        provenance=node.provenance,
                        version=node.version,
                        validation_status=node.validation_status,
                        epistemic_class=node.epistemic_class,
                        updated_at=node.updated_at
                    )
            except Exception as e:
                logger.warning(f"[GraphManager] Falha ao sincronizar nó com Neo4j: {e}")
        return ok

    def add_edge(self, edge: KnowledgeEdge) -> bool:
        ok = self.embedded.add_edge(edge)
        if self.is_neo4j_online and self.neo4j_driver:
            try:
                with self.neo4j_driver.session(database=self.config.database) as session:
                    cypher = f"""
                    MATCH (s {{id: $source_id}}), (t {{id: $target_id}})
                    MERGE (s)-[r:{edge.relation_type} {{id: $id}}]->(t)
                    SET r.weight_semantic = $weight_semantic,
                        r.weight_epistemic = $weight_epistemic,
                        r.weight_operational = $weight_operational,
                        r.uncertainty = $uncertainty,
                        r.provenance = $provenance,
                        r.updated_at = $updated_at
                    """
                    session.run(
                        cypher,
                        id=edge.id,
                        source_id=edge.source_id,
                        target_id=edge.target_id,
                        weight_semantic=edge.weights.weight_semantic,
                        weight_epistemic=edge.weights.weight_epistemic,
                        weight_operational=edge.weights.weight_operational,
                        uncertainty=edge.weights.uncertainty,
                        provenance=edge.provenance,
                        updated_at=edge.weights.updated_at
                    )
            except Exception as e:
                logger.warning(f"[GraphManager] Falha ao sincronizar aresta com Neo4j: {e}")
        return ok

    def get_node(self, node_id: str) -> Optional[KnowledgeNode]:
        return self.embedded.get_node(node_id)

    def get_edge(self, edge_id: str) -> Optional[KnowledgeEdge]:
        return self.embedded.get_edge(edge_id)

    def find_nodes(self, label: Optional[str] = None, validation_status: Optional[str] = None) -> List[KnowledgeNode]:
        return self.embedded.find_nodes(label=label, validation_status=validation_status)

    def get_connected_subgraph(
        self,
        center_node_ids: List[str],
        max_depth: int = 2,
        min_weight_score: float = 0.05
    ) -> Tuple[List[KnowledgeNode], List[KnowledgeEdge]]:
        return self.embedded.get_connected_subgraph(center_node_ids, max_depth, min_weight_score)

    def record_contradiction(
        self,
        hypothesis_a_id: str,
        hypothesis_b_id: str,
        reason: str,
        detected_by: str,
        generation_id: str
    ) -> str:
        return self.embedded.record_contradiction(hypothesis_a_id, hypothesis_b_id, reason, detected_by, generation_id)

    def count_stats(self) -> Dict[str, int]:
        nodes_by_label: Dict[str, int] = {}
        for n in self.embedded.nodes.values():
            nodes_by_label[n.label] = nodes_by_label.get(n.label, 0) + 1
        return {
            "total_nodes": len(self.embedded.nodes),
            "total_edges": len(self.embedded.edges),
            "hypotheses_proposed": len(self.embedded.find_nodes(label="Hypothesis", validation_status="PROPOSED")),
            "hypotheses_verified": len(self.embedded.find_nodes(label="Hypothesis", validation_status="VERIFIED")),
            "hypotheses_refuted": len(self.embedded.find_nodes(label="Hypothesis", validation_status="REFUTED")),
            "contradictions_open": len(self.embedded.find_nodes(label="Contradiction", validation_status="OPEN")),
            **nodes_by_label
        }

knowledge_graph = KnowledgeGraphManager()
