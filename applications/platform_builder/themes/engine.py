"""Visual Theme Engine & Enterprise UI Personalization — Sprint 29.5.

Controls complete visual identity. Themes never contain business logic.
Themes affect appearance only.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store
from applications.platform_builder.themes.catalogs import (
    ACCESSIBILITY_FEATURES,
    AI_CITY_THEME_FOUNDATION,
    AI_VISUAL_STYLES,
    ANIMATION_THEME_KEYS,
    BRANDING_FIELDS,
    BUILTIN_THEMES,
    COLOR_TOKENS,
    COMPONENT_TARGETS,
    DEFAULT_PALETTES,
    THEME_SCOPES,
    WIZARD_STEPS,
    full_catalog,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class ThemeRegistry:
    """Registry of theme definitions (appearance only)."""

    def __init__(self, store: PlatformBuilderStore) -> None:
        self.store = store
        self._ensure_builtins()

    def _ensure_builtins(self) -> None:
        for theme in BUILTIN_THEMES:
            tid = theme["theme_id"]
            if not self.store.theme_definitions.get(tid):
                mode = theme["mode"]
                record = {
                    **theme,
                    "colors": dict(DEFAULT_PALETTES[mode]),
                    "registered_at": _now(),
                    "contains_business_logic": False,
                    "affects_appearance_only": True,
                }
                self.store.theme_definitions.save(tid, record)

    def list_themes(self) -> dict[str, Any]:
        themes = self.store.theme_definitions.list_all()
        return {
            "themes": themes,
            "count": len(themes),
            "scopes": list(THEME_SCOPES),
            "ready": True,
            "operational": True,
        }

    def get(self, theme_id: str) -> dict[str, Any]:
        theme = self.store.theme_definitions.get(theme_id)
        if not theme:
            raise NotFoundError(f"Theme not found: {theme_id}")
        return theme

    def register(self, theme: dict[str, Any]) -> dict[str, Any]:
        tid = theme.get("theme_id") or _id("theme")
        record = {
            **theme,
            "theme_id": tid,
            "contains_business_logic": False,
            "affects_appearance_only": True,
            "registered_at": _now(),
        }
        self.store.theme_definitions.save(tid, record)
        return record


class VisualThemeEngine:
    """Enterprise Visual Theme Engine — appearance only, no business logic."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.registry = ThemeRegistry(self.store)
        self._active_theme_id = "enterprise_dark"
        self._live_refresh_count = 0

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.5",
            "theme_engine_ready": True,
            "branding_engine_ready": True,
            "theme_registry_ready": True,
            "live_theme_switching_ready": True,
            "contains_business_logic": False,
            "affects_appearance_only": True,
            "active_theme_id": self._active_theme_id,
            **full_catalog(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.5",
            "active_theme_id": self._active_theme_id,
            "registered_themes": len(self.store.theme_definitions.list_all()),
            "brand_profiles": len(self.store.brand_profiles.list_all()),
            "theme_engines": len(self.store.theme_engines.list_all()),
            "live_refreshes": self._live_refresh_count,
            "contains_business_logic": False,
            "affects_appearance_only": True,
            "modes": ["dark", "light"],
        }

    # Step 1 — Theme Engine
    def theme_engine_overview(self) -> dict[str, Any]:
        return {
            "title": "Theme Engine",
            "scopes": list(THEME_SCOPES),
            "registry": self.registry.list_themes(),
            "active_theme_id": self._active_theme_id,
            "contains_business_logic": False,
            "affects_appearance_only": True,
            "ready": True,
        }

    # Step 2 — Color System
    def color_system(self, mode: str = "dark") -> dict[str, Any]:
        m = mode if mode in DEFAULT_PALETTES else "dark"
        return {
            "mode": m,
            "tokens": list(COLOR_TOKENS),
            "palette": dict(DEFAULT_PALETTES[m]),
            "modes": ["dark", "light"],
            "ready": True,
        }

    # Step 3 — Enterprise Branding
    def branding(self, organization_id: str | None = None) -> dict[str, Any]:
        org = organization_id or "org_default"
        existing = None
        for p in self.store.brand_profiles.list_all():
            if p.get("organization_id") == org:
                existing = p
                break
        profile = existing or {
            "organization_id": org,
            "Logo": {"url": "/assets/brand/logo.svg", "alt": "Organization"},
            "Brand Colors": {"primary": "#3B82F6", "accent": "#22D3EE"},
            "Typography": {"display": "Söhne", "body": "Inter Display"},
            "Icons": {"set": "eds-outline", "weight": "regular"},
            "Dashboard Style": {"density": "comfortable", "card_radius": "md"},
            "contains_business_logic": False,
        }
        return {
            "fields": list(BRANDING_FIELDS),
            "profile": profile,
            "ready": True,
        }

    def upsert_brand_profile(self, patch: dict[str, Any]) -> dict[str, Any]:
        org = patch.get("organization_id") or "org_default"
        current = self.branding(org)["profile"]
        updated = {**current, **patch, "organization_id": org, "updated_at": _now()}
        updated["contains_business_logic"] = False
        pid = updated.get("brand_profile_id") or _id("brand")
        updated["brand_profile_id"] = pid
        self.store.brand_profiles.save(pid, updated)
        return updated

    # Step 4 — Component Theming
    def component_theming(self, theme_id: str | None = None) -> dict[str, Any]:
        tid = theme_id or self._active_theme_id
        theme = self.registry.get(tid)
        components = {
            name: {
                "themed": True,
                "surface": theme["colors"].get("Surface"),
                "primary": theme["colors"].get("Primary"),
                "mode": theme.get("mode"),
            }
            for name in COMPONENT_TARGETS
        }
        return {
            "theme_id": tid,
            "components": components,
            "targets": list(COMPONENT_TARGETS),
            "ready": True,
        }

    # Step 5 — AI Visual Style
    def ai_visual_style(self) -> dict[str, Any]:
        return {
            "styles": {
                "Avatar Frames": {"variants": ["ring", "hex", "soft"], "active": "ring"},
                "Role Colors": {"specialist": "#3B82F6", "concierge": "#A855F7", "lead": "#F59E0B"},
                "Department Colors": {"ops": "#22C55E", "knowledge": "#38BDF8", "build": "#F97316"},
                "Status Indicators": {"online": "#22C55E", "busy": "#F59E0B", "offline": "#64748B"},
                "Achievement Badges": {"shapes": ["medal", "star", "shield"]},
                "Future Character Styles": {"prepared": True, "runtime": "ai_city"},
            },
            "style_names": list(AI_VISUAL_STYLES),
            "contains_business_logic": False,
            "ready": True,
        }

    # Step 6 — Animation Themes
    def animation_themes(self) -> dict[str, Any]:
        return {
            "config": {
                "Animation Speed": {"value": "normal", "options": ["slow", "normal", "fast"]},
                "Transition Style": {"value": "ease-out", "options": ["linear", "ease-out", "spring"]},
                "Glow Effects": {"enabled": True, "intensity": "subtle"},
                "Connection Effects": {"enabled": True, "style": "pulse"},
                "Notification Effects": {"enabled": True, "style": "fade-slide"},
            },
            "keys": list(ANIMATION_THEME_KEYS),
            "ready": True,
        }

    # Step 7 — Accessibility
    def accessibility(self) -> dict[str, Any]:
        return {
            "features": {name: True for name in ACCESSIBILITY_FEATURES},
            "feature_names": list(ACCESSIBILITY_FEATURES),
            "high_contrast": True,
            "large_fonts": True,
            "reduced_motion": True,
            "color_safe_palette": True,
            "ready": True,
        }

    # Step 8 — Live Theme Switching
    def live_switch(self, theme_id: str) -> dict[str, Any]:
        theme = self.registry.get(theme_id)
        previous = self._active_theme_id
        self._active_theme_id = theme_id
        self._live_refresh_count += 1
        self.store.active_theme_state.save(
            "current",
            {
                "active_theme_id": theme_id,
                "previous_theme_id": previous,
                "switched_at": _now(),
                "requires_restart": False,
                "instant_visual_refresh": True,
                "refresh_count": self._live_refresh_count,
            },
        )
        return {
            "ok": True,
            "previous_theme_id": previous,
            "active_theme_id": theme_id,
            "theme": theme,
            "requires_restart": False,
            "instant_visual_refresh": True,
            "refresh_count": self._live_refresh_count,
            "contains_business_logic": False,
            "affects_appearance_only": True,
        }

    def active_theme(self) -> dict[str, Any]:
        theme = self.registry.get(self._active_theme_id)
        state = self.store.active_theme_state.get("current") or {}
        return {
            "active_theme_id": self._active_theme_id,
            "theme": theme,
            "state": state,
            "requires_restart": False,
            "instant_visual_refresh": True,
            "ready": True,
        }

    # Step 9 — AI City foundation
    def ai_city_foundation(self) -> dict[str, Any]:
        return {
            "title": "Foundation for AI City",
            "interfaces": {
                name: {"ready": True, "planned_runtime": "ai_city"}
                for name in AI_CITY_THEME_FOUNDATION
            },
            "interface_names": list(AI_CITY_THEME_FOUNDATION),
            "note": "Theme interfaces prepared; building/environment/season runtimes reserved for AI City.",
            "ready": True,
        }

    # Wizard
    def start_session(self) -> dict[str, Any]:
        sid = _id("theme")
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "draft": {
                "mode": "dark",
                "theme_id": self._active_theme_id,
                "organization_id": "org_default",
            },
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.theme_wizard_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.theme_wizard_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Theme session not found: {session_id}")
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
        self.store.theme_wizard_sessions.save(session_id, session)
        return session

    def summary(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        mode = session["draft"].get("mode") or "dark"
        return {
            "session_id": session_id,
            "title": "Visual Theme Engine Summary",
            "theme_engine": self.theme_engine_overview(),
            "color_system": self.color_system(mode),
            "branding": self.branding(session["draft"].get("organization_id")),
            "components": self.component_theming(session["draft"].get("theme_id")),
            "ai_visual_style": self.ai_visual_style(),
            "animation_themes": self.animation_themes(),
            "accessibility": self.accessibility(),
            "active_theme": self.active_theme(),
            "ai_city": self.ai_city_foundation(),
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        draft = session["draft"]
        mode = draft.get("mode") or "dark"
        org = draft.get("organization_id") or "org_default"

        engine_id = _id("theng")
        registry_id = _id("threg")
        brand = self.upsert_brand_profile(
            {
                "organization_id": org,
                "Brand Colors": DEFAULT_PALETTES[mode if mode in DEFAULT_PALETTES else "dark"],
            }
        )

        theme_engine = {
            "theme_engine_id": engine_id,
            "internal_id": engine_id,
            "catalog": self.catalog(),
            "active_theme_id": self._active_theme_id,
            "contains_business_logic": False,
            "affects_appearance_only": True,
            "registered_at": _now(),
            "sprint": "29.5",
        }
        theme_registry = {
            "theme_registry_id": registry_id,
            "internal_id": registry_id,
            "themes": self.registry.list_themes(),
            "contains_business_logic": False,
            "registered_at": _now(),
            "sprint": "29.5",
        }

        self.store.theme_engines.save(engine_id, theme_engine)
        self.store.theme_registries.save(registry_id, theme_registry)

        session["status"] = "created"
        session["registrations"] = {
            "theme_engine_id": engine_id,
            "theme_registry_id": registry_id,
            "brand_profile_id": brand["brand_profile_id"],
        }
        session["updated_at"] = _now()
        self.store.theme_wizard_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "theme_engine": theme_engine,
            "theme_registry": theme_registry,
            "brand_profile": brand,
            "message": "Theme Engine, Theme Registry, and Brand Profiles registered.",
        }
