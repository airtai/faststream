import pytest

from faststream.kafka import TestKafkaBroker

from .app import Post, broker, on_new_post, on_popular_post


@broker.subscriber("just_text")
async def on_just_text(msg: str) -> None:
    pass


@pytest.mark.asyncio
async def test_post_with_just_two_likes():
    async with TestKafkaBroker(broker):
        await broker.publish(
            Post(user_id=1, text="bad post", number_of_likes=2), "new_post"
        )
        on_new_post.mock.assert_called_with(
            dict(Post(user_id=1, text="bad post", number_of_likes=2))
        )
        on_popular_post.mock.assert_not_called()
        on_just_text.mock.assert_not_called()


@pytest.mark.asyncio
async def test_post_with_many_likes():
    async with TestKafkaBroker(broker):
        await broker.publish(
            Post(user_id=1, text="cool post", number_of_likes=100), "new_post"
        )
        on_new_post.mock.assert_called_with(
            dict(Post(user_id=1, text="cool post", number_of_likes=100))
        )
        on_popular_post.mock.assert_called_with(
            dict(Post(user_id=1, text="cool post", number_of_likes=100))
        )
        on_just_text.mock.assert_called_with("cool post")
