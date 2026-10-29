# 🧠 Sistema Cognitivo Multiagente Orientado por Grafos
**Documento de Definição e Especificação Arquitetural**  
**Repositório Oficial:** `https://github.com/elicksom15/LLM_PROJECT.git`  
**Módulo Implementado:** `collective/`  

---

## 1. Conceito Central
O projeto implementa uma arquitetura multiagente hierárquica e adaptativa, na qual agentes de inteligência artificial produzem, transformam, relacionam e verificam informações de maneira estritamente colaborativa e estruturada.

O conhecimento gerado não é simplesmente transmitido de um agente para outro como texto livre descartável. Ele é convertido em uma estrutura de grafo persistente e ponderado utilizando **Neo4j** (com motor de resiliência embutido).

O grafo atua simultaneamente como:
- **Memória Coletiva:** Preserva hipóteses, evidências, conclusões, contradições e relações causais entre gerações sucessivas.
- **Estrutura de Raciocínio:** Permite que agentes operem diretamente sobre o conhecimento formalizado anteriormente, sem perder contexto ou histórico de falsificações.
- **Mecanismo de Orientação:** Utiliza algoritmos de grafos (GDS) e pesos multidimensionais para determinar quais regiões do grafo devem ser investigadas prioritariamente.
- **Histórico de Aprendizagem Operacional:** Registra quais conexões, hipóteses e estratégias produziram resultados experimentalmente verificáveis.

> **Objetivo Maior:** Cada geração de agentes modifica o ambiente de conhecimento que orientará, restringirá e potencializará o trabalho das gerações seguintes.

---

## 2. Princípios Fundamentais do Sistema

| Princípio | Implementação no LLM_PROJECT | Módulo Responsável |
| :--- | :--- | :--- |
| **Processamento Paralelo** | Pool de 100 a 500 agentes lógicos com scheduler de concorrência desacoplado | `collective/agent_pool.py`, `collective/inference_scheduler.py` |
| **Conhecimento Estruturado** | 13 tipos de nós (`Problem`, `Hypothesis`, `Evidence`, `Contradiction`, etc.) persistidos no Neo4j | `collective/graph_engine.py`, `neo4j_schema.cypher` |
| **Grafo Ponderado** | Três dimensões de pesos independentes ($W_s, W_e, W_o$) por aresta | `collective/weights.py` |
| **Raciocínio Compartilhado** | Extração de subgrafos contextuais com blindagem semântica contra injeção de prompt | `collective/subgraph_extractor.py` |
| **Organização Adaptativa** | O Grafo de Conhecimento (A) dita dinamicamente a topologia do Grafo de Execução (B) | `collective/graph_orchestrator.py` |
| **Retroalimentação** | Resolução explícita de contradições e correção de hipóteses sem apagar histórico | `collective/verifier.py`, `collective/graph_engine.py` |
| **Aprendizagem Operacional** | Atualização idempotente de utilidade com penalização de becos sem saída | `collective/weights.py` |
| **Validação Independente** | Separação estrita entre o agente propositor e o verificador objetivo | `collective/verifier.py` |

---

## 3. Dinâmica das Três Dimensões de Pesos
Para não confundir popularidade, similaridade ou utilidade com veracidade, os pesos operam de maneira desacoplada e nunca são combinados em um único atributo permanente:

### 3.1 Peso Semântico ($W_s \in [0, 1]$)
- Expressa proximidade conceitual, similaridade vetorial e intensidade de associação teórica.
- **Propriedade:** Não representa prova nem veracidade científica.

### 3.2 Peso Epistêmico ($W_e \in [0, 1]$)
- Mede a qualidade do suporte evidencial, a independência das fontes e a ausência de contradições abertas.
- **Regra de Ouro:** Múltiplos agentes citando a mesma fonte ou concordando entre si **não** são contabilizados como fontes independentes.

### 3.3 Peso Operacional ($W_o \in [0, 1]$)
- Mede a utilidade histórica de uma conexão ou caminho investigativo para produzir resultados comprovados em bancada experimental.
- **Fórmula de Atualização Operacional:**
  $$W_{o, \text{next}} = \text{clip}\big((1 - \alpha) \cdot W_{o, \text{current}} + \alpha \cdot \text{verified\_reward},\, \min\_w,\, \max\_w\big)$$
- **Garantias:**
  - Idempotência estrita por `event_id` (nenhum feedback é computado em duplicidade).
  - Penalização automática de caminhos que resultem em falsificações empíricas ou contradições.
  - Controle de incerteza decrescente ($U \leftarrow U \cdot \gamma$) à medida que o caminho acumula validações.

---

## 4. Algoritmos de Grafos (Neo4j Graph Data Science)
O Neo4j atua como banco transacional, e os algoritmos estruturais fornecem sinais de prioridade investigativa para o orquestrador:

- **Leiden / Louvain:** Identificação de comunidades temáticas densas de hipóteses correlacionadas.
- **PageRank:** Identificação de nós centrais que exercem forte influência estrutural sobre o problema.
- **Betweenness Centrality:** Mapeamento de nós que conectam diferentes subdomínios (ex: ponte entre álgebra linear e física de semicondutores).
- **Node Similarity:** Detecção de sobreposições teóricas e redundâncias entre agentes para desduplicação.
- **Link Prediction (Adamic-Adar):** Sugestão de novas hipóteses de ligação que merecem alocação de orçamento investigativo.

> **Regra Epistêmica:** O GDS nunca declara uma hipótese verdadeira. Seus resultados atuam como sinais de priorização para a alocação de agentes.

---

## 5. Ciclo de Execução Contínuo (Gerações de Inteligência)
Cada geração de pesquisa opera em um ciclo fechado de 13 etapas governadas por orçamentos de tempo, tokens e tarefas:

```
[Problema Aberto / Fronteira]
          │
          ▼
1. Consulta à Memória Coletiva (Neo4j)
          │
          ▼
2. Análise Estrutural GDS (PageRank, Betweenness, Comunidades, Contradições)
          │
          ▼
3. Extração de Subgrafo Contextual com IDs Rastreáveis (subgraph_extractor)
          │
          ▼
4. Construção do Grafo de Execução Dinâmico (graph_orchestrator)
   - Contradições abertas  ─► Ativa Críticos e Verificadores
   - Lacunas de evidência ─► Ativa Investigadores e Analistas
          │
          ▼
5. Alocação do Pool de Agentes Lógicos (Ativação enxuta de até 12 ativos)
          │
          ▼
6. Inferência Concorrente Regulada por Semáforo (inference_scheduler)
          │
          ▼
7. Estruturação em Nós e Arestas Ponderadas no Grafo
          │
          ▼
8. Auditoria Matemática Analítica (Fase 0: Corte >= 75%)
   ├─► Se Corte < 75%: REFUTAÇÃO IMEDIATA (Penalidade Operacional Wo ↓) ──┐
   ▼                                                                      │
9. Validação Física Independente em GPU (benchmark_engine RTX 3060)       │
   ├─► Se Aprovada (Top1 >= 98%, Speedup > 1.0x): RECOMPENSA (Wo ↑)       │
   └─► Se Falsificada: REFUTAÇÃO (Wo ↓)                                   │
          │                                                               │
          ├───────────────────────────────────────────────────────────────┘
          ▼
10. Revisão de Conclusões e Resolução de Conflitos
          │
          ▼
11. Registro Transacional do Nó de Geração e Checkpoint
          │
          ▼
12. Telemetria em Tempo Real (Discord & GitHub Sync)
          │
          ▼
[Geração N+1: Inicia com o Grafo Mais Rico e Caminhos Inúteis Já Podados]
```

---

## 6. Diferencial da Arquitetura e Validação Científica
A hipótese central:
> *Um sistema multiagente pode melhorar sua eficiência e qualidade de investigação quando o conhecimento produzido é estruturado em um grafo ponderado, e os resultados anteriores influenciam dinamicamente a seleção e a organização das investigações seguintes.*

### Resultados Empíricos A/B/C Comprovados (`collective/benchmark_experiment.py`):
- **Modo A (Baseline sem grafo):** Taxa de acerto de 50.0%, 932 tokens médios por tarefa.
- **Modo B (Grafo estático sem aprendizado de pesos):** Taxa de acerto de 75.0%, 658 tokens médios por tarefa.
- **Modo C (Grafo adaptativo com aprendizado operacional):** Taxa de acerto de **91.7%**, consumo de **564 tokens médios por tarefa** (+83% de precisão sobre o baseline e 39% de economia de computação).
