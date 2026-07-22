from __future__ import annotations

from typing import Any

from applications.drone_platform.firmware.analyzer import FirmwareAnalyzer, firmware_analyzer
from applications.drone_platform.firmware.repository import FirmwareRepository, firmware_repository
from applications.drone_platform.firmware.service import FirmwareService, firmware_service


class FirmwareComparator:
    def __init__(
        self,
        firmware: FirmwareService | None = None,
        repository: FirmwareRepository | None = None,
        analyzer: FirmwareAnalyzer | None = None,
    ) -> None:
        self.firmware = firmware or firmware_service
        self.repository = repository or firmware_repository
        self.analyzer = analyzer or firmware_analyzer

    def compare_parameters(self, left_id: str, right_id: str) -> dict[str, Any]:
        return self.firmware.compare_parameters(left_id, right_id)

    def compare_artifacts(self, left_artifact_id: str, right_artifact_id: str) -> dict[str, Any]:
        left = self.repository.get(left_artifact_id)
        right = self.repository.get(right_artifact_id)
        result: dict[str, Any] = {
            "left_id": left_artifact_id,
            "right_id": right_artifact_id,
            "same_sha256": left.get("sha256") == right.get("sha256"),
            "left_type": left.get("artifact_type"),
            "right_type": right.get("artifact_type"),
        }
        if str(left.get("artifact_type", "")).endswith("param") or left.get("artifact_type") == ".param":
            lp = self.analyzer.parse_param_file(left.get("content") or "")
            rp = self.analyzer.parse_param_file(right.get("content") or "")
            keys = set(lp) | set(rp)
            changed = []
            only_left, only_right = [], []
            for k in sorted(keys):
                if k in lp and k not in rp:
                    only_left.append(k)
                elif k in rp and k not in lp:
                    only_right.append(k)
                elif lp[k] != rp[k]:
                    changed.append({"parameter": k, "left": lp[k], "right": rp[k]})
            result.update({"changed": changed, "only_left": only_left, "only_right": only_right})
        return result

    def compare_releases(self, left_release_id: str, right_release_id: str, store) -> dict[str, Any]:
        left = store.firmware_releases.get(left_release_id)
        right = store.firmware_releases.get(right_release_id)
        return {
            "left": left,
            "right": right,
            "version_changed": (left or {}).get("version") != (right or {}).get("version"),
            "notes_diff": {
                "left": (left or {}).get("notes", ""),
                "right": (right or {}).get("notes", ""),
            },
        }


firmware_comparator = FirmwareComparator()
