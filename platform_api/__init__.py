# Platform API v1.0 — frozen public contracts and versioning.

from platform_api.contracts import API_CONTRACT_VERSION, PLATFORM_API_VERSION
from platform_api.errors import ApiError, ErrorResponse
from platform_api.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from platform_api.responses import ApiEnvelope, error_response, success_response
from platform_api.versioning import (
    MANAGEMENT_V1_PREFIX,
    PUBLIC_V1_PREFIX,
    deprecated,
    register_dual_prefix_routes,
)

__all__ = [
    "API_CONTRACT_VERSION",
    "PLATFORM_API_VERSION",
    "ApiError",
    "ApiEnvelope",
    "ErrorResponse",
    "MANAGEMENT_V1_PREFIX",
    "PUBLIC_V1_PREFIX",
    "PaginatedResponse",
    "PaginationMeta",
    "PaginationParams",
    "deprecated",
    "error_response",
    "register_dual_prefix_routes",
    "success_response",
]
