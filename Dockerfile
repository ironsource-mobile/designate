FROM python:3.9-slim as builder

RUN pip install -q poetry

WORKDIR /usr/src/designate

COPY . /usr/src/designate/
RUN poetry build -f wheel


FROM python:3.9-slim as production

COPY --from=builder /usr/src/designate/dist/designate-*.whl /usr/src/designate/
RUN pip install -q /usr/src/designate/designate-*.whl && rm -f /usr/src/designate/designate-*.whl

CMD ["/bin/bash"]
