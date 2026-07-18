"""Plugin entry point — Agro."""


def register(ctx):
    ctx.log("Agro plugin registered")
    return {"plugin_id": ctx.plugin_id, "status": "registered"}


async def on_enable(ctx):
    ctx.log("Agro plugin enabled")


async def on_disable(ctx):
    ctx.log("Agro plugin disabled")


async def health(ctx):
    return {"status": "healthy", "domain": "agro"}
