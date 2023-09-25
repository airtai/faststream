from faststream import Context, ContextRepo, FastStream

app = FastStream()


@app.on_startup
async def setup(context: ContextRepo):
    context.set_global("field", 1)


@app.on_startup
async def setup_later(field: int = Context()):
    assert field == 1
