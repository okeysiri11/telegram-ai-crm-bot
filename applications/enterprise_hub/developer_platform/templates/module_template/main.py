"""Example module entrypoint."""


class Module:
    def on_load(self, sdk):
        return {"ok": True, "kind": "module"}
