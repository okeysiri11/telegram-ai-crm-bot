"""Speech providers + automatic fallback — Sprint 36.6."""

from __future__ import annotations

import hashlib
from typing import Any, Protocol

from platform_ai.voice_models import SpeechProviderId, TranscriptChunk


class SpeechProvider(Protocol):
    provider_id: str

    async def health(self) -> dict[str, Any]: ...

    async def transcribe(self, audio: bytes | str, *, streaming: bool = False) -> TranscriptChunk: ...


def _deterministic_text(audio: bytes | str, *, prefix: str) -> str:
    raw = audio if isinstance(audio, bytes) else str(audio).encode("utf-8")
    if not raw:
        return ""
    # If caller already passed text (tests / push-to-talk text path), echo it.
    if isinstance(audio, str) and audio.strip() and not audio.startswith("data:"):
        return audio.strip()
    digest = hashlib.sha1(raw).hexdigest()[:8]
    return f"{prefix} command {digest}"


class BaseMockSpeechProvider:
    provider_id: str = "base"
    label: str = "Base"
    available: bool = True

    async def health(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "label": self.label,
            "available": self.available,
            "streaming": True,
            "vad": True,
        }

    async def transcribe(self, audio: bytes | str, *, streaming: bool = False) -> TranscriptChunk:
        if not self.available:
            raise RuntimeError(f"provider unavailable: {self.provider_id}")
        text = _deterministic_text(audio, prefix=self.label)
        return TranscriptChunk(
            text=text,
            is_final=not streaming or True,
            provider_id=self.provider_id,
            confidence=0.91 if streaming else 0.94,
            vad_active=bool(audio),
        )


class OpenAIRealtimeProvider(BaseMockSpeechProvider):
    provider_id = SpeechProviderId.OPENAI_REALTIME.value
    label = "OpenAI Realtime"


class WhisperProvider(BaseMockSpeechProvider):
    provider_id = SpeechProviderId.WHISPER.value
    label = "Whisper"


class AzureSpeechProvider(BaseMockSpeechProvider):
    provider_id = SpeechProviderId.AZURE_SPEECH.value
    label = "Azure Speech"


class DeepgramProvider(BaseMockSpeechProvider):
    provider_id = SpeechProviderId.DEEPGRAM.value
    label = "Deepgram"


class GoogleSpeechProvider(BaseMockSpeechProvider):
    provider_id = SpeechProviderId.GOOGLE_SPEECH.value
    label = "Google Speech"


class LocalWhisperProvider(BaseMockSpeechProvider):
    provider_id = SpeechProviderId.LOCAL_WHISPER.value
    label = "Local Whisper"


DEFAULT_FALLBACK_CHAIN = [
    SpeechProviderId.OPENAI_REALTIME.value,
    SpeechProviderId.WHISPER.value,
    SpeechProviderId.DEEPGRAM.value,
    SpeechProviderId.AZURE_SPEECH.value,
    SpeechProviderId.GOOGLE_SPEECH.value,
    SpeechProviderId.LOCAL_WHISPER.value,
]


class SpeechProviderManager:
    def __init__(self) -> None:
        self._providers: dict[str, BaseMockSpeechProvider] = {
            p.provider_id: p
            for p in (
                OpenAIRealtimeProvider(),
                WhisperProvider(),
                AzureSpeechProvider(),
                DeepgramProvider(),
                GoogleSpeechProvider(),
                LocalWhisperProvider(),
            )
        }
        self.fallback_chain = list(DEFAULT_FALLBACK_CHAIN)
        self.default_provider = SpeechProviderId.WHISPER.value

    def reset(self) -> None:
        for p in self._providers.values():
            p.available = True
        self.fallback_chain = list(DEFAULT_FALLBACK_CHAIN)
        self.default_provider = SpeechProviderId.WHISPER.value

    def get(self, provider_id: str) -> BaseMockSpeechProvider:
        p = self._providers.get(provider_id)
        if p is None:
            raise KeyError(f"unknown speech provider: {provider_id}")
        return p

    def set_available(self, provider_id: str, available: bool) -> None:
        self.get(provider_id).available = available

    async def health_all(self) -> list[dict[str, Any]]:
        return [await p.health() for p in self._providers.values()]

    async def transcribe(
        self,
        audio: bytes | str,
        *,
        preferred: str | None = None,
        streaming: bool = False,
    ) -> TranscriptChunk:
        order: list[str] = []
        if preferred:
            order.append(preferred)
        for pid in self.fallback_chain:
            if pid not in order:
                order.append(pid)
        errors: list[str] = []
        for pid in order:
            provider = self._providers.get(pid)
            if provider is None:
                continue
            try:
                chunk = await provider.transcribe(audio, streaming=streaming)
                chunk.provider_id = pid
                return chunk
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{pid}: {exc}")
        raise RuntimeError("all speech providers failed: " + "; ".join(errors))


speech_provider_manager = SpeechProviderManager()
