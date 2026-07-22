# Administrator Guide — Agro Enterprise Suite v4.4.0-enterprise

## Responsibilities

- Maintain module API health and auth middleware configuration
- Run certification suite before major releases
- Monitor executive readiness, security, and performance dashboards
- Manage environment configuration from `config.template.env`

## Key endpoints

- Certification health: `/api/agro-enterprise-certification/v1/health`
- Full certification run: `POST /api/agro-enterprise-certification/v1/bootstrap`
- Executive dashboard: `/api/agro-enterprise-certification/v1/executive`

## Frozen platforms

Do not modify Platform Core, AI OS, Enterprise Edition, or Automotive Enterprise Platform when operating Agro Enterprise.
