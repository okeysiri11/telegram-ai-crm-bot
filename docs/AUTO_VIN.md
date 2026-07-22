# Auto VIN Intelligence — Sprint 10.2

VIN decoding and OEM intelligence for **Auto Marketplace 1.2.0-alpha** (`vin_engine = 1.0`).

| Field | Value |
|-------|-------|
| Application version | `1.2.0-alpha` |
| VIN engine | `1.0` |
| API | `/api/auto/v1/vin` · `/api/auto/v1/history` |

**Hard constraint:** Platform Core, Ecosystem, Agro Marketplace, and Port ERP are not modified.

## VIN Intelligence

- VIN decoding (WMI / VDS / VIS)
- Factory configuration
- Production date / year
- Country & plant
- Engine / transmission / body / drive / fuel
- Options
- Recalls
- Service campaigns
- OEM specifications

## Vehicle History

Ownership · Registration · Mileage · Insurance claims · Accidents · Repairs · Service records · Import/Export · Theft status · Lien status · Inspection history

```python
from applications.auto_marketplace import auto_marketplace

decoded = auto_marketplace.marketplace.vin.decode("JTDBR32E720123456")
assert decoded.valid is True
assert auto_marketplace.config.vin_engine == "1.0"
```
