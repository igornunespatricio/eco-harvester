SHELL := /bin/bash
DOTENV := ../../.env

dbt-run:
	set -a && source $(DOTENV) && set +a && dbt run --profiles-dir . $(ARGS)

dbt-test:
	set -a && source $(DOTENV) && set +a && dbt test --profiles-dir . $(ARGS)

dbt-debug:
	set -a && source $(DOTENV) && set +a && dbt debug --profiles-dir .

dbt-run-date:
	set -a && source $(DOTENV) && set +a && dbt run --profiles-dir . --select $(MODEL) --vars '{"year": $(YEAR), "month": $(MONTH), "day": $(DAY)}'