# ⚡ Dual MiMo Autonomous Research Engine (LLM_PROJECT)

[![Research Cycles](https://img.shields.io/badge/Cycles-73-blue.svg)](#)
[![Approved Hypotheses](https://img.shields.io/badge/Approved-7-success.svg)](#)
[![Hardware](https://img.shields.io/badge/GPU-RTX%203060%2012GB-76B900.svg)](#)
[![Methodology](https://img.shields.io/badge/Method-Cálculo%20Primeiro%20(Fase%200)-orange.svg)](#)

Motor de pesquisa científica autônomo 24/7 alimentado por instâncias duais do modelo **MiMo-V2.6 (UltraSpeed & Pro)** debatendo em regime adversarial para **reduzir o poder computacional e viabilizar a execução de LLMs gigantes (como Qwen 32B) em uma RTX 3060 12GB sem quantização convencional**.

---

### 🎯 Missão Principal
Desenvolver uma formulação matemática inédita que reduza o custo computacional e o tráfego de memória de inferência autorregressiva em mais de **75% a 85%**, eliminando as perdas de precisão das quantizações convencionais (AWQ/GPTQ) através de:
- **Álgebra de Subespaços Invariantes de Krylov**
- **Transporte Paralelo Espectral entre Camadas**
- **Splitting de Strang e Operadores Anti-simétricos Simpléticos**

---

### 🧮 Diretriz: Cálculo Primeiro, GPU Depois (Fase 0)
1. **Auditoria Matemática:** Antes de acionar a GPU, os operadores são auditados formalmente no papel. Se a redução teórica de FLOPs e tráfego de VRAM for $< 75%$, a hipótese é **imediatamente rejeitada**, poupando ciclos físicos da RTX 3060.
2. **Validação Física em GPU:** Modelos aprovados no cálculo são compilados e medidos na bancada física local (`~3B GPT`), aferindo throughput real (tokens/s), divergência KL e acurácia Top-1.
3. **Persistência e Telemetria em Tempo Real:** Todos os ciclos, teses e pareceres são registrados em SQLite e transmitidos ao Discord com sincronização contínua neste repositório.

Para conferir o relatório completo de todos os ciclos executados, acesse:
👉 **[Ver Estado e Ledger Completo (STATE.md)](STATE.md)**
