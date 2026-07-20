# Vehicle media models.

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class MediaType(str, enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"
    IMAGE_360 = "360_image"
    DOCUMENT = "document"


@dataclass
class VehicleMedia:
    media_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vehicle_id: str = ""
    media_type: MediaType = MediaType.PHOTO
    url: str = ""
    thumbnail_url: str = ""
    caption: str = ""
    sort_order: int = 0
    optimized: bool = False
    file_size_bytes: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    uploaded_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "media_id": self.media_id,
            "vehicle_id": self.vehicle_id,
            "media_type": self.media_type.value,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "caption": self.caption,
            "sort_order": self.sort_order,
            "optimized": self.optimized,
            "file_size_bytes": self.file_size_bytes,
            "metadata": dict(self.metadata),
            "uploaded_at": self.uploaded_at,
        }
