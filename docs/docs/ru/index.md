---
hide:
  - navigation
  - footer
---

# FastStream

<b>Простейший способ интеграции потоков сообщений в ваши сервисы</b>

---

<p align="center">
  <a href="https://github.com/airtai/faststream/actions/workflows/test.yaml" target="_blank">
    <img src="https://github.com/airtai/faststream/actions/workflows/test.yaml/badge.svg?branch=main" alt="Test Passing"/>
  </a>

  <a href="https://coverage-badge.samuelcolvin.workers.dev/redirect/airtai/faststream" target="_blank">
      <img src="https://coverage-badge.samuelcolvin.workers.dev/airtai/faststream.svg" alt="Coverage">
  </a>

  <a href="https://www.pepy.tech/projects/faststream" target="_blank">
    <img src="https://static.pepy.tech/personalized-badge/faststream?period=month&units=international_system&left_color=grey&right_color=green&left_text=downloads/month" alt="Downloads"/>
  </a>

  <a href="https://pypi.org/project/faststream" target="_blank">
    <img src="https://img.shields.io/pypi/v/faststream?label=PyPI" alt="Package version">
  </a>

  <a href="https://pypi.org/project/faststream" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/faststream.svg" alt="Supported Python versions">
  </a>

  <br/>

  <a href="https://github.com/airtai/faststream/actions/workflows/codeql.yml" target="_blank">
    <img src="https://github.com/airtai/faststream/actions/workflows/codeql.yml/badge.svg" alt="CodeQL">
  </a>

  <a href="https://github.com/airtai/faststream/actions/workflows/dependency-review.yaml" target="_blank">
    <img src="https://github.com/airtai/faststream/actions/workflows/dependency-review.yaml/badge.svg" alt="Dependency Review">
  </a>

  <a href="https://github.com/airtai/faststream/blob/main/LICENSE" target="_blank">
    <img src="https://img.shields.io/github/license/airtai/faststream.png" alt="License">
  </a>

  <a href="https://github.com/airtai/faststream/blob/main/CODE_OF_CONDUCT.md" target="_blank">
    <img src="https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg" alt="Code of Conduct">
  </a>

  <a href="https://discord.gg/qFm6aSqq59" target="_blank">
      <img alt="Discord" src="https://img.shields.io/discord/1085457301214855171?logo=discord">
  </a>
</p>

---

## Особенности Проекта

[**FastStream**](https://faststream.airt.ai/) упрощает написание кода для работы с очередями сообщений, делая всю работу по сериализации, взаимодействию между сервисами и их документирования за вас!

Создание микросервисов для работы с потоками никогда не было таким простым. **FastStream** разработан для удобства работы даже Junior разработчиков, при этом не ограничивая вас в более сложных вариантах использования. Ниже приведены основные функции, которые делают **FastStream** идеальным фреймфорком для современных микросервисов, ориентированных на данные.

- **Поддержка разных брокеров**: **FastStream** Предоставляет унифицированный API для работы с различными брокерами сообщений (поддерживает **Kafka**, **RabbitMQ**, **NATS**).

- [**Pydantic валидация**](#_4): Используйте [**Pydantic**](https://docs.pydantic.dev/){.external-link target="_blank"}. для валидации, сериализации и проверки сообщений.

- [**Авто документация**](#_7): автоматическая [**AsyncAPI**](https://www.asyncapi.com/){.external-link target="_blank"} документацию для ваших сервисов.

- **Интуитивность**: Полная типизация упрощает процесс разработки, выявляя ошибки до того, как они попадут на прод.

- [**Внедрение зависимостей**](#_8): Эффективно управляйте зависимостями вашего сервиса с помощью встроенной DI системы **FastStream**.

- [**Тестируемость**](#_8): Поддерживает **In-Memory** тестирование, что делает ваш **CI/CD** быстрее и надежнее.

- **Расширяемость**: Вы можете переопределить практически любой функционал с помощью системы Middlewares и сериализаторов.

- [**Совместимость**](#http): **FastStream** полностью совместим с любым HTTP-фреймворком (особенно с [**FastAPI**](#fastapi)).

- [**Создан для автогенерации кода**](#_10): **FastStream** оптимизирован для автогенерации кода с помощью  LLM моделей, таких как GPT и Llama.

 **FastStream** — простой, эффективный и мощный. Независимо от того, начинаете ли вы использовать микросервисы потоковой передачи данных или хотите масштабироваться, **FastStream** поможет вам.

---

## История

**FastStream** — это новый пакет, основанный на идеях и опыте, полученном от [**FastKafka**](https://github.com/airtai/fastkafka){.external-link target="_blank"} и [**Propan**](https://github.com/lancetnik/propan){.external-link target="_blank"}. Объединив наши усилия, мы взяли лучшее из обоих пакетов и создали унифицированный способ написания сервисов, способных обрабатывать потоковые данные независимо от базового протокола. Мы продолжим поддерживать оба пакета, но новые возможности будут реализованы в этом проекте. Если вы пишете новый сервис, мы рекомендуем вам использовать именно **FastStream**.

---

## Установка

**FastStream** работает на **Linux**, **macOS**, **Windows** и на большинстве операционных систем **Unix**.
Вы просто можете установить его с помощью `pip`:

{!> includes/index/1.md !}

!!! tip ""
    По умолчанию **FastStream** использует **PydanticV2**, написанный на **Rust**, но вы можете понизить его версию вручную, если ваша платформа не поддерживает **Rust** — **FastStream** продолжит корректно работать с **PydanticV1**.

---

## Написание кода приложения

Брокеры **FastStream** предоставляют удобные декораторы `#!python @broker.subscriber` и `#!python @broker.publisher`, с помощью которых вы можете:

- потреблять и публиковать сообщения в очереди

- сериализовать и десериализовать данные автоматически

Эти декораторы позволяют легко определить схему ваших потребителей и производителей сообщений, позволяя вам сосредоточиться на основной бизнес-логике вашего приложения, не беспокоясь об интеграции.

Кроме того, **FastStream** использует [**Pydantic**](https://docs.pydantic.dev/){.external-link target="_blank"} для обработки входных данных.
Данные в кодировке JSON преобразуются в объекты Python, что упрощает работу со структурированными данными в ваших приложениях, поэтому вы можете сериализовать входные сообщения, просто используя аннотации типов.

Вот пример Python приложения, использующего **FastStream**, которое получает данные из входящего потока и отправляет результат в другой поток:

{!> includes/index/2.md !}

Кроме того, класс **Pydantic** [`BaseModel`](https://docs.pydantic.dev/usage/models/){.external-link target="_blank"} позволяет вам
определять стуртуру сообщения с использованием декларативного синтаксиса, что упрощает указание полей и типов ваших сообщений.

{!> includes/index/3.md !}

---

## Тестирование сервиса

Сервис можно протестировать с помощью контекстных менеджеров `TestBroker`, которые переводят брокер в специальный «режим тестирования».

Это перенаправит сообщений ваших `publisher` и `subscriber` на InMemory брокеры, что позволит вам быстро протестировать приложение без необходимости использования внешнего брокера и всех его зависимостей.

Используя **pytest**, тест для нашего сервиса будет выглядеть следующим образом:

{!> includes/index/4.md !}

## Запуск приложения

Приложение можно запустить с помощью встроенной **FastStream CLI**.

Чтобы запустить сервис, используйте **FastStream CLI** команду и передайте ей модуль (файл, в котором находится реализация приложения) и название объекта приложения.

``` shell
faststream run basic:app
```

После запуска команды вы должны увидеть следующий вывод:

``` {.shell .no-copy}
INFO     - FastStream app starting...
INFO     - input_data |            - `HandleMsg` waiting for messages
INFO     - FastStream app started successfully! To exit press CTRL+C
```

Кроме того, **FastStream** предоставляет "горячую" перезагрузку, которая значительно улучшит ваш опыт локальной разработки.

``` shell
faststream run basic:app --reload
```

И функцию горизонтального масштабирования вашего сервиса между процессами:

``` shell
faststream run basic:app --workers 3
```

Дополнительную информацию о функциях **CLI** можно узнать [здесь](./getting-started/cli/){.internal-link}

---

## Документация проекта

**FastStream** автоматически генерирует документацию для вашего проекта в соответствии со спецификацией [**AsyncAPI**](https://www.asyncapi.com/){.external-link target="_blank"}. Вы можете работать как со сгенерированными артефактами, так и просто размещать документацию на ресурсах и делать ее доступной для других команд.

Наличие такой документации существенно упрощает интеграцию сервисов: вы сразу можете увидеть с какими каналами и форматами сообщений работает приложение. И самое главное, это ничего не стоит — **FastStream** уже создал документацию за вас!

![HTML-page](../assets/img/AsyncAPI-basic-html-short.png){ loading=lazy }

---

## Зависимости

**FastStream** (благодаря [**FastDepend**](https://lancetnik.github.io/FastDepends/){.external-link target="_blank"}) имеет систему управления зависимостями, схожую с `pytest fixtures` и `FastAPI Depends`. Аргументы функций объявляют, какие зависимости вам нужны, а специальный декоратор доставляет их из глобального объекта Context.

```python linenums="1" hl_lines="9-10"
{!> docs_src/index/dependencies.py [ln:1,6-14] !}
```

---

## Интеграция с HTTP фреймворками

### Любой фреймворк

Вы можете использовать любой брокер **FastStream** даже без самого приложения `FastStream`.
Просто *запустите* и *остановите* его вместе с вашим приложения.

{! includes/index/integrations.md !}

### Плагин для **FastAPI**

Кроме того, **FastStream** можно использовать как часть **FastAPI**.

Просто импортируйте необходимый вам **StreamRouter** и используйте те же декораторы `#!python @router.subscriber(...)` and `#!python @router.publisher(...)`.

!!! tip
    В этом случае **FastStream** не использует собственную систему зависимостей и сериализацию, а напрямую интегрируется в **FastAPI**.
    Это означает, что вы можете использовать `Depends`, `BackgroundTasks` и другие инструменты **FastAPI**, как если бы это была обычная HTTP функция.

{! includes/getting_started/integrations/fastapi/1.md !}

!!! note
    Дополнительные информацию об интеграции можно найти [здесь](./getting-started/integrations/fastapi/){.internal-link}

---

## Генератор кода

Как видно, **FastStream** — невероятно удобный фреймворк. Однако мы пошли еще дальше и сделали его еще более удобным для пользователя! Представляем [**faststream-gen**](https://faststream-gen.airt.ai){.external-link target="_blank"}, Python библиотеку, которая использует возможности генеративного ИИ для создания **FastStream** приложения. Просто опишите требования к вашему приложению, и [**faststream-gen**](https://faststream-gen.airt.ai){.external-link target="_blank"} создаст проект **FastStream**, готовый к развертыванию в кратчайшие сроки.

Сохраните описание приложения внутри `description.txt`:

```
{!> docs_src/index/app_description.txt !}
```

и выполните следующую команду, чтобы создать новый **FastStream** проект:

``` shell
faststream_gen -i description.txt
```

``` {.shell .no-copy}
✨  Generating a new FastStream application!
 ✔ Application description validated.
 ✔ FastStream app skeleton code generated. akes around 15 to 45 seconds)...
 ✔ The app and the tests are generated.  around 30 to 90 seconds)...
 ✔ New FastStream project created.
 ✔ Integration tests were successfully completed.
 Tokens used: 10768
 Total Cost (USD): $0.03284
✨  All files were successfully generated!
```

### Туториал

Мы также приглашаем вас изучить наше руководство, в котором мы проведем вас через процесс использования [**faststream-gen**](https://faststream-gen.airt.ai){.external-link target=" _blank"} - Python библиотеки для легкого создания **FastStream** приложений:

- [Анализ криптовалют с помощью FastStream](https://faststream-gen.airt.ai/Tutorial/Cryptocurrency_Tutorial/){.external-link target="_blank"}

---

## Будьте на связи

Пожалуйста, проявите свою поддержку и оставайтесь на связи:

- поставьте звезду в [GitHub репозитории](https://github.com/airtai/faststream/){.external-link target="_blank"}

- присоединяйтесь к нашему [Discord серверу](https://discord.gg/CJWmYpyFbc){.external-link target="_blank"}

- или [Telegram каналу](https://t.me/propan_python){.external-link target="_blank"} русскоязычного сообщества

Ваша поддержка помогает нам оставаться на связи и побуждает продолжать развивать и совершенствовать фреймворк. Спасибо за вашу
поддержку!

---

## Авторы

Спасибо всем этим замечательным людям, которые сделали проект лучше!

<a href="https://github.com/airtai/faststream/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=airtai/faststream"/>
</a>
