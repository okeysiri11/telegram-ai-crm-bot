# CRM module — Sprint 6.3 engine and models.

from applications.auto_marketplace.crm.engine import CRMEngine, crm_engine
from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMLeadStatus,
    CRMRole,
    CRMTask,
    CustomerProfile,
    DealStage,
    LeadSource,
    SalesOpportunity,
)
from applications.auto_marketplace.crm.service import CRMService, crm_service

__all__ = [
    "CRMDeal",
    "CRMEngine",
    "CRMLead",
    "CRMLeadStatus",
    "CRMRole",
    "CRMService",
    "CRMTask",
    "CustomerProfile",
    "DealStage",
    "LeadSource",
    "SalesOpportunity",
    "crm_engine",
    "crm_service",
]
