"""Enterprise Learning & Continuous Improvement Engine — Sprint 24.8 / v7.8.0.

Design target: src/modules/enterprise-learning-engine → platform_enterprise_learning_engine.
Confirmed outcomes only. Owner or trust policy must approve new knowledge before use.
AI never self-modifies algorithms or learns from unconfirmed data.
"""

from platform_enterprise_learning_engine.facade import LearningEngineLibrary, learning_engine_library

__all__ = ["LearningEngineLibrary", "learning_engine_library"]
