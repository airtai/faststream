from faststream import Context, apply_types


@broker.subscriber("test")
async def handler(body: dict):
    nested_func()


@apply_types
def nested_func(body: dict, logger=Context()):
    logger.info(body)
