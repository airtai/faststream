from fastapi import FastAPI

from faststream.nats.fastapi import Logger, NatsRouter

router = NatsRouter()
app = FastAPI(lifespan=router.lifespan_context)
app.include_router(router)


@router.subscriber("test")
async def handler(msg, logger: Logger):
    logger.info(msg)


@router.after_startup
async def t(app):
    await router.broker.publish("test", "test")
