# 🏛️ RELATÓRIO FACTUAL DA ARQUITETURA EXISTENTE (LLM_PROJECT)
**Data da Auditoria:** 2026-10-28  
**Localização do Projeto:** `E:\AI_MODELS\research_duel`  
**Repositório Oficial:** `https://github.com/elicksom15/LLM_PROJECT.git` (branch `main`)  
**Hardware da Bancada:** NVIDIA GeForce RTX 3060 12GB GDDR6 (3.584 CUDA Cores, Banda: 360 GB/s)  

---

## 1. Visão Geral e Missão do Sistema
O `LLM_PROJECT` (operando sob o diretório `research_duel`) é um sistema autônomo de pesquisa científica contínua (24/7) projetado para investigar, formular, auditar e testar técnicas matemáticas inéditas de redução extrema de poder computacional (FLOPs e tráfego de memória de ativação) em Modelos de Linguagem de Grande Porte (LLMs), visando viabilizar a execução de modelos de grande porte (como **Qwen 32B**) em GPUs de consumo de 12GB sem o uso de quantização convencional uniforme (GGUF, AWQ, GPTQ).

---

## 2. Tecnologias, Linguagens e Frameworks
- **Linguagem Principal:** Python 3.14 (CPython 64-bit sobre Windows).
- **Aceleração de Hardware & Deep Learning:**
  - `torch` 2.x com suporte CUDA 12.x (`NVIDIA GeForce RTX 3060 12GB`).
  - `transformers` 4.x (`GPT2LMHeadModel`, `GPT2Tokenizer`).
  - `numpy` e `scipy` (álgebra linear, decomposição espectral SVD/PCA, projeção matricial).
- **Persistência de Dados & Estado:**
  - `sqlite3` (`research_state.db`) com journaling WAL/Rollback.
  - `json` estruturado (`ledger.json`) para portabilidade e reidratação.
  - `markdown` (`STATE.md` e `README.md`) gerados automaticamente.
- **Rede, APIs e Comunicação:**
  - `httpx` (requisições síncronas/streaming via HTTP/1.1 para OpenAI-compatible API e Discord REST API v10).
  - `uvicorn` e `fastapi` na proxy reversa local (`E:\AI_MODELS\PROXY-REVERSA`).
  - `neo4j` Python Driver (Bolt Protocol).

---

## 3. Entry Points e Controle de Ciclo de Vida
O projeto conta com entry points por scripts batch e CLI:
1. `START_RESEARCH.bat`: Dispara o orquestrador em modo loop infinito (`python orchestrator.py loop 100`).
2. `STOP_RESEARCH.bat`: Emite sinal gracioso de parada gravando `STOP.signal`.
3. `PAUSE_RESEARCH.bat`: Emite sinal de pausa gravando `PAUSE.signal`.
4. `RESUME_RESEARCH.bat`: Remove o sinal `PAUSE.signal`, retomando o processamento.
5. `orchestrator.py`: Entry point primário de execução (`python orchestrator.py` para ciclo único ou `python orchestrator.py loop [N]`).
6. `git_sync.py`: Entry point de reconciliação, compilação de ledger e push para o GitHub.
7. `tests/run_tests.py`: Suíte de testes automatizados (testes 1 a 13).

---

## 4. LLM Principal, Provedores e Proxy Reversa
- **Provedor Primário:** Xiaomi MiMo AI Studio acessado via proxy reversa local rodando na porta 8088 (`http://127.0.0.1:8088/v1/chat/completions`).
- **Modelos Utilizados:**
  - `mimo-v2.6-pro-ultraspeed` (**Pesquisador A / Inovador Matemático**): Encarregado da geração de formulações analíticas inéditas (variedades simpléticas, contração espectral de Kronecker, salto analítico Taylor ODE, geometria de Poincaré).
  - `mimo-v2.6-pro` (**Pesquisador B / Auditor Adversarial**): Encarregado da auditoria estrita de limites físicos de hardware, complexidade de FLOPs e falsificação científica.
- **Conector (`mimo_client.py`):**
  - Implementa streaming Server-Sent Events (SSE) acumulativo para evitar deadlocks de buffer em payloads longos.
  - Detecção automática de esgotamento de cota diária (erro Xiaomi `4005` / HTTP `429`).
  - Micro-pausa anti-rate-limit configurada entre chamadas.
- **Bancada Local de Validação em GPU:**
  - Modelo físico local: GPT-2 (`~3B Architecture Testbed`, localizado em `E:\AI_MODELS\branchman\models\gpt2`).
  - Avaliação direta de tensores de ativação, acurácia Top-1 Argmax, divergência KL e tokens/s medidos via CUDA.

---

## 5. Mapeamento do Fluxo Operacional Existente
O fluxo de execução do sistema é linear e estritamente encadeado por ciclo:

```
[Início do Ciclo]
      │
      ▼
1. Recuperação do Estado (persistence.get_latest_cycle_id() + 1)
      │
      ▼
2. Seleção de Hipótese (hypothesis_manager.get_pending_hypothesis() ou síntese)
      │
      ▼
3. Rodada 1: Investigação Independente (debate_engine - MiMo UltraSpeed & Pro)
      │
      ▼
4. Rodada 2: Confronto e Críticas Adversariais (debate_engine - Auditoria de Overheads)
      │
      ▼
5. Rodada 3: Especificação Experimental Formal (debate_engine - Parâmetros r, k, tau)
      │
      ▼
6. Fase 0: Auditoria Matemática Prévia (analytical_engine - "Cálculo Primeiro, GPU Depois")
      ├─► Se Corte Teórico < 75%: REJEIÇÃO IMEDIATA (GPU Poupada) ──┐
      ▼                                                             │
7. Se Corte >= 75%: Benchmark Físico em GPU (experiment_runner)     │
   - Execução CUDA vetorial em RTX 3060                             │
   - Medição real de tokens/s, FLOPs, Top-1 Argmax e VRAM           │
      │                                                             │
      ▼                                                             │
8. Rodada 4: Avaliação Crítica Pós-Experimento & Veredito Final     │
      │                                                             │
      ├─────────────────────────────────────────────────────────────┘
      ▼
9. Persistência SQLite & Ledger JSON (persistence.finish_cycle)
      │
      ▼
10. Sincronização Contínua com GitHub (git_sync.commit_and_push)
      │
      ▼
11. Telemetria Discord (discord_bridge - Rich Embeds com hash do commit)
      │
      ▼
[Resfriamento / Próximo Ciclo no Loop 24/7]
```

---

## 6. Persistência, Memória e Gerenciamento de Contexto Atual
- **Banco de Dados SQLite (`research_state.db`):**
  - Tabela `research_cycles`: Registro de ciclo, objetivo, veredito (`APPROVED`, `REJECTED`, `REJECTED_ANALYTICAL`), métricas JSON e próximo passo.
  - Tabela `debate_messages`: Histórico de mensagens completas de cada rodada, agentes, modelos e latências.
  - Tabela `hypotheses`: Fila de hipóteses, status, proponente e evidências associadas.
  - Tabela `experiment_records`: Dados do ensaio físico (hash do código, tokens/s baseline e otimizado, redução de FLOPs, acurácia Top-1, VRAM).
- **Memória de Contexto Injetada:**
  - Função `build_gpt3b_ledger_context()`: Injeta sumário textual dos ciclos passados e descobertas empíricas comprovadas nos prompts do debate.
- **Limitação da Memória Existente:**
  - A memória é relacional-tabular (SQLite) e textual linear. Não há estrutura em grafo conectando dependências causais entre conceitos, evidências parciais, contradições entre hipóteses, nem rastreamento de nós de raciocínio.

---

## 7. Telemetria e Monitoramento
- **Discord Bot / Webhooks via REST API (`discord_bridge.py`):**
  - Canal `#ia-3` (`1561523208509853756`).
  - Cards formatados para cada rodada: Investigação, Confronto, Especificação, Fase 0 Analítica, Resultados em GPU e Sincronização Git.
- **Git Continuous Delivery (`git_sync.py`):**
  - Sincronização automática para `https://github.com/elicksom15/LLM_PROJECT.git`.
  - Reconciliação com `git pull origin main --rebase`.
  - Exportação automática do `STATE.md` e `ledger.json`.

---

## 8. Políticas de Recuperação, Resiliência e Concorrência
- **Idempotência:** A reidratação do SQLite pode ser realizada a partir de `ledger.json` se o arquivo `.db` estiver ausente.
- **Tratamento de Rate-Limit / Cota:** Quando a API Xiaomi retorna erro `4005` ou `429`, o orquestrador entra em estado `PAUSED_QUOTA`, pausando por 60 segundos sem quebrar o loop.
- **Concorrência:** Atualmente single-threaded síncrono por ciclo de pesquisa. Não há pool dinâmico de agentes concorrentes nem escalonamento assíncrono de inferências.

---

## 9. Diagnóstico de Oportunidades para a Evolução da Inteligência Coletiva
1. **Grafo de Conhecimento Estruturado (Neo4j):**
   - Substituir a injeção de texto bruto linear por uma rede de nós (`Problem`, `Hypothesis`, `Evidence`, `Experiment`, `Result`, `Contradiction`, `Agent`, `Generation`) e arestas ponderadas.
2. **Três Dimensões de Pesos Independentes:**
   - Implementar nas arestas os pesos Semântico ($W_s$), Epistêmico ($W_e$) e Operacional ($W_o$), com atualização de feedback apenas mediante verificação objetiva e idempotente.
3. **Pool Hierárquico de 100 a 500 Agentes Lógicos:**
   - Desacoplar os processos físicos dos papéis lógicos, mantendo um pool de até 500 perfis especializados com ativação dinâmica e limite configurável de concorrência de inferência (ex: 4 concorrentes, 12 ativos simultâneos).
4. **Orquestrador de Grafo Dinâmico e Gerações Contínuas:**
   - O Grafo de Conhecimento dita o Grafo de Execução de cada Geração, identificando lacunas e contradições para acionar os agentes especializados correspondentes.
5. **Algoritmos de Grafo (GDS):**
   - Incorporar PageRank, Centralidade de Intermediação (Betweenness), Detecção de Comunidades (Leiden/Louvain) e Predição de Links com fallback resiliente.
