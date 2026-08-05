# City Districts

**Sprint:** 30.4  
**Files:** `cityDistricts.ts` · `cityCatalog.ts`

## Beta set (16)

| ID | EN | RU |
|----|----|----|
| settings | Administration | Администрация |
| crm | CRM | CRM |
| erp | ERP | ERP |
| finance | Finance | Финансы |
| enterprise | Production | Производство |
| warehouse | Warehouse | Склад |
| legal | Legal | Юридический отдел |
| marketing | Marketing | Маркетинг |
| ai | AI Center | AI-центр |
| security | Security Center | Центр безопасности |
| analytics | Analytics | Аналитика |
| documents | Documents | Документы |
| marketplace | Marketplace | Маркетплейс |
| production | Production Studio | Продакшн-студия |
| knowledge | Knowledge Center | Центр знаний |
| developer | Developer Zone | Зона разработчика |

## Rules

- Districts are presentation metadata (label, centroid, CSS).  
- Buildings own `route` — only existing platform paths.  
- Quick-jump chips and map labels use `labelRu`.  
- Street graph: plaza → hubs + intra-district edges.

See [CITY_BUILDINGS.md](./CITY_BUILDINGS.md).
