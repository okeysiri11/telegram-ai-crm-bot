# Deployment Engine — profiles and release steps for Port ERP 2.0.0.

from __future__ import annotations

from applications.port_erp.enterprise.models import DeploymentProfile
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


class DeploymentEngine:
    """Deployment profiles for production release."""

    DEFAULT_STEPS = [
        {"id": "pre.1", "step": "Validate configuration", "required": True},
        {"id": "pre.2", "step": "Verify application_version = 2.0.0", "required": True},
        {"id": "pre.3", "step": "Validate platform and ecosystem bridges", "required": True},
        {"id": "pre.4", "step": "Run readiness and release verification", "required": True},
        {"id": "deploy.1", "step": "Apply deployment profile", "required": True},
        {"id": "post.1", "step": "Health probe", "required": True},
    ]

    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def steps(self) -> list[dict]:
        return list(self.DEFAULT_STEPS)

    def save_profile(self, profile: DeploymentProfile) -> DeploymentProfile:
        if not profile.name:
            raise ValidationError("profile name is required")
        return self._store.deployment_profiles.save(profile.profile_id, profile)

    def get_profile(self, profile_id: str) -> DeploymentProfile:
        profile = self._store.deployment_profiles.get(profile_id)
        if profile is None:
            raise NotFoundError("deployment_profile", profile_id)
        return profile

    def list_profiles(self) -> list[DeploymentProfile]:
        return self._store.deployment_profiles.list_all()

    def ensure_production_profile(self) -> DeploymentProfile:
        for profile in self.list_profiles():
            if profile.environment == "production" and profile.name == "production":
                return profile
        return self.save_profile(
            DeploymentProfile(
                name="production",
                environment="production",
                replicas=2,
                region="global",
                feature_flags={
                    "enterprise_integration": True,
                    "global_network": True,
                    "digital_exchange": True,
                    "executive_dashboard": True,
                },
            )
        )


deployment_engine = DeploymentEngine()
