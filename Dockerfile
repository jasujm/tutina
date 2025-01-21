# Dockerfile for the Tutina HA addon
# Needs to be called just Dockerfile because of the HA addon build system

FROM homeassistant/aarch64-base-debian:bookworm AS base

ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/tutina

RUN set -x &&                                             \
    apt-get -y update &&                                  \
    apt-get install -y python3 python3-wheel python3-pip

FROM base AS builder

RUN set -ex &&                                 \
    apt-get install -y pipx &&                 \
    pipx install poetry==2.0.0 &&              \
    mkdir -p ./tutina-lib/tutina/lib &&        \
    touch ./tutina-lib/tutina/lib/__init__.py

COPY ./tutina-lib/pyproject.toml ./tutina-lib/poetry.lock ./tutina-lib/README.md ./tutina-lib/
COPY ./tutina-ha/pyproject.toml ./tutina-ha/poetry.lock ./tutina-ha/README.md ./tutina-ha/

RUN set -x &&                                                      \
    cd ./tutina-ha/ &&                                             \
    /root/.local/bin/poetry config virtualenvs.in-project true &&  \
    /root/.local/bin/poetry install --only=main --no-root

COPY ./tutina-ha ./tutina-ha

RUN set -x &&                      \
    cd ./tutina-ha/ &&             \
    /root/.local/bin/poetry build

FROM base

COPY ./tutina-lib ./tutina-lib

COPY --from=builder /usr/src/tutina/tutina-ha/.venv ./tutina-ha/.venv
COPY --from=builder /usr/src/tutina/tutina-ha/dist ./tutina-ha/dist

RUN set -x && \
    apt-get install -y pkg-config libmariadb-dev && \
    cd ./tutina-ha && \
    ./.venv/bin/pip install ./dist/*.whl

COPY ./tutina-ha/run.sh /usr/bin/run.sh
RUN chmod a+x /usr/bin/run.sh

CMD [ "/usr/bin/run.sh" ]
