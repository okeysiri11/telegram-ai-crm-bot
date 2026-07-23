"""Example plugin entrypoint."""


class Plugin:
    def on_load(self, sdk):
        return {"ok": True, "kind": "plugin"}
