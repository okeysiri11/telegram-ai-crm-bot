# Anti-Parsing Protection

**Sprint:** 32.4 · **Module:** `platform_security.anti_parsing.AntiParsingProtection`

## Protects

Enterprise City visualization · Knowledge Base · API endpoints · Marketplace data

## Capabilities

Bot / crawler / scraping detection · behavior analysis · request fingerprinting · adaptive rate limiting · dynamic challenges · session integrity · access pattern analysis

## Usage

```python
from platform_security.anti_parsing import AntiParsingProtection

ap = AntiParsingProtection()
ap.analyze(ip="1.2.3.4", user_agent="Mozilla/5.0", path="/city", surface="enterprise_city")
```

Complements (does not replace) `middleware/security_middleware` rate limiting.
