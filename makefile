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