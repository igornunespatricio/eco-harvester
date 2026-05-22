FROM python:3.12-slim

WORKDIR /app

COPY dbt/requirements.txt .
RUN pip install -r requirements.txt

COPY dbt/ .

CMD ["sleep", "infinity"]