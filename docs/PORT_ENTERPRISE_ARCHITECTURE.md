# Port Enterprise Architecture

**Version:** `4.6.0-enterprise`  
**Sprint:** 15.8  
**Suite:** Port Enterprise Suite  
**Foundation:** Enterprise Platform v4.5.7-enterprise

## Layers

1. Foundation (15.0) — ports, terminals, cargo, fleet, operations
2. Navigation (15.1) — VTS / AIS / radar / safety
3. Containers (15.2) — yard, equipment, twin, automation
4. Multimodal (15.3) — rail, truck, inland, shipments
5. Customs (15.4) — border, trade, compliance, documents
6. Warehouse (15.5) — FEZ, distribution, inventory, automation
7. Freight Marketplace (15.6) — exchange, carriers, global network
8. AI Port Director (15.7) — predictive, autonomous, executive AI
9. Certification (15.8) — architecture, security, performance, release

## Integration

Additive APIs share `PortEnterpriseStore`. Platform Core, AI OS, Enterprise, Automotive, and Agro remain frozen dependencies.
