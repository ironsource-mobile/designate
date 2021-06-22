FROM python:3.9-slim

RUN pip install -q poetry

WORKDIR /usr/src/designate

COPY . /usr/src/designate/
RUN poetry build -f wheel && pip install -q dist/designate-*.whl

ENTRYPOINT ["/usr/local/bin/designate"]
