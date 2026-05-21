FROM python:3.12-slim

WORKDIR /app

RUN pip install dbt-core dbt-duckdb

COPY dbt/ .

CMD ["sleep", "infinity"]