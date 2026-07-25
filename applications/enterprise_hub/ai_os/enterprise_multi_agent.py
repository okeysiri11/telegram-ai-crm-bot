"""Sprint 27.1 bridge — Multi-Agent Executive Layer.

Legacy Autonomous AIOS (Sprint 20.4) remains in this package (`facade.py` / `api.py`).
Multi-Agent OS suite lives in `applications.enterprise_hub.enterprise_ai_os`.
"""

from applications.enterprise_hub.enterprise_ai_os.facade import EnterpriseAIOSSuite, enterprise_ai_os

__all__ = ["EnterpriseAIOSSuite", "enterprise_ai_os"]
