from fastapi import FastAPI

from faststream.kafka.fastapi import KafkaRouter

router = KafkaRouter(schema_url=None)
app = FastAPI(lifespan=router.lifespan_context)
app.include_router(router)
