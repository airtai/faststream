---
hide:
  - navigation
  - footer
---

# FastStream

<b>Простая интеграция потоков событий в ваши сервисы</b>

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

## Функции

[**FastStream**](https://faststream.airt.ai/) 
упрощает процесс написания producers и consumers для брокеров сообщений, обрабатывая все автоматическим анализом, созданием сетей и созданием документации.

Создание потоковых микросервисов никогда не было простым. **FastStream**, разработанный специально для junior разработчиков, упрощает вашу работу, при этом сохраняя возможность для более сложных вариантов использования. Ниже приведены основные функции, которые выполняет **FastStream**. Подходящий фреймфорк для современных микросервисов, ориентированных на данные.

- **Несколько брокеров**: **FastStream** Предоставляет унифицированный (общий) API для работы с несколькими брокерами сообщений (поддерживает **Kafka**, **RabbitMQ**, **NATS** и другие).

- [**Pydantic валидация**](#writing-app-code): Используйте [**Pydantic**](https://docs.pydantic.dev/){.external-link target="_blank"}. для валидации, сериализации и проверки сообщений.

- [**Авто документация**](#project-documentation): Будьте впереди с автоматической документацией [**AsyncAPI**](https://www.asyncapi.com/){.external-link target="_blank"}.

- **Интуитивный**: Полная типизация упрощает процесс разработки, выявляя ошибки до того, как они выявятся.

- [**Мощная система Dependency Injection**](#dependencies): Эффективно управляйте зависимостями вашего сервиса с помощью встроенной системы DI в **FastStream**.

- [**Тестируемый**](#testing-the-service): Поддерживает in-memory тесты, что делает ваш процесс CI/CD быстрее и надежнее.

- **Расширяемый**: Используйте расширения для собственной сериализации и мидлевари.

- [**Интеграционный**](#any-framework): **FastStream** полностью совместим с любым HTTP-фреймворком, которую вы хотите использовать (особенно с [**FastAPI**](#fastapi-plugin)).

- [**Создан для автогенерации кода**](#code-generator): **FastStream** оптимизирован для автогенерации кода с использованием расширяемых моделей, таких как GPT и Llama.

 **FastStream** — простой, эффективный и мощный. Независимо от того, начнёте ли вы использовать микросервисы потоковой передачи или хотите масштабироваться, **FastStream** поможет вам.

---

## История

**FastStream** — это новый пакет, основанный на идеях и опыте, полученном от [**FastKafka**](https://github.com/airtai/fastkafka){.external-link target="_blank"} и [ **Propan**](https://github.com/lancetnik/propan){.external-link target="_blank"}. Объединив наши усилия, мы взяли лучшее из обоих пакетов и создали унифицированный (общий) способ написания сервисов, способных обрабатывать потоковые данные без необходимости использования базового протокола. Мы продолжим поддерживать оба пакета, но в этом проекте будут новые возможности. Если вы пишете новый сервис, этот пакет является рекомендуемым для разработки.

---

## Установка

**FastStream** работает на **Linux**, **macOS**, **Windows** и на большинстве операционных систем **Unix**.
Вы можете установить его с помощью `pip`:

{!> includes/index/1.md !}

!!! tip ""
    По умолчанию **FastStream** использует **PydanticV2**, написанный на **Rust**, но вы можете понизить его версию вручную, если ваша платформа не поддерживает **Rust** — **FastStream** будет корректно работать с * *PydanticV1** тоже.

---

## Написание кода приложения

Брокеры **FastStream** предоставляют удобные декораторы `#!python @broker.subscriber`
и `#!python @broker.publisher`, чтобы вы могли делегировать фактический процесс:

- потребление и создание данных в очереди событий, а также

- декодирование и кодирование JSON сообщений.

Эти декораторы позволяют легко указать логику обработки для ваших consumers и producers, позволяя вам сосредоточиться на основной бизнес-логике вашего приложения, не беспокоясь о базовой интеграции.

Кроме того, **FastStream** использует [**Pydantic**](https://docs.pydantic.dev/){.external-link target="_blank"} для обработки входных данных.
Данные в кодировке JSON преобразуются в объекты Python, что упрощает работу со структурированными данными в ваших приложениях, поэтому вы можете сериализовать входные сообщения, просто используя аннотации типов

Вот пример приложения Python, использующего **FastStream**, которое получает данные из входящего потока данных и выводит данные в другой поток:

{!> includes/index/2.md !}

Кроме того, класс [`BaseModel`](https://docs.pydantic.dev/usage/models/){.external-link target="_blank"} в **Pydantic** позволяет вам
определять сообщения с использованием декларативного синтаксиса, что упрощает указание полей и типов ваших сообщений.

{!> includes/index/3.md !}

---

## Тестирование сервиса

Сервис можно протестировать с помощью контекстных менеджеров `TestBroker`, которые по умолчанию переводят брокера в «режим тестирования».

Tester перенаправит ваши оформленные функции `subscriber` и `publisher` на InMemory брокеры, что позволит вам быстро протестировать приложение без необходимости использования работающего брокера и всех его зависимостей.

Используя pytest, тест нашего сервиса будет выглядеть так:

{!> includes/index/4.md !}

## Запуск приложения

Приложение можно запустить с помощью встроенной CLI команды **FastStream**.

Чтобы запустить сервис, используйте **FastStream CLI** команду и передайте ей модуль (в данном случае файл, в котором находится реализация приложения) и символ приложения.

``` shell
faststream run basic:app
```

После запуска команды вы должны увидеть следующий вывод:

``` shell
INFO     - FastStream app starting...
INFO     - input_data |            - `HandleMsg` waiting for messages
INFO     - FastStream app started successfully! To exit press CTRL+C
```

Кроме того, **FastStream** предоставляет отличную функцию "горячей" перезагрузки, которая улучшит ваш опыт разработки.

``` shell
faststream run basic:app --reload
```

А также функцию горизонтального масштабирования многопроцессорной обработки:

``` shell
faststream run basic:app --workers 3
```

Дополнительную информацию о функциях **CLI** можно узнать [здесь](./getting-started/cli/index.md){.internal-link}

---

## Документация проекта

**FastStream** автоматически генерирует документацию для вашего проекта в соответствии со спецификацией [**AsyncAPI**](https://www.asyncapi.com/){.external-link target="_blank"}. Вы можете работать как со сгенерированными артефактами, размещать документацию на ресурсах, доступная соответствующим командам.

Наличие такой документации существенно упрощает интеграцию сервисов: вы сразу можете увидеть с какими каналами и форматами сообщений работает приложение. И самое главное, это ничего не будет стоить — **FastStream** уже создал для вас документацию!

![HTML-page](../assets/img/AsyncAPI-basic-html-short.png)

---

## Зависимости

**FastStream** (благодаря [**FastDepend**](https://lancetnik.github.io/FastDepends/){.external-link target="_blank"}) имеет систему управления зависимостями, аналогичную `pytest fixtures` и `FastAPI Depends`. Аргументы функций объявляют, какие зависимости вам нужны, а специальный декоратор доставляет их из глобального объекта Context.

```python linenums="1" hl_lines="9-10"
{!> docs_src/index/dependencies.py [ln:1,6-14] !}
```

---

## Интеграция с http фреймворком

### Любой фреймворк

Вы можете использовать **FastStream** `MQBrokers` без приложения `FastStream`.
Просто *запустите* и *остановите* их в зависимости от срока службы вашего приложения.

{! includes/index/integrations.md !}

### **FastAPI** Плагин

Кроме того, **FastStream** можно использовать как часть **FastAPI**.

Just import a **StreamRouter** you need and declare the message handler with the same `#!python @router.subscriber(...)` and `#!python @router.publisher(...)` decorators.

!!! tip
    При таком использовании **FastStream** не использует собственную систему зависимостей и сериализацию, а легко интегрируется в **FastAPI**.
    Это означает, что вы можете использовать `Depends`, `BackgroundTasks` и другие инструменты **FastAPI**, как если бы это была обычная HTTP endpoint.

{! includes/getting_started/integrations/fastapi/1.md !}

!!! note
    Дополнительные функции интеграции можно найти [здесь](./getting-started/integrations/fastapi/index.md){.internal-link}

---

## Генератор кода

Как видно, **FastStream** — невероятно удобная библиотека. Однако мы пошли еще дальше и сделали его еще более удобным для пользователя! Представляем [**faststream-gen**](https://faststream-gen.airt.ai){.external-link target="_blank"}, Python библиотеку, которая использует возможности генеративного ИИ для легкой генерации **FastStream** приложения. Просто опишите требования к вашему приложению, и [**faststream-gen**](https://faststream-gen.airt.ai){.external-link target="_blank"} создаст рабочий и высококлассный проект **FastStream**, готовый к развертыванию в кратчайшие сроки.

Сохраните описание приложения внутри `description.txt`:
```
{!> docs_src/index/app_description.txt !}
```


и выполните следующую команду, чтобы создать новый **FastStream** проект:

``` shell
faststream_gen -i description.txt
```

``` shell
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

Мы также приглашаем вас изучить наше руководство, в котором мы проведем вас через процесс использования [**faststream-gen**](https://faststream-gen.airt.ai){.external-link target=" _blank"} Python библиотека для легкого создания приложений **FastStream**:

- [Анализ криптовалют с помощью FastStream](https://faststream-gen.airt.ai/Tutorial/Cryptocurrency_Tutorial/){.external-link target="_blank"}

---

## Будьте на связи

Пожалуйста, проявите свою поддержку и оставайтесь на связи:

- [GitHub репозиторий](https://github.com/airtai/faststream/){.external-link target="_blank"} a star, and

- присоединяюсь к нашему [Discord серверу](https://discord.gg/CJWmYpyFbc){.external-link target="_blank"}

Ваша поддержка помогает нам оставаться на связи с вами и побуждает нас
продолжать развивать и совершенствовать библиотеку. Спасибо за вашу
поддержку!

---

## Авторы

Спасибо всем этим замечательным людям, которые сделали проект лучше!

<a href="https://github.com/airtai/faststream/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=airtai/faststream"/>
</a>
