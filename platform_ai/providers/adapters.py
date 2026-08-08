"""Sprint 43.2 — provider adapters (live when key present, sandbox otherwise)."""

from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import Any

import aiohttp

from platform_ai.providers.models import GenerationCost, ProviderResult
from platform_ai.providers.vault import ProviderKeyVault, provider_key_vault

logger = logging.getLogger(__name__)


def _live_enabled() -> bool:
    return os.environ.get("ADOS_AI_LIVE", "").lower() in ("1", "true", "yes")


class BaseProviderAdapter:
    vendor: str = "local"
    modality: str = "text"
    default_endpoint: str = ""

    def __init__(self, vault: ProviderKeyVault | None = None) -> None:
        self.vault = vault or provider_key_vault

    def api_key(self) -> str | None:
        return self.vault.get(self.vendor)

    def can_live(self) -> bool:
        return bool(self.api_key()) and _live_enabled()

    async def generate(
        self,
        prompt: str,
        *,
        provider_id: str,
        timeout_sec: float = 30.0,
        meta: dict[str, Any] | None = None,
    ) -> ProviderResult:
        started = time.time()
        meta = meta or {}
        if self.can_live():
            try:
                result = await self._live(prompt, timeout_sec=timeout_sec, meta=meta)
                result.latency_ms = round((time.time() - started) * 1000, 2)
                result.mode = "live"
                result.provider_id = provider_id
                return result
            except Exception as exc:  # noqa: BLE001
                logger.warning("provider_live_failed vendor=%s err=%s", self.vendor, exc)
                # fall through to sandbox
        sandbox = self._sandbox(prompt, provider_id=provider_id, meta=meta)
        sandbox.latency_ms = round((time.time() - started) * 1000, 2)
        return sandbox

    async def _live(self, prompt: str, *, timeout_sec: float, meta: dict[str, Any]) -> ProviderResult:
        raise NotImplementedError

    def _sandbox(self, prompt: str, *, provider_id: str, meta: dict[str, Any]) -> ProviderResult:
        digest = hashlib.md5(prompt.encode()).hexdigest()[:10]
        cost = GenerationCost(total=0.0)
        if self.modality == "image":
            cost = GenerationCost(image_cost=0.04, total=0.04)
            content = f"[sandbox-image:{provider_id}] {prompt[:120]}"
            url = f"sandbox://image/{provider_id}/{digest}"
        elif self.modality == "video":
            cost = GenerationCost(video_cost=0.25, total=0.25)
            content = f"[sandbox-video:{provider_id}] {prompt[:100]}"
            url = f"sandbox://video/{provider_id}/{digest}"
        elif self.modality == "voice":
            cost = GenerationCost(voice_cost=0.03, total=0.03)
            content = f"[sandbox-voice:{provider_id}] {prompt[:100]}"
            url = f"sandbox://voice/{provider_id}/{digest}"
        elif self.modality == "music":
            cost = GenerationCost(music_cost=0.05, total=0.05)
            content = f"[sandbox-music:{provider_id}] {prompt[:80]}"
            url = f"sandbox://music/{provider_id}/{digest}"
        else:
            tokens_out = max(20, len(prompt.split()) * 2)
            cost = GenerationCost(model_cost=0.002, tokens_in=len(prompt.split()), tokens_out=tokens_out, total=0.002)
            content = (
                f"[sandbox-text:{provider_id}]\n{prompt.strip()}\n\n"
                "— Результат подготовлен через Provider Manager (режим песочницы). "
                "Укажите API-ключ и ADOS_AI_LIVE=1 для live-режима."
            )
            url = None
        return ProviderResult(
            provider_id=provider_id,
            modality=self.modality,
            content=content,
            media_url=url,
            mode="sandbox",
            cost=cost,
            raw={"meta": meta},
        )

    async def health_check(self, *, timeout_sec: float = 5.0) -> dict[str, Any]:
        started = time.time()
        key = self.api_key()
        if not key:
            return {
                "ok": False,
                "status": "error",
                "message": "Ключ не настроен",
                "latency_ms": round((time.time() - started) * 1000, 2),
                "balance": None,
            }
        if not _live_enabled():
            return {
                "ok": True,
                "status": "active",
                "message": "Ключ есть · live выключен (песочница)",
                "latency_ms": round((time.time() - started) * 1000, 2),
                "balance": "n/a",
            }
        # ping optional endpoint
        try:
            await self._ping(timeout_sec=timeout_sec)
            return {
                "ok": True,
                "status": "active",
                "message": "API работает",
                "latency_ms": round((time.time() - started) * 1000, 2),
                "balance": "ok",
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "status": "error",
                "message": str(exc)[:200],
                "latency_ms": round((time.time() - started) * 1000, 2),
                "balance": None,
            }

    async def _ping(self, *, timeout_sec: float) -> None:
        if not self.default_endpoint:
            return
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        headers = {"Authorization": f"Bearer {self.api_key()}"}
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(self.default_endpoint, headers=headers) as resp:
                if resp.status >= 500:
                    raise RuntimeError(f"HTTP {resp.status}")


class OpenAITextAdapter(BaseProviderAdapter):
    vendor = "openai"
    modality = "text"
    default_endpoint = "https://api.openai.com/v1/models"

    async def _live(self, prompt: str, *, timeout_sec: float, meta: dict[str, Any]) -> ProviderResult:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        headers = {
            "Authorization": f"Bearer {self.api_key()}",
            "Content-Type": "application/json",
        }
        model = meta.get("model") or "gpt-4o-mini"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Ты AI ADOS Enterprise. Отвечай на русском."},
                {"role": "user", "content": prompt},
            ],
        }
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            ) as resp:
                data = await resp.json()
                if resp.status >= 400:
                    raise RuntimeError(data.get("error", data))
                text = data["choices"][0]["message"]["content"]
                usage = data.get("usage") or {}
                cost = GenerationCost(
                    tokens_in=int(usage.get("prompt_tokens") or 0),
                    tokens_out=int(usage.get("completion_tokens") or 0),
                    model_cost=0.002,
                    total=0.002,
                )
                return ProviderResult(
                    provider_id="openai_text",
                    modality="text",
                    content=text,
                    mode="live",
                    cost=cost,
                    raw={"model": model},
                )


class OpenAIImageAdapter(BaseProviderAdapter):
    vendor = "openai"
    modality = "image"
    default_endpoint = "https://api.openai.com/v1/models"

    async def _live(self, prompt: str, *, timeout_sec: float, meta: dict[str, Any]) -> ProviderResult:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        headers = {
            "Authorization": f"Bearer {self.api_key()}",
            "Content-Type": "application/json",
        }
        size = meta.get("size") or "1024x1024"
        size = size.replace("×", "x")
        payload = {"model": meta.get("model") or "dall-e-3", "prompt": prompt, "n": 1, "size": size}
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json=payload,
            ) as resp:
                data = await resp.json()
                if resp.status >= 400:
                    raise RuntimeError(data.get("error", data))
                url = data["data"][0].get("url") or data["data"][0].get("b64_json")
                return ProviderResult(
                    provider_id="openai_image",
                    modality="image",
                    content=f"Изображение сгенерировано (OpenAI Images).",
                    media_url=url,
                    mode="live",
                    cost=GenerationCost(image_cost=0.04, total=0.04),
                    raw={"model": payload["model"]},
                )


class GenericHttpAdapter(BaseProviderAdapter):
    """Generic REST adapter for Flux/Runway/etc. — live POST when key + endpoint set."""

    def __init__(
        self,
        *,
        vendor: str,
        modality: str,
        endpoint: str,
        vault: ProviderKeyVault | None = None,
    ) -> None:
        super().__init__(vault=vault)
        self.vendor = vendor
        self.modality = modality
        self.default_endpoint = endpoint

    async def _live(self, prompt: str, *, timeout_sec: float, meta: dict[str, Any]) -> ProviderResult:
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        headers = {
            "Authorization": f"Bearer {self.api_key()}",
            "Content-Type": "application/json",
        }
        payload = {"prompt": prompt, **{k: v for k, v in (meta or {}).items() if k != "model"}}
        if meta.get("model"):
            payload["model"] = meta["model"]
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(self.default_endpoint, headers=headers, json=payload) as resp:
                data = await resp.json(content_type=None)
                if resp.status >= 400:
                    raise RuntimeError(str(data)[:300])
                url = None
                if isinstance(data, dict):
                    url = data.get("url") or data.get("media_url") or (data.get("output") or [None])[0]
                content = data.get("content") if isinstance(data, dict) else str(data)[:500]
                cost = GenerationCost(total=0.1)
                if self.modality == "image":
                    cost = GenerationCost(image_cost=0.05, total=0.05)
                elif self.modality == "video":
                    cost = GenerationCost(video_cost=0.3, total=0.3)
                elif self.modality == "voice":
                    cost = GenerationCost(voice_cost=0.04, total=0.04)
                return ProviderResult(
                    provider_id=f"{self.vendor}_{self.modality}",
                    modality=self.modality,
                    content=str(content or f"Готово ({self.vendor})"),
                    media_url=url if isinstance(url, str) else None,
                    mode="live",
                    cost=cost,
                    raw={"response_keys": list(data.keys()) if isinstance(data, dict) else []},
                )


def build_default_adapters(vault: ProviderKeyVault | None = None) -> dict[str, BaseProviderAdapter]:
    v = vault or provider_key_vault
    adapters: dict[str, BaseProviderAdapter] = {
        "openai_text": OpenAITextAdapter(vault=v),
        "openai_image": OpenAIImageAdapter(vault=v),
        "openai_voice": GenericHttpAdapter(
            vendor="openai",
            modality="voice",
            endpoint="https://api.openai.com/v1/audio/speech",
            vault=v,
        ),
        "anthropic_text": GenericHttpAdapter(
            vendor="anthropic",
            modality="text",
            endpoint="https://api.anthropic.com/v1/messages",
            vault=v,
        ),
        "gemini_text": GenericHttpAdapter(
            vendor="gemini",
            modality="text",
            endpoint="https://generativelanguage.googleapis.com/v1beta/models",
            vault=v,
        ),
        "deepseek_text": GenericHttpAdapter(
            vendor="deepseek",
            modality="text",
            endpoint="https://api.deepseek.com/chat/completions",
            vault=v,
        ),
        "mistral_text": GenericHttpAdapter(
            vendor="mistral",
            modality="text",
            endpoint="https://api.mistral.ai/v1/chat/completions",
            vault=v,
        ),
        "flux_image": GenericHttpAdapter(
            vendor="flux", modality="image", endpoint="https://api.bfl.ai/v1/flux", vault=v
        ),
        "recraft_image": GenericHttpAdapter(
            vendor="recraft", modality="image", endpoint="https://external.api.recraft.ai/v1/images/generations", vault=v
        ),
        "ideogram_image": GenericHttpAdapter(
            vendor="ideogram", modality="image", endpoint="https://api.ideogram.ai/generate", vault=v
        ),
        "bfl_image": GenericHttpAdapter(
            vendor="bfl", modality="image", endpoint="https://api.bfl.ai/v1/flux", vault=v
        ),
        "stability_image": GenericHttpAdapter(
            vendor="stability",
            modality="image",
            endpoint="https://api.stability.ai/v2beta/stable-image/generate/core",
            vault=v,
        ),
        "fal_image": GenericHttpAdapter(
            vendor="fal", modality="image", endpoint="https://fal.run/fal-ai/flux/dev", vault=v
        ),
        "replicate_image": GenericHttpAdapter(
            vendor="replicate", modality="image", endpoint="https://api.replicate.com/v1/predictions", vault=v
        ),
        "runway_video": GenericHttpAdapter(
            vendor="runway", modality="video", endpoint="https://api.dev.runwayml.com/v1/image_to_video", vault=v
        ),
        "google_veo": GenericHttpAdapter(
            vendor="google", modality="video", endpoint="https://generativelanguage.googleapis.com/v1beta/veo", vault=v
        ),
        "pika_video": GenericHttpAdapter(
            vendor="pika", modality="video", endpoint="https://api.pika.art/v1/generate", vault=v
        ),
        "kling_video": GenericHttpAdapter(
            vendor="kling", modality="video", endpoint="https://api.kling.ai/v1/videos/generations", vault=v
        ),
        "luma_video": GenericHttpAdapter(
            vendor="luma", modality="video", endpoint="https://api.lumalabs.ai/dream-machine/v1/generations", vault=v
        ),
        "hailuo_video": GenericHttpAdapter(
            vendor="hailuo", modality="video", endpoint="https://api.minimaxi.chat/v1/video_generation", vault=v
        ),
        "elevenlabs_voice": GenericHttpAdapter(
            vendor="elevenlabs",
            modality="voice",
            endpoint="https://api.elevenlabs.io/v1/text-to-speech",
            vault=v,
        ),
        "cartesia_voice": GenericHttpAdapter(
            vendor="cartesia", modality="voice", endpoint="https://api.cartesia.ai/tts/bytes", vault=v
        ),
        "google_tts": GenericHttpAdapter(
            vendor="google", modality="voice", endpoint="https://texttospeech.googleapis.com/v1/text:synthesize", vault=v
        ),
        "azure_speech": GenericHttpAdapter(
            vendor="azure",
            modality="voice",
            endpoint="https://eastus.tts.speech.microsoft.com/cognitiveservices/v1",
            vault=v,
        ),
        "local_music": BaseProviderAdapter(vault=v),
    }
    adapters["local_music"].vendor = "local"
    adapters["local_music"].modality = "music"
    # local fallbacks
    for mod in ("image", "video", "voice", "text"):
        local = BaseProviderAdapter(vault=v)
        local.vendor = "local"
        local.modality = mod
        adapters[f"local_{mod}"] = local
    return adapters
