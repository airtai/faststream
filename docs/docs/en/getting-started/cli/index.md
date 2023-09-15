# CLI

**FastStream** has its own built-in **CLI** tool for your maximum comfort as a developer.

!!! quote ""
    Thanks to [*typer*](https://typer.tiangolo.com/){.external-link target="_blank"} and [*watchfiles*](https://watchfiles.helpmanual.io/){.external-link target="_blank"}. Their work is the basis of this tool.

```bash
faststream --help
```

```console
Usage: faststream [OPTIONS] COMMAND [ARGS]...

  Generate, run and manage FastStream apps to greater development experience

Options:
  -v, --version                   Show current platform, python and FastStream
                                  version
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  docs  AsyncAPI schema commands
  run   Run [MODULE:APP] FastStream application
```

## Run the project

### Multiprocessing scaling

**FastStream** allows you to scale application right from the command line by running you application in the Process pool.

Just set `--worker` option to scale your application:

```bash
faststream run serve:app --workers 2
```

```console
2023-09-14 21:24:49,726 INFO     - Started parent process [7591]
2023-09-14 21:24:49,731 INFO     - Started child process [7593]
2023-09-14 21:24:49,735 INFO     - Started child process [7594]
2023-09-14 21:24:50,543 INFO     - test |            - `Handle` waiting for messages
2023-09-14 21:24:50,600 INFO     - test |            - `Handle` waiting for messages
```

### Hotreload

Thanks to [*watchfiles*](https://watchfiles.helpmanual.io/){.external-link target="_blank"}, written in *Rust*, you can
work with your project easily. Edit the code as much as you like - the new version has already been launched and is waiting for your requests!

```bash
faststream run serve:app --reload
```

```console
2023-09-14 21:27:20,727 INFO     - Started reloader process [7902] using WatchFiles
2023-09-14 21:27:21,638 INFO     - FastStream app starting...
2023-09-14 21:27:21,655 INFO     - test |            - `Handle` waiting for messages
2023-09-14 21:27:21,676 INFO     - FastStream app started successfully! To exit press CTRL+C
```

### Environment Management

You can pass any custom flags and launch options to the **FastStream CLI** even without first registering them. Just use them when launching the application - and they will be right in your environment.

Use this option to select environment files, configure logging, or at your discretion.

For example, we will pass the *.env* file to the context of our application:

```bash
faststream run serve:app --env=.env.dev
```

```console
2023-09-14 21:28:38,191 INFO     - FastStream app starting...
2023-09-14 21:28:38,213 INFO     - test |            - `Handle` waiting for messages
2023-09-14 21:28:38,230 INFO     - FastStream app started successfully! To exit press CTRL+C
```

{! includes/getting_started/cli/env.md !}

!!! note
    Note that the `env` parameter was passed to the `setup` function directly from the command line

All passed values can be of type `#!python bool`, `#!python str` or `#!python list[str]`.

In this case, the flags will be interpreted as follows:

```bash
faststream run app:app --flag       # flag = True
faststream run app:app --no-flag    # flag = False
faststream run app:app --my-flag    # my_flag = True
faststream run app:app --key value  # key = "value"
faststream run app:app --key 1 2    # key = ["1", "2"]
```
You can use them both individually and together in unlimited quantities.

## AsyncAPI Schema

Also, **FastStream CLI** allows you to work with the **AsyncAPI** schema in a simple way.

You are able to generate `.json` or `.yaml` files by your application code or host **HTML** representation directly:

```bash
faststream docs --help
```

```console
Usage: faststream docs [OPTIONS] COMMAND [ARGS]...

  AsyncAPI schema commands

Options:
  --help  Show this message and exit.

Commands:
  gen    Generate project AsyncAPI schema
  serve  Serve project AsyncAPI schema
```

To know more about the commands above, please visit [**AsyncAPI** export](../asyncapi/export.md){.internal-link} and [**AsyncAPI** hosting](../asyncapi/hosting.md){.internal-link}.
