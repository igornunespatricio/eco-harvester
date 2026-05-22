# Build scraper image
build-scraper:
	docker compose build scraper

# Build scraper image with no cache
build-scraper-nocache:
	docker compose build scraper --no-cache

# Start scraper container
scraper: build-scraper
	docker compose up -d scraper

# Start scraper container with fresh build
scraper-fresh: build-scraper-nocache
	docker compose up -d scraper

# Stop scraper container
stop-scraper:
	docker compose stop scraper

# Remove scraper container
clean-scraper:
	docker compose down scraper -v

# View scraper logs
logs-scraper:
	docker compose logs -f scraper

# Show scraper status
status:
	docker compose ps

build-minio:
	docker compose build minio

build-minio-nocache:
	docker compose build minio --no-cache

minio: build-minio
	docker compose up -d minio

stop-minio:
	docker compose stop minio

clean-minio:
	docker compose down minio -v

# Build dbt image
build-dbt:
	docker compose build dbt

# Build dbt image with no cache
build-dbt-nocache:
	docker compose build dbt --no-cache

# Start dbt container
dbt: build-dbt
	docker compose up -d dbt

# Start dbt container with fresh build
dbt-fresh: build-dbt-nocache
	docker compose up -d dbt

# Stop dbt container
stop-dbt:
	docker compose stop dbt

# Remove dbt container
clean-dbt:
	docker compose down dbt -v

# View dbt logs
logs-dbt:
	docker compose logs -f dbt

build-airflow:
	docker compose build airflow-worker airflow-scheduler airflow-apiserver

build-airflow-nocache:
	docker compose build airflow-worker airflow-scheduler airflow-apiserver --no-cache

# start all containers
start-no-cache:
	docker compose build --no-cache
	docker compose up -d

start:
	docker compose build
	docker compose up -d

# down all containers
down:
	docker compose down

down-volumes:
	docker compose down -v

# remove orphan containers
down-orphans:
	docker compose down --remove-orphans
	
#restart all containers
restart: down start

restart-no-cache: down start-no-cache

restart-volumes: down-volumes start