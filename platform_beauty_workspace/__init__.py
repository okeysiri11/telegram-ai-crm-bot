"""Beauty Workspace & Reception Desk — Sprint 22.3 / v6.4.0.

Design target: src/modules/beauty-workspace (import path platform_beauty_workspace).
Reception UI coordination layer over Beauty OS — no duplicated business logic.
AI Assistant proposes only; never executes.
"""

from platform_beauty_workspace.facade import BeautyWorkspaceLibrary, beauty_workspace_library

__all__ = ["BeautyWorkspaceLibrary", "beauty_workspace_library"]
