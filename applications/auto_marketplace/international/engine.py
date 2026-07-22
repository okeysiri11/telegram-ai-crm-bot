# International shipping helpers — regulations catalog.

from __future__ import annotations

REGULATIONS = {
    ("US", "EU"): ["UNECE compliance", "CO2 labeling"],
    ("EU", "US"): ["EPA certification", "DOT standards"],
    ("JP", "US"): ["EPA certification", "right-hand conversion note"],
    ("DE", "TR"): ["TSE conformity", "import permit"],
}


class InternationalEngine:
    def regulations(self, origin: str, destination: str) -> list[str]:
        key = (origin.upper(), destination.upper())
        return list(REGULATIONS.get(key, ["General import inspection", "Proof of ownership"]))

    def metrics(self) -> dict:
        return {"regulation_pairs": len(REGULATIONS)}


international_engine = InternationalEngine()
