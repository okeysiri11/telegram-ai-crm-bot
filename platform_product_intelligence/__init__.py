"""Enterprise Product Intelligence — Sprint 22.0 / v6.1.0.

Design target: src/modules/product-intelligence (import path platform_product_intelligence).
AI never changes the system; owner approval is mandatory before development.
"""

from platform_product_intelligence.facade import ProductIntelligenceLibrary, product_intelligence_library

__all__ = ["ProductIntelligenceLibrary", "product_intelligence_library"]
