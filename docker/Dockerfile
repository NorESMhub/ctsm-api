FROM python:3.10-bullseye

RUN apt update && apt upgrade -y
RUN apt install -u sudo

RUN pip install --upgrade pip setuptools
RUN pip install poetry
RUN poetry config virtualenvs.create false

COPY ./pyproject.toml /ctsm-api/pyproject.toml
COPY ./poetry.lock /ctsm-api/poetry.lock

WORKDIR /ctsm-api

RUN poetry install

COPY docker/entrypoint.sh /ctsm-api/docker/entrypoint.sh

RUN chmod +x /ctsm-api/docker/entrypoint.sh

EXPOSE 8000

CMD ["/ctsm-api/docker/entrypoint.sh"]
