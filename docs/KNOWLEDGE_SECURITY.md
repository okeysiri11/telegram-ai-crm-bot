# Knowledge Security

**Sprint:** 32.4 · **Module:** `platform_security.knowledge_security.KnowledgeSecurity`

## Protects

Knowledge Base · RAG · Embeddings · Vector DB · Documents · Semantic Search · Context Windows

## Rules

- Tenant required for vector / semantic retrieval
- Sensitivity levels: public < internal < confidential < restricted
- Context windows truncated by policy
- Encryption required for confidential / restricted documents

Canonical knowledge SoR remains `platform_enterprise_knowledge_graph` (Sprint 32.3). This module is the **security policy** layer only.
