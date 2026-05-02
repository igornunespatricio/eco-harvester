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

restart-volumes: down-no-volumes start