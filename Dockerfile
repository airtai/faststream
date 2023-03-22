ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION}-slim-bullseye

SHELL ["/bin/bash", "-c"]

RUN apt update && apt install -y curl git \
    && curl -fsSL https://deb.nodesource.com/setup_19.x | bash - && apt-get install -y nodejs \
    && apt purge --auto-remove && apt clean && rm -rf /var/lib/apt/lists/*

COPY scripts/start_fastkafka.sh ./

WORKDIR /fastkafka
EXPOSE 8000

ENTRYPOINT []
CMD ["/bin/bash", "-c", "/start_fastkafka.sh"]
