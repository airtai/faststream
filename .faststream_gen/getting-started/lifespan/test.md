# Events Testing

In the most cases you are testing your subsriber/publisher functions, but sometimes you need to trigger some lifespan hooks in your tests too.

For this reason, **FastStream** has a special **TestApp** patcher working as a regular async context manager.

{! includes/getting_started/lifespan/testing.md !}

!!! tip
    If you are using a connected broker inside withing your lifespan hooks, it's advisable to patch the broker first (before applying the application patch).
