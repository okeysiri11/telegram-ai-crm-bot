# Enterprise Security Verification

**Version:** `8.5.0`  
**Sprint:** 25.5  
**API:** `/api/enterprise-esv/v1`  
**Library:** `platform_enterprise_security_verification/`  
**Hub attr:** `enterprise_hub.security_verification`  
**Design path:** `src/platform/security` → `platform_enterprise_security_verification/` (CI/CD gate)

Centralized pre-release security verification with a unified Security Report. Production is blocked when critical vulnerabilities are present. Verification only — no exploit payloads. Distinct from Security Hardening (`/api/enterprise-esh/v1`) and ISAM (`/api/enterprise-isam/v1`).

## Readiness

Security Verification Ready · Vulnerability Scanner Ready · Secret Scanner Ready · Compliance Ready
