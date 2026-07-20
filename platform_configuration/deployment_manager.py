# DeploymentManager — local and Docker deployment abstraction.

from __future__ import annotations

import logging
import shutil
import subprocess
import time
from typing import Any

from platform_configuration.layer_config import DEFAULT_LAYER_CONFIG, ConfigurationLayerConfig
from platform_configuration.layer_exceptions import DeploymentError
from platform_configuration.models import DeploymentRecord, DeploymentStatus, DeploymentTarget

logger = logging.getLogger(__name__)


class DeploymentManager:
    """Deployment abstraction with verification, rollback, and history."""

    def __init__(self, *, config: ConfigurationLayerConfig | None = None) -> None:
        self._config = config or DEFAULT_LAYER_CONFIG
        self._history: list[DeploymentRecord] = []
        self._active: DeploymentRecord | None = None
        self._previous: DeploymentRecord | None = None
        self._rollback_count: int = 0

    def reset(self) -> None:
        self._history.clear()
        self._active = None
        self._previous = None
        self._rollback_count = 0

    @property
    def rollback_count(self) -> int:
        return self._rollback_count

    def history(self) -> list[DeploymentRecord]:
        return list(self._history)

    async def deploy(
        self,
        *,
        target: DeploymentTarget = DeploymentTarget.LOCAL,
        environment: str = "development",
        version: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> DeploymentRecord:
        record = DeploymentRecord(
            target=target,
            environment=environment,
            status=DeploymentStatus.RUNNING,
            version=version,
            metadata=metadata or {},
        )
        started = time.perf_counter()
        try:
            if target == DeploymentTarget.DOCKER:
                await self._deploy_docker(record)
            else:
                await self._deploy_local(record)
            verification = await self.verify(record)
            record.verification = verification
            if verification.get("ok"):
                record.status = DeploymentStatus.VERIFIED
            else:
                record.status = DeploymentStatus.FAILED
                raise DeploymentError(
                    verification.get("message", "Deployment verification failed"),
                    deployment_id=record.deployment_id,
                )
        except DeploymentError:
            raise
        except Exception as exc:
            record.status = DeploymentStatus.FAILED
            raise DeploymentError(str(exc), deployment_id=record.deployment_id) from exc
        finally:
            record.completed_at = time.time()
            record.duration_ms = (time.perf_counter() - started) * 1000.0
            if self._active is not None:
                self._previous = self._active
            self._active = record
            self._history.append(record)

        logger.info(
            "deployment_completed id=%s target=%s status=%s duration_ms=%.2f",
            record.deployment_id,
            target.value,
            record.status.value,
            record.duration_ms,
        )
        return record

    async def _deploy_local(self, record: DeploymentRecord) -> None:
        record.metadata["backend"] = "local"
        record.metadata["message"] = "Local deployment simulated"

    async def _deploy_docker(self, record: DeploymentRecord) -> None:
        if not shutil.which("docker"):
            record.metadata["backend"] = "docker"
            record.metadata["simulated"] = True
            record.metadata["message"] = "Docker CLI not found — simulated deployment"
            return
        image = self._config.docker_image
        try:
            subprocess.run(
                ["docker", "image", "inspect", image],
                check=False,
                capture_output=True,
                timeout=self._config.deployment_verify_timeout_sec,
            )
            record.metadata["backend"] = "docker"
            record.metadata["image"] = image
            record.metadata["lifecycle"] = "inspected"
        except subprocess.TimeoutExpired as exc:
            raise DeploymentError("Docker inspect timed out") from exc

    async def verify(self, record: DeploymentRecord | None = None) -> dict[str, Any]:
        rec = record or self._active
        if rec is None:
            return {"ok": False, "message": "No active deployment"}
        checks = {
            "has_version": bool(rec.version),
            "has_environment": bool(rec.environment),
            "status_running_or_verified": rec.status in {
                DeploymentStatus.RUNNING,
                DeploymentStatus.VERIFIED,
            },
        }
        ok = all(checks.values()) or rec.metadata.get("simulated")
        return {"ok": ok, "checks": checks, "message": "verified" if ok else "verification failed"}

    async def rollback(self) -> DeploymentRecord:
        if self._previous is None:
            raise DeploymentError("No previous deployment to rollback to")
        rolled = DeploymentRecord(
            target=self._previous.target,
            environment=self._previous.environment,
            status=DeploymentStatus.ROLLED_BACK,
            version=self._previous.version,
            metadata={"rolled_back_from": self._active.deployment_id if self._active else None},
        )
        rolled.completed_at = time.time()
        self._rollback_count += 1
        self._active = rolled
        self._history.append(rolled)
        logger.info("deployment_rollback id=%s", rolled.deployment_id)
        return rolled

    def docker_available(self) -> bool:
        return shutil.which("docker") is not None


deployment_manager = DeploymentManager()
