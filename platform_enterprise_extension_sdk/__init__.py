"""Enterprise Extension SDK & Marketplace Foundation — Sprint 25.0 / v8.0.0.

Design target: src/modules/enterprise-extension-sdk → platform_enterprise_extension_sdk.
Extensions connect via SDK/API only — never by modifying Enterprise Core or calling internals directly.
"""

from platform_enterprise_extension_sdk.facade import ExtensionSDKLibrary, extension_sdk_library

__all__ = ["ExtensionSDKLibrary", "extension_sdk_library"]
