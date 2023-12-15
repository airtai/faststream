---
# 0.5 - API
# 2 - Release
# 3 - Contributing
# 5 - Template Page
# 10 - Default
search:
  boost: 10
---

# Lifespan Context Manager

Also, you can define *startup* and *shutdown* logic using the `lifespan` parameter of the **FastSTream** app, and a "context manager" (I'll show you what that is in a second).

Let's start with an example from [hooks page](./hooks.md#another-example){.internal-link} and refactor it using "context manager".

We create an async function `lifespan()` with `#!python yield` like this:

{! includes/getting_started/lifespan/ml_context.md !}

As you can see, `lifespan` parameter is much suitable for case (than `#!python @app.on_startup` and `#!python @app.after_shutdown` separated calls) if you have object needs to process at application startup and shutdown both.

!!! tip
    `lifespan` starts **BEFORE** your broken started (`#!python @app.on_startup` hook) and **AFTER** broker was shutdown (`#!python @app.after_shutdown`), so you can't publish any messages here.

    If you want to make some actions will *already/still running broker*, please use `#!python @app.after_startup` and `#!python @app.on_shutdown` hooks.

Also, `lifespan` supports all **FastStream** hooks features:

* Dependency Injection
* [extra **CLI**](../cli/index.md#environment-management){.internal-link} options passing
