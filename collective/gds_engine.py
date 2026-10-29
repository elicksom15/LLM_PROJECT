import math
import logging
from typing import Dict, Any, List, Set, Tuple
from collective.graph_engine import knowledge_graph, KnowledgeNode, KnowledgeEdge

logger = logging.getLogger("research_duel.collective.gds")

class GraphDataScienceEngine:
    """
    Motor de Ciência de Dados em Grafos (GDS).
    Executa análises estruturais para priorização e roteamento epistêmico.
    Nunca declara uma hipótese verdadeira: gera apenas sinais de prioridade investigativa.
    """
    def __init__(self, graph_manager=None):
        self.km = graph_manager or knowledge_graph
        self.last_run_timestamp = 0
        self.cached_pagerank: Dict[str, float] = {}
        self.cached_betweenness: Dict[str, float] = {}
        self.cached_communities: Dict[str, int] = {}
        self.cached_link_predictions: List[Dict[str, Any]] = []

    def run_full_analysis(self, graph_manager=None) -> Dict[str, Any]:
        """
        Executa todos os algoritmos de GDS estruturais (via Neo4j GDS se online, ou Embedded fallback).
        """
        km = graph_manager or self.km
        if km.is_neo4j_online and km.neo4j_driver:
            try:
                return self._run_neo4j_gds(km)
            except Exception as e:
                logger.warning(f"[GDS] Neo4j GDS falhou ou indisponível ({e}). Executando via Embedded GDS.")

        return self._run_embedded_gds(km)

    def _run_embedded_gds(self, km=None) -> Dict[str, Any]:
        """Algoritmos de Grafo Embutidos de Alto Desempenho."""
        km = km or self.km
        nodes = km.embedded.nodes
        edges = km.embedded.edges
        adj = km.embedded.adjacency

        N = len(nodes)
        if N == 0:
            return {"status": "EMPTY_GRAPH", "communities_count": 0}

        # 1. PAGERANK (Influência Estrutural)
        pr = {nid: 1.0 / N for nid in nodes}
        damping = 0.85
        for _ in range(15):
            new_pr = {nid: (1.0 - damping) / N for nid in nodes}
            for u in nodes:
                out_edges = adj.get(u, set())
                out_neighbors = [edges[eid].target_id for eid in out_edges if eid in edges]
                if out_neighbors:
                    contrib = pr[u] / len(out_neighbors)
                    for v in out_neighbors:
                        if v in new_pr:
                            new_pr[v] += damping * contrib
                else:
                    for v in nodes:
                        new_pr[v] += damping * (pr[u] / N)
            pr = new_pr
        self.cached_pagerank = pr

        # 2. BETWEENNESS CENTRALITY (Pontes entre subdomínios)
        bc = {nid: 0.0 for nid in nodes}
        # Amostragem de caminhos mínimos para aproximação de Brandes
        sample_nodes = list(nodes.keys())[:min(20, N)]
        for s in sample_nodes:
            # BFS simples
            queue = [s]
            dist = {s: 0}
            sigma = {nid: 0 for nid in nodes}
            sigma[s] = 1
            pred = {nid: [] for nid in nodes}

            while queue:
                v = queue.pop(0)
                for eid in adj.get(v, set()):
                    w = edges[eid].target_id if eid in edges else None
                    if w and w in nodes:
                        if w not in dist:
                            dist[w] = dist[v] + 1
                            queue.append(w)
                        if dist[w] == dist[v] + 1:
                            sigma[w] += sigma[v]
                            pred[w].append(v)

            delta = {nid: 0.0 for nid in nodes}
            # Ordem reversa de distância
            stack = sorted(dist.keys(), key=lambda x: dist[x], reverse=True)
            for w in stack:
                for v in pred[w]:
                    delta[v] += (sigma[v] / max(1, sigma[w])) * (1.0 + delta[w])
                if w != s:
                    bc[w] += delta[w]
        self.cached_betweenness = bc

        # 3. DETECÇÃO DE COMUNIDADES (Leiden / Label Propagation simplificado)
        labels = {nid: idx for idx, nid in enumerate(nodes.keys())}
        for _ in range(5):
            for u in nodes:
                neighbors = [edges[eid].target_id for eid in adj.get(u, set()) if eid in edges]
                if neighbors:
                    counts: Dict[int, int] = {}
                    for v in neighbors:
                        l = labels.get(v, labels[u])
                        counts[l] = counts.get(l, 0) + 1
                    best_label = max(counts.items(), key=lambda x: x[1])[0]
                    labels[u] = best_label
        self.cached_communities = labels
        unique_communities = len(set(labels.values()))

        # 4. LINK PREDICTION (Adamic-Adar / Similaridade de Vizinhos)
        candidates = []
        node_list = list(nodes.keys())
        for i in range(min(15, len(node_list))):
            for j in range(i + 1, min(15, len(node_list))):
                u, v = node_list[i], node_list[j]
                # Verifica se já são conectados
                existing_e = any(edges[eid].target_id == v for eid in adj.get(u, set()) if eid in edges)
                if not existing_e:
                    u_neigh = {edges[eid].target_id for eid in adj.get(u, set()) if eid in edges}
                    v_neigh = {edges[eid].target_id for eid in adj.get(v, set()) if eid in edges}
                    common = u_neigh & v_neigh
                    if common:
                        score = sum(1.0 / max(1.0, math.log(len(adj.get(c, set())) + 1.1)) for c in common)
                        candidates.append({
                            "source_id": u,
                            "target_id": v,
                            "predicted_score": round(score, 4),
                            "rationale": f"Possuem {len(common)} vizinhos conceituais em comum"
                        })
        self.cached_link_predictions = sorted(candidates, key=lambda x: x["predicted_score"], reverse=True)[:5]

        return {
            "status": "SUCCESS_EMBEDDED",
            "nodes_analyzed": N,
            "edges_analyzed": len(edges),
            "communities_count": unique_communities,
            "top_pagerank": sorted(pr.items(), key=lambda x: x[1], reverse=True)[:5],
            "top_betweenness": sorted(bc.items(), key=lambda x: x[1], reverse=True)[:5],
            "link_predictions": self.cached_link_predictions
        }

    def _run_neo4j_gds(self) -> Dict[str, Any]:
        """Execução remota no Neo4j Graph Data Science."""
        with knowledge_graph.neo4j_driver.session(database=knowledge_graph.config.database) as session:
            # Verifica se GDS está disponível no Neo4j
            res = session.run("CALL gds.version() YIELD version RETURN version")
            gds_version = res.single()[0]
            logger.info(f"[GDS] Neo4j GDS versão {gds_version} ativa.")
            # Projeção efêmera ou fallback
            return self._run_embedded_gds()

gds_engine = GraphDataScienceEngine()
