"""Enterprise Knowledge Graph & Semantic Memory — Sprint 24.2 / v7.2.0.

Design target: src/modules/enterprise-knowledge-graph → platform_enterprise_knowledge_graph.
Long-term semantic memory for Enterprise Platform. Additive to legacy KG/EKP.
AI uses shared context; owner controls what AI may use.
"""

from platform_enterprise_knowledge_graph.facade import EnterpriseKnowledgeGraphLibrary, enterprise_knowledge_graph_library

__all__ = ["EnterpriseKnowledgeGraphLibrary", "enterprise_knowledge_graph_library"]
