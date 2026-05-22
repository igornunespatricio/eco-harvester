SHELL := /bin/bash
DOTENV := ../../.env

dbt-run:
	set -a && source $(DOTENV) && set +a && dbt run --profiles-dir . $(ARGS)

dbt-test:
	set -a && source $(DOTENV) && set +a && dbt test --profiles-dir . $(ARGS)

dbt-debug:
	set -a && source $(DOTENV) && set +a && dbt debug --profiles-dir .