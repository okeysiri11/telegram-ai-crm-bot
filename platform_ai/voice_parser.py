"""Voice command parser — natural language intent detection (Sprint 36.6)."""

from __future__ import annotations

import re
from typing import Callable

from platform_ai.voice_models import CommandRisk, ParsedCommand, VoiceIntent

EntityFn = Callable[[re.Match[str]], dict[str, str]]

# Intent → default UI route / risk
INTENT_META: dict[VoiceIntent, dict] = {
    VoiceIntent.OPEN_PAGE: {"risk": CommandRisk.SAFE, "route": None},
    VoiceIntent.CREATE_PROJECT: {"risk": CommandRisk.CONFIRM, "route": "/projects"},
    VoiceIntent.CREATE_TASK: {"risk": CommandRisk.CONFIRM, "route": "/tasks"},
    VoiceIntent.ASSIGN_EMPLOYEE: {"risk": CommandRisk.DANGEROUS, "route": "/hr"},
    VoiceIntent.SEARCH_KNOWLEDGE: {"risk": CommandRisk.SAFE, "route": "/knowledge"},
    VoiceIntent.OPEN_CRM: {"risk": CommandRisk.SAFE, "route": "/crm"},
    VoiceIntent.OPEN_ERP: {"risk": CommandRisk.SAFE, "route": "/erp"},
    VoiceIntent.LAUNCH_WORKFLOW: {"risk": CommandRisk.CONFIRM, "route": "/platform-builder/workflows"},
    VoiceIntent.CALL_AI_AGENT: {"risk": CommandRisk.CONFIRM, "route": "/platform-builder/ai-runtime"},
    VoiceIntent.GENERATE_REPORT: {"risk": CommandRisk.CONFIRM, "route": "/analytics"},
    VoiceIntent.UNKNOWN: {"risk": CommandRisk.SAFE, "route": None},
}

PATTERNS: list[tuple[VoiceIntent, re.Pattern[str], float, EntityFn | None]] = [
    (
        VoiceIntent.CREATE_PROJECT,
        re.compile(r"(?:create|new|start)\s+(?:a\s+)?project(?:\s+(?:called|named)\s+(.+))?", re.I),
        0.92,
        lambda m: {"name": m.group(1).strip()} if m.group(1) else {},
    ),
    (
        VoiceIntent.CREATE_TASK,
        re.compile(r"(?:create|add|new)\s+(?:a\s+)?task(?:\s+(?:to|for|:)\s+(.+))?", re.I),
        0.9,
        lambda m: {"task": m.group(1).strip()} if m.group(1) else {},
    ),
    (
        VoiceIntent.ASSIGN_EMPLOYEE,
        re.compile(
            r"(?:assign|allocate)\s+(?:employee\s+)?([\w.\s-]+?)(?:\s+to\s+(.+))?$",
            re.I,
        ),
        0.9,
        lambda m: {
            **({"employee": m.group(1).strip()} if m.group(1) else {}),
            **({"target": m.group(2).strip()} if m.group(2) else {}),
        },
    ),
    (
        VoiceIntent.OPEN_CRM,
        re.compile(r"open\s+(?:the\s+)?crm", re.I),
        0.95,
        None,
    ),
    (
        VoiceIntent.OPEN_ERP,
        re.compile(r"open\s+(?:the\s+)?erp", re.I),
        0.95,
        None,
    ),
    (
        VoiceIntent.SEARCH_KNOWLEDGE,
        re.compile(r"(?:search|find|look\s+up)\s+(?:(?:in\s+)?knowledge\s+)?(?:for\s+)?(.+)", re.I),
        0.88,
        lambda m: {"query": m.group(1).strip()} if m.group(1) else {},
    ),
    (
        VoiceIntent.LAUNCH_WORKFLOW,
        re.compile(r"(?:launch|run|start|execute)\s+(?:the\s+)?workflow(?:\s+(.+))?", re.I),
        0.9,
        lambda m: {"workflow": m.group(1).strip()} if m.group(1) else {},
    ),
    (
        VoiceIntent.CALL_AI_AGENT,
        re.compile(r"(?:call|ask|run|invoke)\s+(?:the\s+)?(?:ai\s+)?agent(?:\s+([\w.\s-]+))?(?:\s+to\s+(.+))?", re.I),
        0.87,
        lambda m: {
            **({"agent": m.group(1).strip()} if m.group(1) else {}),
            **({"task": m.group(2).strip()} if m.group(2) else {}),
        },
    ),
    (
        VoiceIntent.GENERATE_REPORT,
        re.compile(r"(?:generate|create|make)\s+(?:a\s+)?report(?:\s+(?:on|for|about)\s+(.+))?", re.I),
        0.89,
        lambda m: {"topic": m.group(1).strip()} if m.group(1) else {},
    ),
    (
        VoiceIntent.OPEN_PAGE,
        re.compile(r"open\s+(?:the\s+)?(?:page\s+)?([\w\s/-]+)", re.I),
        0.82,
        lambda m: {"page": m.group(1).strip()} if m.group(1) else {},
    ),
]


class VoiceCommandParser:
    def parse(self, transcript: str) -> ParsedCommand:
        text = (transcript or "").strip()
        if not text:
            return ParsedCommand(
                intent=VoiceIntent.UNKNOWN,
                confidence=0.0,
                transcript=text,
                risk=CommandRisk.SAFE,
            )
        for intent, pattern, confidence, entity_fn in PATTERNS:
            m = pattern.search(text)
            if not m:
                continue
            entities = entity_fn(m) if entity_fn else {}
            meta = INTENT_META[intent]
            risk = meta["risk"]
            route = meta["route"]
            if intent == VoiceIntent.OPEN_PAGE and entities.get("page"):
                page = entities["page"].lower().replace(" ", "-")
                route = f"/{page}" if not page.startswith("/") else page
            return ParsedCommand(
                intent=intent,
                confidence=confidence,
                transcript=text,
                entities=entities,
                risk=risk,
                route=route,
                requires_confirmation=risk in (CommandRisk.CONFIRM, CommandRisk.DANGEROUS),
            )
        return ParsedCommand(
            intent=VoiceIntent.UNKNOWN,
            confidence=0.2,
            transcript=text,
            risk=CommandRisk.SAFE,
        )


voice_command_parser = VoiceCommandParser()
