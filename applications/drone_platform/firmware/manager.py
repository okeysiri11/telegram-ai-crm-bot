from __future__ import annotations

from typing import Any

from applications.drone_platform.firmware.analyzer import FirmwareAnalyzer, firmware_analyzer
from applications.drone_platform.firmware.builder import FirmwareBuilder, firmware_builder
from applications.drone_platform.firmware.comparator import FirmwareComparator, firmware_comparator
from applications.drone_platform.firmware.configuration import (
    FirmwareConfigurationManager,
    firmware_configuration_manager,
)
from applications.drone_platform.firmware.patches import FirmwarePatchManager, firmware_patch_manager
from applications.drone_platform.firmware.releases import FirmwareReleaseManager, firmware_release_manager
from applications.drone_platform.firmware.repository import FirmwareRepository, firmware_repository
from applications.drone_platform.firmware.rollback import FirmwareRollbackManager, firmware_rollback_manager
from applications.drone_platform.firmware.service import FirmwareService, firmware_service
from applications.drone_platform.firmware.signing import FirmwareSigning, firmware_signing
from applications.drone_platform.firmware.versions import FirmwareVersionManager, firmware_version_manager


class FirmwareManager:
    """Unified firmware intelligence facade (Sprint 11.2)."""

    def __init__(
        self,
        service: FirmwareService | None = None,
        repository: FirmwareRepository | None = None,
        versions: FirmwareVersionManager | None = None,
        builder: FirmwareBuilder | None = None,
        analyzer: FirmwareAnalyzer | None = None,
        comparator: FirmwareComparator | None = None,
        patches: FirmwarePatchManager | None = None,
        configuration: FirmwareConfigurationManager | None = None,
        rollback: FirmwareRollbackManager | None = None,
        signing: FirmwareSigning | None = None,
        releases: FirmwareReleaseManager | None = None,
    ) -> None:
        self.service = service or firmware_service
        self.repository = repository or firmware_repository
        self.versions = versions or firmware_version_manager
        self.builder = builder or firmware_builder
        self.analyzer = analyzer or firmware_analyzer
        self.comparator = comparator or firmware_comparator
        self.patches = patches or firmware_patch_manager
        self.configuration = configuration or firmware_configuration_manager
        self.rollback = rollback or firmware_rollback_manager
        self.signing = signing or firmware_signing
        self.releases = releases or firmware_release_manager

    def status(self) -> dict[str, Any]:
        return {
            "firmware_intelligence": "1.0",
            "stacks": self.service.supported_stacks(),
            "artifact_count": self.repository.store.firmware_artifacts.count(),
            "build_count": self.builder.store.firmware_builds.count(),
            "release_count": self.releases.store.firmware_releases.count(),
            "capabilities": [
                "repository",
                "versions",
                "builder",
                "analyzer",
                "comparator",
                "patches",
                "configuration",
                "rollback",
                "signing",
                "releases",
            ],
        }


firmware_manager = FirmwareManager()
