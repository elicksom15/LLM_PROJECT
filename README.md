# ⚡ Dual MiMo Autonomous Research Engine & Sistema Cognitivo Multiagente (LLM_PROJECT)

[![Research Cycles](https://img.shields.io/badge/Cycles-359-blue.svg)](#)
[![Approved Hypotheses](https://img.shields.io/badge/Approved-12-success.svg)](#)
[![Hardware](https://img.shields.io/badge/GPU-RTX%203060%2012GB-76B900.svg)](#)
[![Methodology](https://img.shields.io/badge/Method-Cálculo%20Primeiro%20(Fase%200)-orange.svg)](#)
[![Architecture](https://img.shields.io/badge/Architecture-Graph--Oriented%20Multi--Agent-purple.svg)](#)
[![Test Suite](https://img.shields.io/badge/Tests-16%2F16%20Passing-brightgreen.svg)](#)

Repositório Oficial: **[https://github.com/elicksom15/LLM_PROJECT.git](https://github.com/elicksom15/LLM_PROJECT.git)**

Motor de pesquisa científica autônomo 24/7 alimentado por instâncias duais do modelo **MiMo-V2.6 (UltraSpeed & Pro)** em debate adversarial, expandido com uma **Arquitetura Cognitiva Multiagente Orientada por Grafos Ponderados (Neo4j / GDS)** para guiar gerações sucessivas de pesquisa científica sem quantização convencional.

---

## 🧠 Sistema Cognitivo Multiagente Orientado por Grafos

A camada `collective/` transforma o sistema em uma rede multiagente hierárquica, persistente e adaptativa, capaz de acumular, revisar e reutilizar conhecimento estruturado ao longo de gerações contínuas.

Consulte a especificação formal completa em:
👉 **[Documento de Definição Arquitetural (docs/PROJECT_DEFINITION.md)](docs/PROJECT_DEFINITION.md)**  
👉 **[Auditoria da Arquitetura Base (docs/CURRENT_ARCHITECTURE.md)](docs/CURRENT_ARCHITECTURE.md)**

```
                      [Problema de Pesquisa]
                                │
                                ▼
                   ┌──────────────────────────┐
                   │    Memória Coletiva      │
                   │   (Neo4j Graph Engine)   │
                   └────────────┬─────────────┘
                                │
             ┌──────────────────┴──────────────────┐
             ▼                                     ▼
   [Análise Topológica GDS]              [Subgrafo Contextual]
   (PageRank, Leiden, Adamic)            (Blindagem de Prompts)
             │                                     │
             └──────────────────┬──────────────────┘
                                │
                                ▼
                   ┌──────────────────────────┐
                   │  Orquestrador Dinâmico   │
                   │ (Grafo A ─► Grafo B Exec)│
                   └────────────┬─────────────┘
                                │
                                ▼
                   ┌──────────────────────────┐
                   │   Pool de Agentes (100)  │
                   │ (Ativação Concorrente 12)│
                   └────────────┬─────────────┘
                                │
                                ▼
                   ┌──────────────────────────┐
                   │ Verificação Independente │
                   │  (Fase 0 Math + GPU RTX) │
                   └────────────┬─────────────┘
                                │
                                ▼
                   ┌──────────────────────────┐
                   │ Atualização de Pesos Wo  │
                   │  (Aprendizado Idempotente│
                   └──────────────────────────┘
```

### Princípios Fundamentais Implementados
1. **Processamento Paralelo:** Pool lógico escalável de 100 agentes (expansível a 500) divididos em 12 perfis especializados (`collective/agent_pool.py`), regulados por semáforo assíncrono (`collective/inference_scheduler.py`).
2. **Conhecimento Estruturado em Grafo:** 13 tipos de nós persistidos no Neo4j com APOC e GDS, além de fallback resiliente embutido (`collective_graph_state.json`).
3. **Três Dimensões de Pesos Independentes ($W_s, W_e, W_o$):** Desacoplamento entre correlação semântica ($W_s$), suporte epistêmico ($W_e$) e utilidade física operacional comprovada em bancada ($W_o$).
4. **Raciocínio Compartilhado com Blindagem:** Contextos extraídos como subgrafos com IDs rastreáveis protegidos contra distorção de prompt.
5. **Organização Adaptativa da Execução:** A topologia do Grafo de Conhecimento comanda a formação de equipes no Grafo de Execução.
6. **Retroalimentação e Revisão Explícita:** Resolução formal de contradições sem descartar o histórico de falsificações.
7. **Aprendizagem Operacional Contínua:** Recompensas e penalizações idempotentes direcionam as gerações a evitar hipóteses inférteis.
8. **Validação Independente:** Separação estrita entre proponente e verificador neutro (Fase 0 analítica e benchmark na GPU RTX 3060).

---

## 📊 Validação Científica dos 3 Modos de Operação

O benchmark comparativo rigoroso (`collective/benchmark_experiment.py`) comprovou a hipótese central:

| Modo Experimental | Taxa de Acerto (%) | Consumo Médio (Tokens/Tarefa) | Eficiência Epistêmica |
| :--- | :---: | :---: | :---: |
| **Modo A (Baseline sem Grafo)** | 50.0% | 932 tokens | 0.536 |
| **Modo B (Grafo Estático)** | 75.0% | 658 tokens | 1.140 |
| **Modo C (Grafo Adaptativo com Retroalimentação)** | **91.7%** | **564 tokens** | **1.626** |

**Ganhos Empíricos Comprovados:**
- **+83.4% de aumento na precisão investigativa** em relação ao modelo convencional.
- **-39.5% de redução no consumo de tokens e FLOPs**, eliminando investigações redundantes e direcionando os agentes para caminhos de alta utilidade comprovada ($W_o = 0.744$).

---

## 🎯 Missão Principal: Qwen 32B em RTX 3060 Sem Quantização Convencional
Desenvolver uma formulação matemática inédita que reduza o custo computacional e o tráfego de memória de inferência autorregressiva em mais de **75% a 85%**, eliminando as perdas de precisão das quantizações convencionais (AWQ/GPTQ) através de:
- **Álgebra de Subespaços Invariantes de Krylov**
- **Transporte Paralelo Espectral entre Camadas**
- **Splitting de Strang e Operadores Anti-simétricos Simpléticos**

### 🧮 Diretriz: Cálculo Primeiro, GPU Depois (Fase 0)
1. **Auditoria Matemática:** Antes de acionar a GPU, os operadores são auditados formalmente no papel. Se a redução teórica de FLOPs e tráfego de VRAM for $< 75%$, a hipótese é **imediatamente rejeitada**, poupando ciclos físicos da RTX 3060.
2. **Validação Física em GPU:** Modelos aprovados no cálculo são compilados e medidos na bancada física local (`~3B GPT`), aferindo throughput real (tokens/s), divergência KL e acurácia Top-1.
3. **Persistência e Telemetria em Tempo Real:** Todos os ciclos, teses e pareceres são registrados em SQLite e transmitidos ao Discord com sincronização contínua neste repositório.

---

## 🛠️ Como Executar

### 1. Suíte de Testes Automatizada
```bash
python tests/test_collective_intelligence.py
```

### 2. Subir Cluster Neo4j com GDS
```bash
docker-compose up -d
```

### 3. Executar Geração Cognitiva Coletiva
```bash
python -c "import asyncio; from collective.generation_cycle import GenerationCycleEngine; asyncio.run(GenerationCycleEngine().run_generation_cycle('Redução de FLOPs em camadas intermediárias via Krylov'))"
```

---

Para conferir o relatório completo de todos os ciclos executados, acesse:
👉 **[Ver Estado e Ledger Completo (STATE.md)](STATE.md)**
