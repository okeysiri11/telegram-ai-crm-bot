# Register ecosystem API routes.

from __future__ import annotations

from aiohttp import web

from ecosystem.api import handlers
from ecosystem.api.middleware import ecosystem_auth_middleware
from ecosystem.config import DEFAULT_CONFIG


def register_ecosystem_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    app.middlewares.append(ecosystem_auth_middleware)

    # Health
    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_get(f"{prefix}/manifest", handlers.manifest_handler)

    # Identity API
    identity = f"{prefix}/identity"
    app.router.add_post(f"{identity}/auth/register", handlers.register_handler)
    app.router.add_post(f"{identity}/auth/login", handlers.login_handler)
    app.router.add_post(f"{identity}/auth/sso", handlers.sso_login_handler)
    app.router.add_route("*", f"{identity}/profile", handlers.profile_handler)
    app.router.add_get(f"{identity}/devices", handlers.devices_handler)
    app.router.add_get(f"{identity}/sessions/history", handlers.session_history_handler)
    app.router.add_post(f"{identity}/mfa/enroll", handlers.mfa_enroll_handler)

    # Organization API
    org = f"{prefix}/organizations"
    app.router.add_post(org, handlers.create_organization_handler)
    app.router.add_get(org, handlers.list_organizations_handler)
    app.router.add_post(f"{org}/workspaces", handlers.create_workspace_handler)
    app.router.add_post(f"{org}/invitations", handlers.invite_member_handler)
    app.router.add_get(f"{prefix}/roles", handlers.list_roles_handler)

    # Workspace API
    ws = f"{prefix}/workspace"
    app.router.add_get(f"{ws}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{ws}/search", handlers.global_search_handler)
    app.router.add_route("*", f"{ws}/favorites", handlers.favorites_handler)
    app.router.add_route("*", f"{ws}/notifications", handlers.notifications_handler)
    app.router.add_get(f"{ws}/quick-actions", handlers.quick_actions_handler)

    # Navigation API
    nav = f"{prefix}/navigation"
    app.router.add_get(nav, handlers.navigation_handler)
    app.router.add_post(f"{nav}/open", handlers.open_application_handler)

    # AI Assistant
    app.router.add_post(f"{prefix}/assistant", handlers.assistant_handler)

    # Cross-application shared services
    shared = f"{prefix}/shared"
    app.router.add_route("*", f"{shared}/{{service}}", handlers.shared_services_handler)
