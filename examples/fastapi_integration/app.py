from fastapi import FastAPI

from faststream.rabbit.fastapi import RabbitRouter

router = RabbitRouter("amqp://guest:guest@localhost:5672/")
app = FastAPI(lifespan=router.lifespan_context)

publisher = router.publisher("response-q")


@publisher
@router.subscriber("test-q")
async def handler(user_id: int):
    print(user_id)
    return f"{user_id} created"


app.include_router(router)
