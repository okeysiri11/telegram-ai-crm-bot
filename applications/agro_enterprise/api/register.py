"""Register Agro Enterprise routes (Sprint 14.0 + 14.1)."""

from __future__ import annotations

from aiohttp import web

from applications.agro_enterprise.api import (
    agro_finance_handlers,
    ai_agronomist_handlers,
    controlled_environment_handlers,
    crop_ai_handlers,
    enterprise_certification_handlers,
    handlers,
    irrigation_handlers,
    precision_handlers,
    supply_chain_handlers,
)
from applications.agro_enterprise.api.middleware import auth_middleware
from applications.agro_enterprise.config import DEFAULT_CONFIG


def register_agro_enterprise_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/marketplace", handlers.marketplace_handler)
    app.router.add_post(f"{prefix}/marketplace", handlers.marketplace_handler)
    app.router.add_get(f"{prefix}/farms", handlers.farms_handler)
    app.router.add_post(f"{prefix}/farms", handlers.farms_handler)
    app.router.add_get(f"{prefix}/crops", handlers.crops_handler)
    app.router.add_post(f"{prefix}/crops", handlers.crops_handler)
    app.router.add_get(f"{prefix}/crm", handlers.crm_handler)
    app.router.add_post(f"{prefix}/crm", handlers.crm_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)

    # Sprint 14.1 — Precision Agriculture (additive)
    pa = DEFAULT_CONFIG.precision_agriculture_api_prefix
    app.router.add_get(f"{pa}/health", precision_handlers.pa_health_handler)
    app.router.add_post(f"{pa}/bootstrap", precision_handlers.pa_bootstrap_handler)
    app.router.add_get(f"{pa}/fields", precision_handlers.pa_fields_handler)
    app.router.add_post(f"{pa}/fields", precision_handlers.pa_fields_handler)
    app.router.add_get(f"{pa}/gis", precision_handlers.pa_gis_handler)
    app.router.add_post(f"{pa}/gis", precision_handlers.pa_gis_handler)
    app.router.add_get(f"{pa}/drone", precision_handlers.pa_drone_handler)
    app.router.add_post(f"{pa}/drone", precision_handlers.pa_drone_handler)
    app.router.add_get(f"{pa}/satellite", precision_handlers.pa_satellite_handler)
    app.router.add_post(f"{pa}/satellite", precision_handlers.pa_satellite_handler)
    app.router.add_get(f"{pa}/iot", precision_handlers.pa_iot_handler)
    app.router.add_post(f"{pa}/iot", precision_handlers.pa_iot_handler)
    app.router.add_get(f"{pa}/ai", precision_handlers.pa_ai_handler)
    app.router.add_post(f"{pa}/ai", precision_handlers.pa_ai_handler)
    app.router.add_get(f"{pa}/dashboard", precision_handlers.pa_dashboard_handler)
    app.router.add_post(f"{pa}/dashboard", precision_handlers.pa_dashboard_handler)
    app.router.add_get(f"{pa}/knowledge", precision_handlers.pa_knowledge_handler)
    app.router.add_post(f"{pa}/knowledge", precision_handlers.pa_knowledge_handler)

    # Sprint 14.2 — Smart Irrigation (additive; prior sprint routes unchanged)
    si = DEFAULT_CONFIG.smart_irrigation_api_prefix
    app.router.add_get(f"{si}/health", irrigation_handlers.si_health_handler)
    app.router.add_post(f"{si}/bootstrap", irrigation_handlers.si_bootstrap_handler)
    app.router.add_get(f"{si}/soil", irrigation_handlers.si_soil_handler)
    app.router.add_post(f"{si}/soil", irrigation_handlers.si_soil_handler)
    app.router.add_get(f"{si}/water", irrigation_handlers.si_water_handler)
    app.router.add_post(f"{si}/water", irrigation_handlers.si_water_handler)
    app.router.add_get(f"{si}/irrigation", irrigation_handlers.si_irrigation_handler)
    app.router.add_post(f"{si}/irrigation", irrigation_handlers.si_irrigation_handler)
    app.router.add_get(f"{si}/iot", irrigation_handlers.si_iot_handler)
    app.router.add_post(f"{si}/iot", irrigation_handlers.si_iot_handler)
    app.router.add_get(f"{si}/ai", irrigation_handlers.si_ai_handler)
    app.router.add_post(f"{si}/ai", irrigation_handlers.si_ai_handler)
    app.router.add_get(f"{si}/environment", irrigation_handlers.si_environment_handler)
    app.router.add_post(f"{si}/environment", irrigation_handlers.si_environment_handler)
    app.router.add_get(f"{si}/dashboard", irrigation_handlers.si_dashboard_handler)
    app.router.add_post(f"{si}/dashboard", irrigation_handlers.si_dashboard_handler)
    app.router.add_get(f"{si}/knowledge", irrigation_handlers.si_knowledge_handler)
    app.router.add_post(f"{si}/knowledge", irrigation_handlers.si_knowledge_handler)

    # Sprint 14.3 — Crop AI (additive; prior sprint routes unchanged)
    ca = DEFAULT_CONFIG.crop_ai_api_prefix
    app.router.add_get(f"{ca}/health", crop_ai_handlers.ca_health_handler)
    app.router.add_post(f"{ca}/bootstrap", crop_ai_handlers.ca_bootstrap_handler)
    app.router.add_get(f"{ca}/crops", crop_ai_handlers.ca_crops_handler)
    app.router.add_post(f"{ca}/crops", crop_ai_handlers.ca_crops_handler)
    app.router.add_get(f"{ca}/disease", crop_ai_handlers.ca_disease_handler)
    app.router.add_post(f"{ca}/disease", crop_ai_handlers.ca_disease_handler)
    app.router.add_get(f"{ca}/pests", crop_ai_handlers.ca_pest_handler)
    app.router.add_post(f"{ca}/pests", crop_ai_handlers.ca_pest_handler)
    app.router.add_get(f"{ca}/yield", crop_ai_handlers.ca_yield_handler)
    app.router.add_post(f"{ca}/yield", crop_ai_handlers.ca_yield_handler)
    app.router.add_get(f"{ca}/ops", crop_ai_handlers.ca_ops_handler)
    app.router.add_post(f"{ca}/ops", crop_ai_handlers.ca_ops_handler)
    app.router.add_get(f"{ca}/decisions", crop_ai_handlers.ca_decisions_handler)
    app.router.add_post(f"{ca}/decisions", crop_ai_handlers.ca_decisions_handler)
    app.router.add_get(f"{ca}/dashboard", crop_ai_handlers.ca_dashboard_handler)
    app.router.add_post(f"{ca}/dashboard", crop_ai_handlers.ca_dashboard_handler)
    app.router.add_get(f"{ca}/knowledge", crop_ai_handlers.ca_knowledge_handler)
    app.router.add_post(f"{ca}/knowledge", crop_ai_handlers.ca_knowledge_handler)

    # Sprint 14.4 — Controlled Environment (additive; prior sprint routes unchanged)
    ce = DEFAULT_CONFIG.controlled_environment_api_prefix
    app.router.add_get(f"{ce}/health", controlled_environment_handlers.ce_health_handler)
    app.router.add_post(f"{ce}/bootstrap", controlled_environment_handlers.ce_bootstrap_handler)
    app.router.add_get(f"{ce}/greenhouse", controlled_environment_handlers.ce_greenhouse_handler)
    app.router.add_post(f"{ce}/greenhouse", controlled_environment_handlers.ce_greenhouse_handler)
    app.router.add_get(f"{ce}/climate-ai", controlled_environment_handlers.ce_climate_ai_handler)
    app.router.add_post(f"{ce}/climate-ai", controlled_environment_handlers.ce_climate_ai_handler)
    app.router.add_get(f"{ce}/livestock", controlled_environment_handlers.ce_livestock_handler)
    app.router.add_post(f"{ce}/livestock", controlled_environment_handlers.ce_livestock_handler)
    app.router.add_get(f"{ce}/poultry", controlled_environment_handlers.ce_poultry_handler)
    app.router.add_post(f"{ce}/poultry", controlled_environment_handlers.ce_poultry_handler)
    app.router.add_get(f"{ce}/aquaculture", controlled_environment_handlers.ce_aquaculture_handler)
    app.router.add_post(f"{ce}/aquaculture", controlled_environment_handlers.ce_aquaculture_handler)
    app.router.add_get(f"{ce}/biosecurity", controlled_environment_handlers.ce_biosecurity_handler)
    app.router.add_post(f"{ce}/biosecurity", controlled_environment_handlers.ce_biosecurity_handler)
    app.router.add_get(f"{ce}/dashboard", controlled_environment_handlers.ce_dashboard_handler)
    app.router.add_post(f"{ce}/dashboard", controlled_environment_handlers.ce_dashboard_handler)
    app.router.add_get(f"{ce}/knowledge", controlled_environment_handlers.ce_knowledge_handler)
    app.router.add_post(f"{ce}/knowledge", controlled_environment_handlers.ce_knowledge_handler)

    # Sprint 14.5 — Agro Supply Chain (additive; prior sprint routes unchanged)
    sc = DEFAULT_CONFIG.supply_chain_api_prefix
    app.router.add_get(f"{sc}/health", supply_chain_handlers.sc_health_handler)
    app.router.add_post(f"{sc}/bootstrap", supply_chain_handlers.sc_bootstrap_handler)
    app.router.add_get(f"{sc}/supply", supply_chain_handlers.sc_supply_handler)
    app.router.add_post(f"{sc}/supply", supply_chain_handlers.sc_supply_handler)
    app.router.add_get(f"{sc}/elevator", supply_chain_handlers.sc_elevator_handler)
    app.router.add_post(f"{sc}/elevator", supply_chain_handlers.sc_elevator_handler)
    app.router.add_get(f"{sc}/quality", supply_chain_handlers.sc_quality_handler)
    app.router.add_post(f"{sc}/quality", supply_chain_handlers.sc_quality_handler)
    app.router.add_get(f"{sc}/warehouse", supply_chain_handlers.sc_warehouse_handler)
    app.router.add_post(f"{sc}/warehouse", supply_chain_handlers.sc_warehouse_handler)
    app.router.add_get(f"{sc}/logistics", supply_chain_handlers.sc_logistics_handler)
    app.router.add_post(f"{sc}/logistics", supply_chain_handlers.sc_logistics_handler)
    app.router.add_get(f"{sc}/export", supply_chain_handlers.sc_export_handler)
    app.router.add_post(f"{sc}/export", supply_chain_handlers.sc_export_handler)
    app.router.add_get(f"{sc}/dashboard", supply_chain_handlers.sc_dashboard_handler)
    app.router.add_post(f"{sc}/dashboard", supply_chain_handlers.sc_dashboard_handler)
    app.router.add_get(f"{sc}/knowledge", supply_chain_handlers.sc_knowledge_handler)
    app.router.add_post(f"{sc}/knowledge", supply_chain_handlers.sc_knowledge_handler)

    # Sprint 14.6 — Agro Finance (additive; prior sprint routes unchanged)
    af = DEFAULT_CONFIG.agro_finance_api_prefix
    app.router.add_get(f"{af}/health", agro_finance_handlers.af_health_handler)
    app.router.add_post(f"{af}/bootstrap", agro_finance_handlers.af_bootstrap_handler)
    app.router.add_get(f"{af}/exchange", agro_finance_handlers.af_exchange_handler)
    app.router.add_post(f"{af}/exchange", agro_finance_handlers.af_exchange_handler)
    app.router.add_get(f"{af}/contracts", agro_finance_handlers.af_contracts_handler)
    app.router.add_post(f"{af}/contracts", agro_finance_handlers.af_contracts_handler)
    app.router.add_get(f"{af}/finance", agro_finance_handlers.af_finance_handler)
    app.router.add_post(f"{af}/finance", agro_finance_handlers.af_finance_handler)
    app.router.add_get(f"{af}/insurance", agro_finance_handlers.af_insurance_handler)
    app.router.add_post(f"{af}/insurance", agro_finance_handlers.af_insurance_handler)
    app.router.add_get(f"{af}/risk", agro_finance_handlers.af_risk_handler)
    app.router.add_post(f"{af}/risk", agro_finance_handlers.af_risk_handler)
    app.router.add_get(f"{af}/market", agro_finance_handlers.af_market_handler)
    app.router.add_post(f"{af}/market", agro_finance_handlers.af_market_handler)
    app.router.add_get(f"{af}/dashboard", agro_finance_handlers.af_dashboard_handler)
    app.router.add_post(f"{af}/dashboard", agro_finance_handlers.af_dashboard_handler)
    app.router.add_get(f"{af}/knowledge", agro_finance_handlers.af_knowledge_handler)
    app.router.add_post(f"{af}/knowledge", agro_finance_handlers.af_knowledge_handler)

    # Sprint 14.7 — AI Agronomist (additive; prior sprint routes unchanged)
    aa = DEFAULT_CONFIG.ai_agronomist_api_prefix
    app.router.add_get(f"{aa}/health", ai_agronomist_handlers.aa_health_handler)
    app.router.add_post(f"{aa}/bootstrap", ai_agronomist_handlers.aa_bootstrap_handler)
    app.router.add_get(f"{aa}/agronomist", ai_agronomist_handlers.aa_agronomist_handler)
    app.router.add_post(f"{aa}/agronomist", ai_agronomist_handlers.aa_agronomist_handler)
    app.router.add_get(f"{aa}/decisions", ai_agronomist_handlers.aa_decisions_handler)
    app.router.add_post(f"{aa}/decisions", ai_agronomist_handlers.aa_decisions_handler)
    app.router.add_get(f"{aa}/planning", ai_agronomist_handlers.aa_planning_handler)
    app.router.add_post(f"{aa}/planning", ai_agronomist_handlers.aa_planning_handler)
    app.router.add_get(f"{aa}/forecast", ai_agronomist_handlers.aa_forecast_handler)
    app.router.add_post(f"{aa}/forecast", ai_agronomist_handlers.aa_forecast_handler)
    app.router.add_get(f"{aa}/optimization", ai_agronomist_handlers.aa_optimization_handler)
    app.router.add_post(f"{aa}/optimization", ai_agronomist_handlers.aa_optimization_handler)
    app.router.add_get(f"{aa}/executive", ai_agronomist_handlers.aa_executive_handler)
    app.router.add_post(f"{aa}/executive", ai_agronomist_handlers.aa_executive_handler)
    app.router.add_get(f"{aa}/dashboard", ai_agronomist_handlers.aa_dashboard_handler)
    app.router.add_post(f"{aa}/dashboard", ai_agronomist_handlers.aa_dashboard_handler)
    app.router.add_get(f"{aa}/knowledge", ai_agronomist_handlers.aa_knowledge_handler)
    app.router.add_post(f"{aa}/knowledge", ai_agronomist_handlers.aa_knowledge_handler)

    # Sprint 14.8 — Agro Enterprise Certification (additive; prior sprint routes unchanged)
    aec = DEFAULT_CONFIG.enterprise_certification_api_prefix
    app.router.add_get(f"{aec}/health", enterprise_certification_handlers.aec_health_handler)
    app.router.add_post(f"{aec}/bootstrap", enterprise_certification_handlers.aec_bootstrap_handler)
    app.router.add_get(f"{aec}/architecture", enterprise_certification_handlers.aec_architecture_handler)
    app.router.add_get(f"{aec}/integration", enterprise_certification_handlers.aec_integration_handler)
    app.router.add_get(f"{aec}/performance", enterprise_certification_handlers.aec_performance_handler)
    app.router.add_get(f"{aec}/security", enterprise_certification_handlers.aec_security_handler)
    app.router.add_get(f"{aec}/documentation", enterprise_certification_handlers.aec_documentation_handler)
    app.router.add_get(f"{aec}/quality", enterprise_certification_handlers.aec_quality_handler)
    app.router.add_post(f"{aec}/quality", enterprise_certification_handlers.aec_quality_handler)
    app.router.add_get(f"{aec}/release", enterprise_certification_handlers.aec_release_handler)
    app.router.add_get(f"{aec}/executive", enterprise_certification_handlers.aec_executive_handler)
    app.router.add_get(f"{aec}/dashboard", enterprise_certification_handlers.aec_dashboard_handler)
    app.router.add_post(f"{aec}/dashboard", enterprise_certification_handlers.aec_dashboard_handler)
