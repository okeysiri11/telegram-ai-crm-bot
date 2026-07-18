"""Plugin entry point — Medical."""


def register(ctx):
    ctx.log("Medical plugin registered")
    return {"plugin_id": ctx.plugin_id, "status": "registered"}


async def on_enable(ctx):
    ctx.log("Medical plugin enabled")


async def on_disable(ctx):
    ctx.log("Medical plugin disabled")


async def health(ctx):
    return {"status": "healthy", "domain": "medical"}
