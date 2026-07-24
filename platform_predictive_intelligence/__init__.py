"""Enterprise Predictive Intelligence Engine — Sprint 24.3 / v7.3.0.

Design target: src/modules/predictive-intelligence → platform_predictive_intelligence.
Unified forecasting layer for Enterprise AI Platform. AI recommends only — never acts alone.
Distinct from Product Intelligence (EPI).
"""

from platform_predictive_intelligence.facade import PredictiveIntelligenceLibrary, predictive_intelligence_library

__all__ = ["PredictiveIntelligenceLibrary", "predictive_intelligence_library"]
