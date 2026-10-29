import os
import sys
import time
import unittest
from pathlib import Path

# Adiciona o diretório base ao sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from collective.config import collective_config
from collective.weights import RelationshipWeights, OperationalWeightEngine
from collective.graph_engine import KnowledgeGraphManager, KnowledgeNode, KnowledgeEdge
from collective.agent_pool import LogicalAgentPool, ROLE_PROMPTS
from collective.inference_scheduler import InferenceScheduler
from collective.subgraph_extractor import SubgraphExtractor
from collective.graph_orchestrator import DynamicGraphOrchestrator
from collective.gds_engine import GraphDataScienceEngine
from collective.verifier import IndependentVerifierEngine
from collective.generation_cycle import GenerationCycleEngine
from collective.benchmark_experiment import ComparativeScientificExperiment
from collective.observability import CollectiveObservability

class TestCollectiveIntelligence(unittest.TestCase):
    def setUp(self):
        # Utiliza arquivo temporário isolado para não poluir o banco de produção
        self.test_state_file = BASE_DIR / "tests" / "test_graph_state.json"
        if self.test_state_file.exists():
            self.test_state_file.unlink()
        self.km = KnowledgeGraphManager()
        self.km.embedded.state_file = self.test_state_file
        self.km.embedded.nodes.clear()
        self.km.embedded.edges.clear()
        self.km.embedded.adjacency.clear()
        self.km.embedded.reverse_adjacency.clear()

    def tearDown(self):
        if self.test_state_file.exists():
            self.test_state_file.unlink()

    # TESTE 1: 100 agentes lógicos registrados
    def test_01_100_logical_agents_registered(self):
        pool = LogicalAgentPool(target_pool_size=100)
        self.assertEqual(len(pool.agents), 100)
        # Todos os papéis essenciais presentes
        roles_present = {a.role for a in pool.agents.values()}
        self.assertTrue(set(ROLE_PROMPTS.keys()).issubset(roles_present))

    # TESTE 2: Expansão configurável para 500 agentes lógicos
    def test_02_500_logical_agents_expansion(self):
        pool = LogicalAgentPool(target_pool_size=100, max_pool_size=500)
        self.assertEqual(len(pool.agents), 100)
        expanded_len = pool.expand_pool(500)
        self.assertEqual(expanded_len, 500)
        self.assertEqual(len(pool.agents), 500)

    # TESTE 3: Ativação de apenas um subconjunto enxuto por tarefa (active_limit)
    def test_03_active_subset_selection(self):
        pool = LogicalAgentPool(target_pool_size=100)
        active = pool.select_active_agents(
            required_roles=["investigator", "critic", "independent_verifier"],
            max_active=5
        )
        self.assertLessEqual(len(active), 5)
        self.assertTrue(all(a.status == "ASSIGNED" for a in active))
        # O restante do pool permanece IDLE
        idle_count = sum(1 for a in pool.agents.values() if a.status == "IDLE")
        self.assertEqual(idle_count, 100 - len(active))

    # TESTE 4: Limites reais de inferência concorrente (Semaphore)
    def test_04_inference_concurrency_limits(self):
        sched = InferenceScheduler(max_concurrency=2)
        self.assertEqual(sched.semaphore._value, 2)
        # Tenta adquirir além do limite
        self.assertTrue(sched.semaphore.acquire(timeout=0.1))
        self.assertTrue(sched.semaphore.acquire(timeout=0.1))
        # Terceiro deve dar timeout
        self.assertFalse(sched.semaphore.acquire(timeout=0.05))
        sched.semaphore.release()
        sched.semaphore.release()

    # TESTE 5: Reinício com memória preservada
    def test_05_restart_with_preserved_memory(self):
        # Insere nós e arestas no grafo de teste
        n1 = KnowledgeNode(id="hyp_test_01", label="Hypothesis", title="Hipótese Teste 1")
        n2 = KnowledgeNode(id="prob_test_01", label="Problem", title="Problema Teste 1")
        e1 = KnowledgeEdge(
            id="e_test_01", source_id="hyp_test_01", target_id="prob_test_01", relation_type="ADDRESSES",
            weights=RelationshipWeights(weight_operational=0.75)
        )
        self.km.add_node(n1)
        self.km.add_node(n2)
        self.km.add_edge(e1)

        # Simula reinício de nova instância carregando o mesmo arquivo de estado
        new_km = KnowledgeGraphManager()
        new_km.embedded.state_file = self.test_state_file
        new_km.embedded.load_state()

        self.assertIn("hyp_test_01", new_km.embedded.nodes)
        self.assertIn("prob_test_01", new_km.embedded.nodes)
        self.assertIn("e_test_01", new_km.embedded.edges)
        self.assertEqual(new_km.get_edge("e_test_01").weights.weight_operational, 0.75)

    # TESTE 6: Persistência explícita de contradições
    def test_06_contradiction_persistence(self):
        h1 = KnowledgeNode(id="hyp_a", label="Hypothesis", title="Hipótese A: Salto Analítico")
        h2 = KnowledgeNode(id="hyp_b", label="Hypothesis", title="Hipótese B: Fluxo Contínuo Não-Saltável")
        self.km.add_node(h1)
        self.km.add_node(h2)

        c_id = self.km.record_contradiction(
            hypothesis_a_id="hyp_a",
            hypothesis_b_id="hyp_b",
            reason="Incompatibilidade de continuidade do residual stream",
            detected_by="agent_critic_01",
            generation_id="gen_001"
        )
        self.assertTrue(c_id.startswith("contra_"))
        self.assertEqual(self.km.get_node("hyp_a").validation_status, "CONTRADICTORY")
        self.assertEqual(self.km.get_node("hyp_b").validation_status, "CONTRADICTORY")
        # Nó de contradição gravado
        c_node = self.km.get_node(c_id)
        self.assertIsNotNone(c_node)
        self.assertEqual(c_node.validation_status, "OPEN")

    # TESTE 7: Correção de hipóteses anteriormente aceitas (sem perda de histórico)
    def test_07_hypothesis_refutation_preserves_history(self):
        h = KnowledgeNode(id="hyp_old", label="Hypothesis", title="Hipótese Anterior", validation_status="VERIFIED")
        self.km.add_node(h)

        # Na geração posterior, nova evidência refuta a hipótese
        h.validation_status = "REFUTED"
        h.epistemic_class = "FALSIFIED"
        h.properties["refuted_in_generation"] = "gen_005"
        self.km.add_node(h) # Upsert preserva o nó com versão incrementada

        updated = self.km.get_node("hyp_old")
        self.assertEqual(updated.validation_status, "REFUTED")
        self.assertEqual(updated.epistemic_class, "FALSIFIED")
        self.assertEqual(updated.version, 2)

    # TESTE 8: Seleção contextual de subgrafos com relações ponderadas
    def test_08_subgraph_selection_with_weights(self):
        extractor = SubgraphExtractor()
        # Conecta nós
        h1 = KnowledgeNode(id="h1", label="Hypothesis", title="Krylov Subspace")
        h2 = KnowledgeNode(id="h2", label="Hypothesis", title="Strang Splitting")
        e = KnowledgeEdge(
            id="e_h1_h2", source_id="h1", target_id="h2", relation_type="DEPENDS_ON",
            weights=RelationshipWeights(weight_operational=0.88, weight_epistemic=0.9)
        )
        self.km.add_node(h1)
        self.km.add_node(h2)
        self.km.add_edge(e)

        res = extractor.extract_context_for_task("Krylov", seed_node_ids=["h1"], max_nodes=5, graph_manager=self.km)
        self.assertIn("h1", res["consumed_node_ids"])
        self.assertIn("h2", res["consumed_node_ids"])
        self.assertIn("e_h1_h2", res["consumed_relation_ids"])
        self.assertIn("MEMÓRIA COLETIVA PERSISTENTE", res["formatted_prompt"])

    # TESTE 9: Feedback duplicado sem dupla atualização (Idempotência)
    def test_09_feedback_idempotency(self):
        engine = OperationalWeightEngine(learning_rate=0.20)
        weights = RelationshipWeights(weight_operational=0.50)

        # Primeira aplicação do evento
        ok1 = engine.update_operational_weight(
            weights=weights,
            event_id="evt_unique_123",
            verified_reward=1.0,
            generation_id="gen_001"
        )
        self.assertTrue(ok1)
        w_after_first = weights.weight_operational
        self.assertGreater(w_after_first, 0.50)

        # Segunda aplicação com o mesmo event_id deve ser estritamente bloqueada
        ok2 = engine.update_operational_weight(
            weights=weights,
            event_id="evt_unique_123",
            verified_reward=1.0,
            generation_id="gen_001"
        )
        self.assertFalse(ok2)
        # O peso NÃO pode ser alterado na chamada repetida
        self.assertEqual(weights.weight_operational, w_after_first)

    # TESTE 10: Três dimensões de pesos não se misturam em atributo único permanente
    def test_10_three_independent_weight_dimensions(self):
        w = RelationshipWeights(weight_semantic=0.8, weight_epistemic=0.7, weight_operational=0.6)
        # Pontuação de decisão composta é efêmera
        score = w.calculate_decision_score(alpha_op=0.5, beta_ep=0.3, gamma_sem=0.2)
        self.assertAlmostEqual(score, 0.5*0.6 + 0.3*0.7 + 0.2*0.8, places=4)
        # Atributos permanentes originais permanecem intactos e auditáveis
        self.assertEqual(w.weight_semantic, 0.8)
        self.assertEqual(w.weight_epistemic, 0.7)
        self.assertEqual(w.weight_operational, 0.6)

    # TESTE 11: Falha temporária da LLM (Resiliência)
    def test_11_llm_resilience_and_graceful_handling(self):
        from unittest.mock import patch
        sched = InferenceScheduler()
        with patch("mimo_client.mimo_client.call_model", return_value={"success": False, "error": "simulated_timeout"}):
            res = sched.dispatch(
                agent_id="agent_test",
                role="investigator",
                messages=[{"role": "user", "content": "ping"}],
                timeout=0.01
            )
        self.assertIn("success", res)
        self.assertFalse(res["success"])

    # TESTE 12: Falha temporária do Neo4j (Fallback Embutido Transparente)
    def test_12_neo4j_fallback_to_embedded(self):
        self.km.is_neo4j_online = False
        # Operações continuam funcionando normalmente no motor embutido
        n = KnowledgeNode(id="node_fallback", label="Hypothesis", title="Resilient Node")
        self.assertTrue(self.km.add_node(n))
        self.assertIsNotNone(self.km.get_node("node_fallback"))

    # TESTE 13: Proteção contra conclusões falsas por consenso
    def test_13_consensus_protection_independent_verification(self):
        verifier = IndependentVerifierEngine(graph_manager=self.km)
        # Hipótese que não corta FLOPs suficientes
        bad_hyp = KnowledgeNode(
            id="hyp_bad_flops",
            label="Hypothesis",
            title="Técnica Convencional sem corte",
            description="Proposta com corte insignificante de 10% de FLOPs"
        )
        self.km.add_node(bad_hyp)

        outcome = verifier.verify_hypothesis(
            hypothesis_id="hyp_bad_flops",
            proposer_agent_id="agent_proposer_01",
            generation_id="gen_test",
            consumed_relation_ids=[],
            graph_manager=self.km
        )
        # Deve ser sumariamente refutada independentemente de qualquer consenso prévio
        self.assertEqual(outcome.status, "refuted")
        self.assertEqual(outcome.reward, 0.0)

    # TESTE 14: PageRank é apenas sinal de prioridade, não prova de verdade epistêmica
    def test_14_pagerank_as_prioritization_signal(self):
        gds = GraphDataScienceEngine(graph_manager=self.km)
        # Cria grafo de teste
        n1 = KnowledgeNode(id="np1", label="Hypothesis", title="Hub Concept")
        n2 = KnowledgeNode(id="np2", label="Hypothesis", title="Leaf Concept")
        e = KnowledgeEdge(id="ep1", source_id="np2", target_id="np1", relation_type="SUPPORTS")
        self.km.add_node(n1)
        self.km.add_node(n2)
        self.km.add_edge(e)

        res = gds.run_full_analysis(graph_manager=self.km)
        self.assertIn("top_pagerank", res)
        # O nó hub terá maior PageRank
        pr_dict = dict(res["top_pagerank"])
        self.assertGreater(pr_dict.get("np1", 0.0), pr_dict.get("np2", 0.0))
        # Mas seu status de validação epistêmica permanece PROPOSED (não vira VERIFIED por causa do PageRank)
        self.assertEqual(self.km.get_node("np1").validation_status, "PROPOSED")

    # TESTE 15: Execução justa do Experimento Científico (Modos A, B, C)
    def test_15_comparative_experiment_abc(self):
        exp = ComparativeScientificExperiment()
        res = exp.run_full_experiment(seeds=[42], replications=1)
        self.assertIn("mode_a_baseline", res)
        self.assertIn("mode_b_static_graph", res)
        self.assertIn("mode_c_adaptive_graph", res)
        # Modo C adaptativo deve registrar taxa de sucesso e peso operacional médio
        self.assertGreaterEqual(res["mode_c_adaptive_graph"]["accuracy_mean"], 0.0)
        self.assertIn("final_w_operational_mean", res["mode_c_adaptive_graph"])

    # TESTE 16: Observabilidade e Snapshots de Telemetria
    def test_16_observability_snapshot(self):
        obs = CollectiveObservability()
        snap = obs.collect_metrics_snapshot()
        self.assertIn("graph", snap)
        self.assertIn("agents", snap)
        self.assertIn("inference", snap)
        self.assertEqual(snap["agents"]["logical_pool_total"], 100)

if __name__ == "__main__":
    unittest.main()
