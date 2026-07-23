"""Example ai_agent entrypoint."""


class Agent:
    def on_load(self, sdk):
        return {"ok": True, "kind": "ai_agent"}
