"""Visual Story Engine & Enterprise Storytelling — Sprint 29.9.

Transforms real platform events into coherent visual narratives.
Never creates, modifies, or reorders business events.
Only groups and presents verified events from the Visual Event Bus.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store
from applications.platform_builder.story.catalogs import (
    AI_STORY_BEATS,
    EXECUTIVE_SUMMARIES,
    KNOWLEDGE_STORY_BEATS,
    NAVIGATION_CONTROLS,
    ORG_EVOLUTION,
    SEGMENT_KEYWORDS,
    STORY_CHANNEL_MAP,
    STORY_ENGINE_COMPONENTS,
    STORY_SEGMENTS,
    STORY_TYPES,
    UI_SURFACES,
    WORKFLOW_STORY_BEATS,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.team_map.engine import VisualEventBus


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _segment_for_event(event_type: str) -> str:
    et = (event_type or "").lower()
    for segment, keywords in SEGMENT_KEYWORDS.items():
        if any(k in et for k in keywords):
            return segment
    return "Execution"


class StoryTimeline:
    """Play / pause / step / navigate — does not mutate source events."""

    def __init__(self) -> None:
        self.playing = False
        self.paused = True
        self.cursor = 0
        self.frames: list[dict[str, Any]] = []
        self.bookmarks: list[dict[str, Any]] = []
        self.milestones: list[dict[str, Any]] = []

    def load_frames(self, frames: list[dict[str, Any]]) -> None:
        # Preserve chronological order of verified events (no reorder)
        self.frames = list(frames)
        self.cursor = 0

    def status(self) -> dict[str, Any]:
        current = self.frames[self.cursor] if self.frames and self.cursor < len(self.frames) else None
        return {
            "playing": self.playing,
            "paused": self.paused,
            "cursor": self.cursor,
            "frame_count": len(self.frames),
            "current_frame": current,
            "bookmarks": list(self.bookmarks),
            "milestones": list(self.milestones),
            "controls": list(NAVIGATION_CONTROLS),
            "reorders_business_events": False,
            "ready": True,
            "operational": True,
        }

    def play(self) -> dict[str, Any]:
        self.playing = True
        self.paused = False
        return {**self.status(), "action": "Play"}

    def pause(self) -> dict[str, Any]:
        self.playing = False
        self.paused = True
        return {**self.status(), "action": "Pause"}

    def step(self) -> dict[str, Any]:
        if self.cursor < len(self.frames) - 1:
            self.cursor += 1
        elif self.frames and self.cursor < len(self.frames):
            self.cursor = min(self.cursor + 1, len(self.frames) - 1)
        return {**self.status(), "action": "Step"}

    def navigate(self, index: int) -> dict[str, Any]:
        if not self.frames:
            self.cursor = 0
        else:
            self.cursor = max(0, min(int(index), len(self.frames) - 1))
        return {**self.status(), "action": "Timeline Navigation"}

    def add_bookmark(self, label: str | None = None) -> dict[str, Any]:
        bm = {
            "bookmark_id": _id("sbm"),
            "index": self.cursor,
            "label": label or f"Bookmark {self.cursor}",
            "created_at": _now(),
        }
        self.bookmarks.append(bm)
        return {**self.status(), "action": "Bookmarks", "bookmark": bm}

    def register_milestone(self, label: str, index: int | None = None) -> dict[str, Any]:
        idx = self.cursor if index is None else int(index)
        ms = {
            "milestone_id": _id("sms"),
            "index": idx,
            "label": label,
            "created_at": _now(),
        }
        self.milestones.append(ms)
        return {**self.status(), "action": "Milestones", "milestone": ms}


class StoryController:
    def __init__(self, timeline: StoryTimeline) -> None:
        self.timeline = timeline
        self.active_story_id: str | None = None

    def attach(self, story_id: str, frames: list[dict[str, Any]]) -> dict[str, Any]:
        self.active_story_id = story_id
        self.timeline.load_frames(frames)
        return {
            "active_story_id": story_id,
            "timeline": self.timeline.status(),
            "ready": True,
        }


class StoryBuilder:
    """Groups verified bus events into story frames — never mutates or reorders source events."""

    def build(
        self,
        story_type: str,
        events: list[dict[str, Any]],
        *,
        title: str | None = None,
    ) -> dict[str, Any]:
        if story_type not in STORY_TYPES:
            raise ValidationError(f"Unsupported story type: {story_type}")
        channels = set(STORY_CHANNEL_MAP.get(story_type, ()))
        # Filter then sort ascending by published_at to preserve chronological event order
        filtered = [e for e in events if e.get("channel") in channels]
        ordered = sorted(filtered, key=lambda e: e.get("published_at") or "")
        frames = []
        for e in ordered:
            frames.append(
                {
                    "frame_id": _id("sframe"),
                    "event_id": e["event_id"],
                    "channel": e.get("channel"),
                    "event_type": e.get("event_type"),
                    "published_at": e.get("published_at"),
                    "payload": e.get("payload") or {},
                    "segment": _segment_for_event(e.get("event_type") or ""),
                    "verified_bus_event": True,
                    "modified": False,
                }
            )
        segments: dict[str, list[dict[str, Any]]] = {s: [] for s in STORY_SEGMENTS}
        for f in frames:
            segments.setdefault(f["segment"], []).append(f)
        return {
            "story_id": _id("story"),
            "story_type": story_type,
            "title": title or story_type,
            "frames": frames,
            "frame_count": len(frames),
            "segments": segments,
            "segment_counts": {k: len(v) for k, v in segments.items()},
            "source_event_ids": [f["event_id"] for f in frames],
            "creates_business_events": False,
            "modifies_business_events": False,
            "reorders_business_events": False,
            "groups_verified_bus_events_only": True,
            "built_at": _now(),
        }


class StoryRegistry:
    def __init__(self, store: PlatformBuilderStore) -> None:
        self.store = store

    def save(self, story: dict[str, Any]) -> dict[str, Any]:
        sid = story["story_id"]
        self.store.story_definitions.save(sid, story)
        return story

    def list_stories(self) -> dict[str, Any]:
        stories = self.store.story_definitions.list_all()
        return {
            "stories": stories,
            "count": len(stories),
            "types": list(STORY_TYPES),
            "ready": True,
            "operational": True,
        }

    def get(self, story_id: str) -> dict[str, Any]:
        story = self.store.story_definitions.get(story_id)
        if not story:
            raise NotFoundError(f"Story not found: {story_id}")
        return story


class VisualStoryEngine:
    """Enterprise Visual Story Engine — verified bus events only."""

    def __init__(
        self,
        store: PlatformBuilderStore | None = None,
        bus: VisualEventBus | None = None,
    ) -> None:
        self.store = store or platform_builder_store
        self.bus = bus or VisualEventBus(self.store)
        self.builder = StoryBuilder()
        self.registry = StoryRegistry(self.store)
        self.timeline = StoryTimeline()
        self.controller = StoryController(self.timeline)

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.9",
            "story_engine_ready": True,
            "story_timeline_ready": True,
            "executive_story_ready": True,
            "milestone_viewer_ready": True,
            "creates_business_events": False,
            "modifies_business_events": False,
            "reorders_business_events": False,
            "groups_verified_bus_events_only": True,
            **full_catalog(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.9",
            "creates_business_events": False,
            "modifies_business_events": False,
            "reorders_business_events": False,
            "groups_verified_bus_events_only": True,
            "components": list(STORY_ENGINE_COMPONENTS),
            "stories": len(self.store.story_definitions.list_all()),
            "engines": len(self.store.story_engines.list_all()),
            "timeline": self.timeline.status(),
            "active_story_id": self.controller.active_story_id,
        }

    def _bus_events(self, limit: int = 200) -> list[dict[str, Any]]:
        polled = self.bus.poll(limit=limit)
        # Poll returns newest-first; builder will sort ascending — we do not mutate bus store
        return list(polled.get("events") or [])

    # Step 1
    def engine_overview(self) -> dict[str, Any]:
        return {
            "title": "Story Engine",
            "components": list(STORY_ENGINE_COMPONENTS),
            "registry": self.registry.list_stories(),
            "timeline": self.timeline.status(),
            "creates_business_events": False,
            "modifies_business_events": False,
            "reorders_business_events": False,
            "groups_verified_bus_events_only": True,
            "ready": True,
        }

    # Step 2
    def story_types(self) -> dict[str, Any]:
        return {
            "types": list(STORY_TYPES),
            "channel_map": {k: list(v) for k, v in STORY_CHANNEL_MAP.items()},
            "count": len(STORY_TYPES),
            "ready": True,
        }

    # Step 3
    def story_segments(self) -> dict[str, Any]:
        return {
            "segments": list(STORY_SEGMENTS),
            "keywords": {k: list(v) for k, v in SEGMENT_KEYWORDS.items()},
            "ready": True,
        }

    def build_story(self, story_type: str, *, title: str | None = None, persist: bool = True) -> dict[str, Any]:
        events = self._bus_events()
        story = self.builder.build(story_type, events, title=title)
        if persist:
            self.registry.save(story)
        self.controller.attach(story["story_id"], story["frames"])
        # Auto milestones at Completion / Archive frames (presentation markers only)
        for i, frame in enumerate(story["frames"]):
            if frame["segment"] in {"Completion", "Archive", "Beginning"}:
                self.timeline.register_milestone(f"{frame['segment']}: {frame['event_type']}", i)
        return story

    # Step 4
    def organization_evolution(self) -> dict[str, Any]:
        story = self.build_story("Organization Story", title="Organization Evolution")
        return {
            "beats": list(ORG_EVOLUTION),
            "story": story,
            "visualize": {b: True for b in ORG_EVOLUTION},
            "ready": True,
        }

    # Step 5
    def ai_stories(self) -> dict[str, Any]:
        story = self.build_story("AI Agent Story", title="AI Agent Story")
        return {
            "beats": list(AI_STORY_BEATS),
            "story": story,
            "visualize": {b: True for b in AI_STORY_BEATS},
            "ready": True,
        }

    # Step 6
    def workflow_stories(self) -> dict[str, Any]:
        story = self.build_story("Workflow Story", title="Workflow Story")
        return {
            "beats": list(WORKFLOW_STORY_BEATS),
            "story": story,
            "display": {b: True for b in WORKFLOW_STORY_BEATS},
            "ready": True,
        }

    # Step 7
    def knowledge_stories(self) -> dict[str, Any]:
        story = self.build_story("Knowledge Story", title="Knowledge Story")
        return {
            "beats": list(KNOWLEDGE_STORY_BEATS),
            "story": story,
            "animate": {b: True for b in KNOWLEDGE_STORY_BEATS},
            "ready": True,
        }

    # Step 8 — Executive Mode (summaries from verified events only)
    def executive_mode(self) -> dict[str, Any]:
        story = self.build_story("Executive Story", title="Executive Story")
        events = story["frames"]
        by_channel: dict[str, int] = {}
        for f in events:
            ch = f.get("channel") or "unknown"
            by_channel[ch] = by_channel.get(ch, 0) + 1
        milestones = [
            {
                "label": f["event_type"],
                "event_id": f["event_id"],
                "published_at": f["published_at"],
                "segment": f["segment"],
            }
            for f in events
            if f["segment"] in {"Completion", "Beginning", "Decision"}
        ]
        summaries = {
            "Today's Progress": {
                "event_count": len(events),
                "channels": by_channel,
                "source": "Visual Event Bus",
            },
            "Weekly Activity": {
                "event_count": len(events),
                "top_channels": sorted(by_channel.items(), key=lambda x: -x[1])[:5],
            },
            "Project Evolution": {
                "workflow_frames": by_channel.get("Workflow Events", 0),
                "task_frames": by_channel.get("Task Events", 0),
            },
            "Organization Development": {
                "organization_frames": by_channel.get("Organization Events", 0),
            },
            "Major Milestones": milestones[:10],
        }
        return {
            "summaries": summaries,
            "summary_names": list(EXECUTIVE_SUMMARIES),
            "story": story,
            "milestone_viewer": {
                "milestones": milestones,
                "count": len(milestones),
                "ready": True,
            },
            "creates_business_events": False,
            "modifies_business_events": False,
            "reorders_business_events": False,
            "ready": True,
        }

    # Step 9
    def navigate(self, action: str, *, index: int | None = None, label: str | None = None) -> dict[str, Any]:
        a = action.strip().lower().replace(" ", "_")
        if a == "play":
            return self.timeline.play()
        if a == "pause":
            return self.timeline.pause()
        if a == "step":
            return self.timeline.step()
        if a in {"timeline_navigation", "navigate", "goto"}:
            if index is None:
                raise ValidationError("index is required for Timeline Navigation")
            return self.timeline.navigate(index)
        if a == "bookmarks":
            return self.timeline.add_bookmark(label)
        if a == "milestones":
            return self.timeline.register_milestone(label or "Milestone", index)
        raise ValidationError(f"Unknown navigation action: {action}")

    def milestone_viewer(self) -> dict[str, Any]:
        return {
            "milestones": list(self.timeline.milestones),
            "count": len(self.timeline.milestones),
            "ready": True,
            "operational": True,
        }

    def story_history(self) -> dict[str, Any]:
        return {
            **self.registry.list_stories(),
            "history": True,
        }

    def ui_dashboard(self) -> dict[str, Any]:
        executive = self.executive_mode()
        return {
            "surfaces": list(UI_SURFACES),
            "story_timeline": self.timeline.status(),
            "story_player": {
                "active_story_id": self.controller.active_story_id,
                "playing": self.timeline.playing,
                "paused": self.timeline.paused,
            },
            "milestone_viewer": executive["milestone_viewer"],
            "executive_summary": {
                name: executive["summaries"][name] for name in EXECUTIVE_SUMMARIES
            },
            "story_history": self.story_history(),
            "creates_business_events": False,
            "ready": True,
        }

    # Wizard
    def start_session(self) -> dict[str, Any]:
        sid = _id("stry")
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "draft": {"story_type": "Executive Story"},
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.story_wizard_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.story_wizard_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Story session not found: {session_id}")
        return session

    def update_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 10:
                raise ValidationError("step must be between 1 and 10")
            session["step"] = step
        if "draft" in patch and isinstance(patch["draft"], dict):
            session["draft"] = {**session["draft"], **patch["draft"]}
        session["updated_at"] = _now()
        self.store.story_wizard_sessions.save(session_id, session)
        return session

    def summary(self, session_id: str) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "title": "Visual Story Engine Summary",
            "engine": self.engine_overview(),
            "types": self.story_types(),
            "segments": self.story_segments(),
            "organization": self.organization_evolution(),
            "ai": self.ai_stories(),
            "workflow": self.workflow_stories(),
            "knowledge": self.knowledge_stories(),
            "executive": self.executive_mode(),
            "timeline": self.timeline.status(),
            "ui": self.ui_dashboard(),
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        story_type = session["draft"].get("story_type") or "Executive Story"
        story = self.build_story(story_type)

        eng_id = _id("steng")
        reg_id = _id("streg")
        bld_id = _id("stbld")
        tl_id = _id("sttl")
        api_id = _id("stapi")

        story_engine = {
            "story_engine_id": eng_id,
            "internal_id": eng_id,
            "catalog": self.catalog(),
            "creates_business_events": False,
            "modifies_business_events": False,
            "reorders_business_events": False,
            "groups_verified_bus_events_only": True,
            "registered_at": _now(),
            "sprint": "29.9",
        }
        story_registry = {
            "story_registry_id": reg_id,
            "internal_id": reg_id,
            "registry": self.registry.list_stories(),
            "registered_at": _now(),
            "sprint": "29.9",
        }
        story_builder = {
            "story_builder_id": bld_id,
            "internal_id": bld_id,
            "types": list(STORY_TYPES),
            "registered_at": _now(),
            "sprint": "29.9",
        }
        story_timeline = {
            "story_timeline_id": tl_id,
            "internal_id": tl_id,
            "status": self.timeline.status(),
            "registered_at": _now(),
            "sprint": "29.9",
        }
        executive_story_api = {
            "executive_story_api_id": api_id,
            "internal_id": api_id,
            "endpoints": [
                "/story/executive",
                "/story/build",
                "/story/navigate",
                "/story/milestones",
                "/story/ui",
            ],
            "creates_business_events": False,
            "registered_at": _now(),
            "sprint": "29.9",
        }

        self.store.story_engines.save(eng_id, story_engine)
        self.store.story_registries.save(reg_id, story_registry)
        self.store.story_builders.save(bld_id, story_builder)
        self.store.story_timelines.save(tl_id, story_timeline)
        self.store.executive_story_apis.save(api_id, executive_story_api)

        self.bus.publish(
            "Registry Events",
            "story_engine_registered",
            {"story_engine_id": eng_id, "presentation_only": True},
        )

        session["status"] = "created"
        session["registrations"] = {
            "story_engine_id": eng_id,
            "story_registry_id": reg_id,
            "story_builder_id": bld_id,
            "story_timeline_id": tl_id,
            "executive_story_api_id": api_id,
            "story_id": story["story_id"],
        }
        session["updated_at"] = _now()
        self.store.story_wizard_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "story_engine": story_engine,
            "story_registry": story_registry,
            "story_builder": story_builder,
            "story_timeline": story_timeline,
            "executive_story_api": executive_story_api,
            "story": story,
            "message": "Story Engine, Registry, Builder, Timeline, and Executive Story API registered.",
        }
