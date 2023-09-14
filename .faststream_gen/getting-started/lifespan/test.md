# Events Testing

In the most cases you are testing your subsriber/publisher functions, but sometimes you need to trigger some lifespan hooks in your tests too.

This reason **FastStream** has a special **TestApp** patcher working as a regular async context manager.

{! includes/getting_started/lifespan/testing.md !}

!!! tip
    If you are using connected broker inside your lifespan hooks, you should batch the broker at first (before application patching)
