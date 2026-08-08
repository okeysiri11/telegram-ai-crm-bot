"""Provider Layer facade for Telegram Super App — no vendor SDKs here.

Routes image/video/voice/text through Creative Factory MediaProviderManager
and publish channels through Creative Factory PublishChannel model.
"""

from __future__ import annotations

from typing import Any

from platform_ai.creative_engine import CreativeFactoryEngine, MediaProviderManager
from platform_ai.creative_models import PublishChannel

# Capability → ordered provider ids (Provider Layer, not Telegram-bound).
IMAGE_PROVIDERS = (
    "openai_image",
    "google_imagen",
    "flux_image",
    "stability_image",
    "ideogram_image",
    "recraft_image",
    "bfl_image",
    "local_image",
)

VIDEO_PROVIDERS = (
    "google_veo",
    "runway_video",
    "pika_video",
    "kling_video",
    "luma_video",
    "hailuo_video",
    "local_video",
)

VOICE_PROVIDERS = (
    "openai_voice",
    "elevenlabs_voice",
    "cartesia_voice",
    "azure_speech",
    "google_tts",
    "local_voice",
)

TEXT_PROVIDERS = ("openai_text", "anthropic_text", "openrouter_text", "local_text")

PUBLISH_PROVIDERS = (
    "instagram_publish",
    "facebook_publish",
    "tiktok_publish",
    "youtube_publish",
    "telegram_publish",
    "linkedin_publish",
)


def _ensure_extended_providers(media: MediaProviderManager) -> None:
    """Register Sprint 43.0 media providers without removing existing ones."""
    extra: list[tuple[str, str]] = [
        ("google_imagen", "image"),
        ("flux_image", "image"),
        ("ideogram_image", "image"),
        ("recraft_image", "image"),
        ("bfl_image", "image"),
        ("google_veo", "video"),
        ("pika_video", "video"),
        ("kling_video", "video"),
        ("luma_video", "video"),
        ("hailuo_video", "video"),
        ("cartesia_voice", "voice"),
        ("azure_speech", "voice"),
        ("google_tts", "voice"),
        ("openrouter_text", "text"),
    ]
    for pid, modality in extra:
        if pid not in media.providers:
            media.providers[pid] = {
                "provider_id": pid,
                "modality": modality,
                "available": True,
                "label": pid.replace("_", " ").title(),
            }
    media.fallback["image"] = list(IMAGE_PROVIDERS)
    media.fallback["video"] = list(VIDEO_PROVIDERS)
    media.fallback["voice"] = list(VOICE_PROVIDERS)
    media.fallback["text"] = list(TEXT_PROVIDERS)


class SuperAppProviderFacade:
    """Thin facade: Telegram → Provider Layer only."""

    def __init__(self, factory: CreativeFactoryEngine | None = None) -> None:
        self.factory = factory or CreativeFactoryEngine()
        _ensure_extended_providers(self.factory.media)

    def list_providers(self, modality: str | None = None) -> list[dict[str, Any]]:
        return self.factory.media.list_providers(modality=modality)

    def provider_ids(self, modality: str) -> list[str]:
        mapping = {
            "image": IMAGE_PROVIDERS,
            "video": VIDEO_PROVIDERS,
            "voice": VOICE_PROVIDERS,
            "text": TEXT_PROVIDERS,
        }
        return list(mapping.get(modality, ()))

    async def generate(
        self,
        modality: str,
        prompt: str,
        *,
        preferred: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = await self.factory.media.generate(
            modality,
            prompt,
            preferred=preferred,
        )
        result["meta"] = meta or {}
        result["via"] = "provider_layer"
        return result

    def prepare_publish(
        self,
        *,
        channel: str,
        asset_ref: str,
        caption: str,
        schedule_at: str | None = None,
    ) -> dict[str, Any]:
        """Architectural publish prep — no direct network to social APIs."""
        ch = channel.lower().strip()
        provider_id = f"{ch}_publish" if not ch.endswith("_publish") else ch
        if provider_id not in PUBLISH_PROVIDERS and ch not in {c.replace("_publish", "") for c in PUBLISH_PROVIDERS}:
            raise ValueError(f"Неизвестный канал публикации: {channel}")
        job = {
            "status": "prepared",
            "channel": ch,
            "provider_id": provider_id if provider_id in PUBLISH_PROVIDERS else f"{ch}_publish",
            "asset_ref": asset_ref,
            "caption": caption,
            "schedule_at": schedule_at,
            "message": "Публикация подготовлена через Provider Layer. Исполнение — после подключения адаптера канала.",
        }
        # Keep Creative Factory publish model aligned when channel enum exists.
        try:
            PublishChannel(ch)  # type: ignore[arg-type]
        except Exception:
            pass
        return job


super_app_providers = SuperAppProviderFacade()
