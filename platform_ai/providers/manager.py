"""Sprint 43.2 — unified Provider Manager (catalog · keys · health · fallback · generate)."""

from __future__ import annotations

import logging
from threading import Lock
from typing import Any

from platform_ai.providers.adapters import BaseProviderAdapter, build_default_adapters
from platform_ai.providers.models import (
    ProviderDef,
    ProviderHealth,
    ProviderResult,
    ProviderStatus,
)
from platform_ai.providers.vault import PROVIDER_KEY_NAMES, ProviderKeyVault, provider_key_vault

logger = logging.getLogger(__name__)


def _seed_catalog() -> list[ProviderDef]:
    """Canonical provider catalog — same connection shape for every vendor."""
    rows: list[tuple] = [
        # image
        ("openai_image", "OpenAI Images", "image", "https://api.openai.com/v1/images/generations", 0.04, "openai", ["flux_image", "stability_image", "local_image"]),
        ("flux_image", "Flux", "image", "https://api.bfl.ai/v1/flux", 0.05, "flux", ["openai_image", "local_image"]),
        ("recraft_image", "Recraft", "image", "https://external.api.recraft.ai/v1/images/generations", 0.04, "recraft", ["openai_image", "local_image"]),
        ("ideogram_image", "Ideogram", "image", "https://api.ideogram.ai/generate", 0.05, "ideogram", ["openai_image", "local_image"]),
        ("bfl_image", "Black Forest Labs", "image", "https://api.bfl.ai/v1/flux", 0.05, "bfl", ["flux_image", "local_image"]),
        ("stability_image", "Stability", "image", "https://api.stability.ai/v2beta/stable-image/generate/core", 0.04, "stability", ["openai_image", "local_image"]),
        ("fal_image", "Fal.ai", "image", "https://fal.run/fal-ai/flux/dev", 0.03, "fal", ["openai_image", "local_image"]),
        ("replicate_image", "Replicate", "image", "https://api.replicate.com/v1/predictions", 0.04, "replicate", ["openai_image", "local_image"]),
        ("local_image", "Local Image", "image", "local://image", 0.0, None, []),
        # video
        ("runway_video", "Runway", "video", "https://api.dev.runwayml.com/v1/image_to_video", 0.35, "runway", ["google_veo", "local_video"]),
        ("google_veo", "Google Veo", "video", "https://generativelanguage.googleapis.com/v1beta/veo", 0.40, "google", ["runway_video", "local_video"]),
        ("pika_video", "Pika", "video", "https://api.pika.art/v1/generate", 0.30, "pika", ["runway_video", "local_video"]),
        ("kling_video", "Kling", "video", "https://api.kling.ai/v1/videos/generations", 0.32, "kling", ["runway_video", "local_video"]),
        ("luma_video", "Luma Dream Machine", "video", "https://api.lumalabs.ai/dream-machine/v1/generations", 0.35, "luma", ["runway_video", "local_video"]),
        ("hailuo_video", "Hailuo", "video", "https://api.minimaxi.chat/v1/video_generation", 0.28, "hailuo", ["runway_video", "local_video"]),
        ("local_video", "Local Video", "video", "local://video", 0.0, None, []),
        # voice
        ("elevenlabs_voice", "ElevenLabs", "voice", "https://api.elevenlabs.io/v1/text-to-speech", 0.04, "elevenlabs", ["openai_voice", "local_voice"]),
        ("cartesia_voice", "Cartesia", "voice", "https://api.cartesia.ai/tts/bytes", 0.03, "cartesia", ["elevenlabs_voice", "local_voice"]),
        ("google_tts", "Google Speech", "voice", "https://texttospeech.googleapis.com/v1/text:synthesize", 0.02, "google", ["openai_voice", "local_voice"]),
        ("azure_speech", "Azure Speech", "voice", "https://eastus.tts.speech.microsoft.com/cognitiveservices/v1", 0.02, "azure", ["openai_voice", "local_voice"]),
        ("openai_voice", "OpenAI Voice", "voice", "https://api.openai.com/v1/audio/speech", 0.03, "openai", ["elevenlabs_voice", "local_voice"]),
        ("local_voice", "Local Voice", "voice", "local://voice", 0.0, None, []),
        # text
        ("openai_text", "OpenAI", "text", "https://api.openai.com/v1/chat/completions", 0.002, "openai", ["anthropic_text", "local_text"]),
        ("anthropic_text", "Anthropic Claude", "text", "https://api.anthropic.com/v1/messages", 0.003, "anthropic", ["openai_text", "local_text"]),
        ("gemini_text", "Gemini", "text", "https://generativelanguage.googleapis.com/v1beta/models", 0.002, "gemini", ["openai_text", "local_text"]),
        ("deepseek_text", "DeepSeek", "text", "https://api.deepseek.com/chat/completions", 0.001, "deepseek", ["openai_text", "local_text"]),
        ("mistral_text", "Mistral", "text", "https://api.mistral.ai/v1/chat/completions", 0.002, "mistral", ["openai_text", "local_text"]),
        ("local_text", "Local Text", "text", "local://text", 0.0, None, []),
        # music
        ("local_music", "Local Music", "music", "local://music", 0.05, None, []),
    ]
    out: list[ProviderDef] = []
    for pid, name, typ, api, cost, vendor, fb in rows:
        key_ref = PROVIDER_KEY_NAMES.get(vendor) if vendor else None
        out.append(
            ProviderDef(
                id=pid,
                name=name,
                type=typ,
                api=api,
                cost_unit=cost,
                limits={"rpm": 60, "concurrency": 4},
                status=ProviderStatus.UNKNOWN.value,
                key_ref=key_ref,
                fallback=list(fb),
                timeout_sec=45.0 if typ == "video" else 30.0,
                retry=2,
            )
        )
    return out


class ProviderManager:
    """Single connection point for all AI vendors."""

    VERSION = "43.2"

    def __init__(self, vault: ProviderKeyVault | None = None) -> None:
        self.vault = vault or provider_key_vault
        self._lock = Lock()
        self._providers: dict[str, ProviderDef] = {p.id: p for p in _seed_catalog()}
        self._adapters: dict[str, BaseProviderAdapter] = build_default_adapters(self.vault)
        self._health: dict[str, ProviderHealth] = {}

    def reset(self) -> None:
        with self._lock:
            self._providers = {p.id: p for p in _seed_catalog()}
            self._health.clear()
            self._adapters = build_default_adapters(self.vault)

    def register(self, provider: ProviderDef) -> ProviderDef:
        with self._lock:
            self._providers[provider.id] = provider
        return provider

    def get(self, provider_id: str) -> ProviderDef | None:
        return self._providers.get(provider_id)

    def list(self, *, type: str | None = None) -> list[ProviderDef]:
        rows = list(self._providers.values())
        if type:
            rows = [p for p in rows if p.type == type]
        return rows

    def catalog(self) -> dict[str, Any]:
        return {
            "version": self.VERSION,
            "providers": [p.to_dict() for p in self.list()],
            "keys": self.vault.list_status(),
            "count": len(self._providers),
        }

    def order_for(self, modality: str, preferred: str | None = None) -> list[str]:
        primary = [p.id for p in self.list(type=modality) if p.status != ProviderStatus.DISABLED.value]
        # prefer providers with keys first
        primary.sort(key=lambda pid: (0 if self._providers[pid].key_ref and self.vault.has(pid.split("_")[0]) else 1, pid))
        order: list[str] = []
        if preferred:
            order.append(preferred)
        for pid in primary:
            if pid not in order:
                order.append(pid)
        # expand fallbacks
        expanded: list[str] = []
        for pid in order:
            if pid not in expanded:
                expanded.append(pid)
            for fb in self._providers.get(pid, ProviderDef(pid, pid, modality, "", 0)).fallback:
                if fb not in expanded:
                    expanded.append(fb)
        local = f"local_{modality if modality != 'music' else 'music'}"
        if local not in expanded and local in self._providers:
            expanded.append(local)
        return expanded

    async def health_check(self, provider_id: str | None = None) -> list[ProviderHealth]:
        targets = [provider_id] if provider_id else list(self._providers.keys())
        results: list[ProviderHealth] = []
        for pid in targets:
            p = self._providers.get(pid)
            if not p:
                continue
            adapter = self._adapters.get(pid)
            if adapter is None:
                h = ProviderHealth(provider_id=pid, ok=False, status="error", message="Адаптер не найден")
            else:
                raw = await adapter.health_check(timeout_sec=min(5.0, p.timeout_sec))
                status = raw.get("status") or ("active" if raw.get("ok") else "error")
                h = ProviderHealth(
                    provider_id=pid,
                    ok=bool(raw.get("ok")),
                    status=status,
                    latency_ms=float(raw.get("latency_ms") or 0),
                    message=str(raw.get("message") or ""),
                    balance=raw.get("balance"),
                )
                p.status = status if status in {s.value for s in ProviderStatus} else ProviderStatus.UNKNOWN.value
                p.health = h.to_dict()
            self._health[pid] = h
            results.append(h)
        return results

    async def generate(
        self,
        modality: str,
        prompt: str,
        *,
        preferred: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ProviderResult:
        """Generate with automatic fallback — user never picks failover."""
        order = self.order_for(modality, preferred)
        tried: list[str] = []
        errors: list[str] = []
        for pid in order:
            p = self._providers.get(pid)
            if not p or p.status == ProviderStatus.DISABLED.value:
                continue
            adapter = self._adapters.get(pid)
            if adapter is None:
                continue
            tried.append(pid)
            try:
                # retries
                last_exc: Exception | None = None
                for _attempt in range(max(1, p.retry)):
                    try:
                        result = await adapter.generate(
                            prompt,
                            provider_id=pid,
                            timeout_sec=p.timeout_sec,
                            meta=meta,
                        )
                        result.failover_used = preferred is not None and pid != preferred
                        result.tried = tried
                        # apply catalog unit cost if sandbox zeroed oddly
                        if result.cost.total <= 0 and p.cost_unit > 0 and result.mode == "live":
                            result.cost.total = p.cost_unit
                        p.status = ProviderStatus.ACTIVE.value
                        return result
                    except Exception as exc:  # noqa: BLE001
                        last_exc = exc
                errors.append(f"{pid}: {last_exc}")
                p.status = ProviderStatus.ERROR.value
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{pid}: {exc}")
                p.status = ProviderStatus.ERROR.value
                logger.warning("provider_generate_failed id=%s err=%s", pid, exc)
        raise RuntimeError("Все провайдеры недоступны: " + "; ".join(errors[:5]))

    def enterprise_analytics(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        for p in self._providers.values():
            by_type[p.type] = by_type.get(p.type, 0) + 1
        with_key = sum(1 for k in self.vault.list_status() if k["configured"])
        health_ok = sum(1 for h in self._health.values() if h.ok)
        return {
            "providers_total": len(self._providers),
            "by_type": by_type,
            "keys_configured": with_key,
            "health_ok": health_ok,
            "health_checked": len(self._health),
            "top_models": [p.id for p in self.list() if p.status == ProviderStatus.ACTIVE.value][:10],
            "version": self.VERSION,
        }


provider_manager = ProviderManager()
