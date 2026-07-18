"""Plugin entry point — Insurance."""


def register(ctx):
    ctx.log("Insurance plugin registered")
    return {"plugin_id": ctx.plugin_id, "status": "registered"}


async def on_enable(ctx):
    ctx.log("Insurance plugin enabled")


async def on_disable(ctx):
    ctx.log("Insurance plugin disabled")


async def health(ctx):
    return {"status": "healthy", "domain": "insurance"}
