# Data Pipeline: Web Scraping → Lakehouse (MinIO + Trino)

## Overview

This project implements a simple lakehouse pipeline:

**Scraper → Bronze → Silver → Gold → Query**

* Orchestrated with Apache Airflow
* Storage powered by MinIO (object storage)
* Query layer via Trino