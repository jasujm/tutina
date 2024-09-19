FROM homeassistant/aarch64-base-debian:bookworm AS base

RUN apt-get update && apt-get install -y python3 python3-pip python3-wheel

WORKDIR /usr/src/tutina

FROM base AS builder
RUN apt-get install -y pipx && pipx install poetry==1.8.3
COPY pyproject.toml poetry.lock ./
RUN /root/.local/bin/poetry export > requirements.txt

FROM base
RUN apt-get update && apt-get install -y python3-venv pkg-config libmariadb-dev
COPY --from=builder /usr/src/tutina/requirements.txt .
RUN python3 -m venv /usr/src/tutina/venv && \
    /usr/src/tutina/venv/bin/pip3 install -r requirements.txt
COPY . ./
RUN chmod a+x /usr/src/tutina/run.sh

CMD [ "/usr/src/tutina/run.sh" ]
