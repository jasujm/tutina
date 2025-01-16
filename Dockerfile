FROM python:3.12 AS base

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/tutina

RUN set -x &&                                \
    apt-get update && apt-get -y upgrade &&  \
    pip install wheel

FROM base AS builder

RUN set -x &&                                     \
    pip install pipx &&                           \
    pipx install poetry==2.0.0 &&                 \
    mkdir -p ./tutina-lib/tutina/lib &&           \
    touch ./tutina-lib/tutina/lib/__init__.py &&  \
    mkdir -p ./tutina-ai/tutina/lib &&            \
    touch ./tutina-ai/tutina/lib/__init__.py

COPY ./tutina-lib/pyproject.toml ./tutina-lib/poetry.lock ./tutina-lib/README.md ./tutina-lib/
COPY ./tutina-ai/pyproject.toml ./tutina-ai/poetry.lock ./tutina-ai/README.md ./tutina-ai/
COPY ./tutina-app/pyproject.toml ./tutina-app/poetry.lock ./tutina-app/README.md ./tutina-app/

RUN set -x &&                                                      \
    cd ./tutina-app/ &&                                            \
    /root/.local/bin/poetry config virtualenvs.in-project true &&  \
    /root/.local/bin/poetry install --only=main --no-root

COPY ./tutina-app ./tutina-app

RUN set -x &&                       \
    cd ./tutina-app/ &&             \
    /root/.local/bin/poetry build

FROM base

COPY ./tutina-lib ./tutina-lib
COPY ./tutina-ai ./tutina-ai

COPY --from=builder /usr/src/tutina/tutina-app/.venv ./tutina-app/.venv
COPY --from=builder /usr/src/tutina/tutina-app/dist ./tutina-app/dist

RUN set -x &&                     \
    cd ./tutina-app/ &&           \
    ./.venv/bin/pip install ./dist/*.whl

ENTRYPOINT ["/usr/src/tutina/tutina-app/.venv/bin/python"]
CMD ["-m", "uvicorn", "tutina.app:app", "--host=0.0.0.0", "--port=80"]
