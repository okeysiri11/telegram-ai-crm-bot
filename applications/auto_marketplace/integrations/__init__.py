from applications.auto_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge

__all__ = [
    "PlatformBridge",
    "platform_bridge",
    "EcosystemBridge",
    "ecosystem_bridge",
    "AgroMarketplaceBridge",
    "agro_marketplace_bridge",
    "PortERPBridge",
    "port_erp_bridge",
    "CrossPlatformIntegrationEngine",
    "cross_platform_integration_engine",
]


def __getattr__(name: str):
    if name in {"EcosystemBridge", "ecosystem_bridge"}:
        from applications.auto_marketplace.integrations.ecosystem_bridge import EcosystemBridge, ecosystem_bridge

        return EcosystemBridge if name == "EcosystemBridge" else ecosystem_bridge
    if name in {"AgroMarketplaceBridge", "agro_marketplace_bridge"}:
        from applications.auto_marketplace.integrations.agro_bridge import AgroMarketplaceBridge, agro_marketplace_bridge

        return AgroMarketplaceBridge if name == "AgroMarketplaceBridge" else agro_marketplace_bridge
    if name in {"PortERPBridge", "port_erp_bridge"}:
        from applications.auto_marketplace.integrations.port_bridge import PortERPBridge, port_erp_bridge

        return PortERPBridge if name == "PortERPBridge" else port_erp_bridge
    if name in {"CrossPlatformIntegrationEngine", "cross_platform_integration_engine"}:
        from applications.auto_marketplace.integrations.cross_platform import (
            CrossPlatformIntegrationEngine,
            cross_platform_integration_engine,
        )

        return (
            CrossPlatformIntegrationEngine
            if name == "CrossPlatformIntegrationEngine"
            else cross_platform_integration_engine
        )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
