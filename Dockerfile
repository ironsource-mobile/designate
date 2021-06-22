FROM python:3.9-slim as builder

RUN pip install -q poetry

WORKDIR /usr/src/designate

COPY . /usr/src/designate/
RUN poetry install --no-dev

ENTRYPOINT ["designate"]
