# Cline Rules

## Purpose

Define concise rules for building and maintaining the data pipeline:
**Scraper → Bronze → Silver → Gold → Trino (via Airflow)**

---

## General Principles

* Keep everything **simple, modular, and reproducible**
* Prefer **small, testable steps** over complex jobs
* All transformations must be **idempotent**

---

## Data Layer Rules

### Bronze

* Store **raw, immutable data**
* No transformations except minimal metadata (timestamp, source)
* Format: JSON / NDJSON / raw HTML
* Never overwrite data

### Silver

* Apply **cleaning and normalization**
* Enforce **schema consistency**
* Handle:

  * nulls
  * type casting
  * deduplication
* Output format: **Parquet**

### Gold

* Create **business-ready datasets**
* Perform:

  * joins
  * aggregations
  * derived metrics
* Optimize for querying (partitioning, column pruning)

---

## Storage (MinIO)

* Use **clear folder structure**:

  * `/bronze/{source}/{date}/`
  * `/silver/{domain}/{table}/`
  * `/gold/{domain}/{dataset}/`
* Use **partitioning by date** whenever possible
* Avoid small files (batch writes)

---

## Airflow Rules

* One DAG per pipeline/domain
* Tasks must be:

  * deterministic
  * retry-safe
* Use clear task naming:

  * `scrape_*`
  * `bronze_*`
  * `silver_*`
  * `gold_*`
* No heavy logic inside DAG files (delegate to scripts)

---

## Processing Rules

* Prefer **set-based transformations** (DuckDB / SQL)
* Avoid row-by-row processing
* Keep transformations **stateless**

---

## Schema & Evolution

* Schema changes must be:

  * backward-compatible when possible
  * versioned if breaking
* Validate schema at Silver layer

---

## Query Layer (Trino)

* Only query **Gold datasets**
* Never query Bronze directly
* Ensure tables are:

  * partitioned
  * documented

---

## Code Standards

* Use clear, descriptive naming
* Separate:

  * scraping
  * transformation
  * orchestration
* Add minimal but meaningful logging

---

## Anti-Patterns (Avoid)

* Writing directly to Gold from scraper
* Mutating Bronze data
* Embedding business logic in Airflow DAGs
* Using relational DB as raw storage

---
