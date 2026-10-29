// ==============================================================================
// NEO4J SCHEMA MIGRATION: LLM_PROJECT COLLECTIVE INTELLIGENCE
// Constraints e Índices para o Grafo de Conhecimento e Execução
// ==============================================================================

// 1. UNIQUE IDENTIFIERS CONSTRAINTS
CREATE CONSTRAINT constraint_problem_id IF NOT EXISTS
FOR (n:Problem) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT constraint_hypothesis_id IF NOT EXISTS
FOR (n:Hypothesis) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT constraint_evidence_id IF NOT EXISTS
FOR (n:Evidence) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT constraint_source_id IF NOT EXISTS
FOR (n:Source) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT constraint_conclusion_id IF NOT EXISTS
FOR (n:Conclusion) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT constraint_contradiction_id IF NOT EXISTS
FOR (n:Contradiction) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT constraint_dependency_id IF NOT EXISTS
FOR (n:Dependency) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT constraint_experiment_id IF NOT EXISTS
FOR (n:Experiment) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT constraint_result_id IF NOT EXISTS
FOR (n:Result) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT constraint_agent_id IF NOT EXISTS
FOR (n:Agent) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT constraint_generation_id IF NOT EXISTS
FOR (n:Generation) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT constraint_strategy_id IF NOT EXISTS
FOR (n:Strategy) REQUIRE n.id IS UNIQUE;

CREATE CONSTRAINT constraint_reasoning_path_id IF NOT EXISTS
FOR (n:ReasoningPath) REQUIRE n.id IS UNIQUE;

// 2. SEARCH & LOOKUP INDEXES
CREATE INDEX index_hypothesis_status IF NOT EXISTS
FOR (n:Hypothesis) ON (n.validation_status);

CREATE INDEX index_hypothesis_created IF NOT EXISTS
FOR (n:Hypothesis) ON (n.created_at);

CREATE INDEX index_evidence_quality IF NOT EXISTS
FOR (n:Evidence) ON (n.quality_score);

CREATE INDEX index_result_verified IF NOT EXISTS
FOR (n:Result) ON (n.is_verified);

CREATE INDEX index_agent_role IF NOT EXISTS
FOR (n:Agent) ON (n.role);

CREATE INDEX index_generation_num IF NOT EXISTS
FOR (n:Generation) ON (n.generation_num);
