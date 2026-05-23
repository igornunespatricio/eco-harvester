FROM python:3.12-slim

WORKDIR /app

COPY dbt/requirements.txt .
RUN pip install -r requirements.txt

# Copy project contents directly into /app, not into /app/eco_harvester/
COPY dbt/eco_harvester/ .

CMD ["sleep", "infinity"]