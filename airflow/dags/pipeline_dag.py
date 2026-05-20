"""
Boilerplate DAG: Bronze → Silver → Gold pipeline.

Layers:
  - Bronze : raw ingestion (scraping, API pulls, file drops)
  - Silver : cleaning, validation, schema enforcement
  - Gold   : aggregation, business logic, mart/feature creation

Replace every DockerOperator with whatever fits your stack
(PythonOperator, BashOperator, SparkSubmitOperator, etc.).
"""

from __future__ import annotations

import os
from airflow.sdk import dag, Param, TaskGroup
from airflow.providers.standard.operators.empty import EmptyOperator
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.timetables.interval import CronDataIntervalTimetable
import pendulum

# ---------------------------------------------------------------------------
# Environment / config
# ---------------------------------------------------------------------------

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "")

DOCKER_ENV = {
    "MINIO_ENDPOINT": MINIO_ENDPOINT,
    "MINIO_ACCESS_KEY": MINIO_ACCESS_KEY,
    "MINIO_SECRET_KEY": MINIO_SECRET_KEY,
}

NETWORK = "eco-harvester-network"

# ---------------------------------------------------------------------------
# Entities processed by each layer
# ---------------------------------------------------------------------------

FORMS = [
    "RA",
    "RDA",
]  # no data or sparse for these: "FIC", "PLN", "REG", "NEC", "ESF", "REAB", "REPRO", "RSOL"]
SILVER_ENTITIES = [
    "RA",
    "RDA",
]  # one transform per form

GOLD_MARTS = [
    "mart_detections",
    "mart_shutdowns",
    "mart_project_summary",
]


# ---------------------------------------------------------------------------
# Helper: build a DockerOperator (swap for any operator you need)
# ---------------------------------------------------------------------------


def _docker_task(
    task_id: str,
    image: str,
    command: str,
    **kwargs,
) -> DockerOperator:
    return DockerOperator(
        task_id=task_id,
        image=image,
        command=command,
        auto_remove="success",
        network_mode=NETWORK,
        environment=DOCKER_ENV,
        mount_tmp_dir=False,
        **kwargs,
    )


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------


@dag(
    dag_id="pipeline_bronze_silver_gold",
    schedule="@daily",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    end_date=pendulum.datetime(2025, 1, 31, tz="UTC"),
    catchup=True,
    tags=["orchestrator", "bronze", "silver", "gold"],
    is_paused_upon_creation=True,
    doc_md=__doc__,
    params={
        "per": Param(
            default=2500,
            enum=[50, 100, 250, 500, 1000, 2000, 2500],
            type="integer",
            description="Maximum number of items to ingest per source per run",
        ),
        "timeout": Param(
            default=300,
            type="integer",
            description="Timeout in seconds for each Docker task",
        ),
        "dry_run": Param(
            default=False,
            type="boolean",
            description="If true, tasks run in dry-run mode (no writes)",
        ),
        "run_scraper": Param(
            default=True,
            type="boolean",
            description="Whether to run the scraper tasks in the bronze layer",
        ),
        "run_transformation": Param(
            default=True,
            type="boolean",
            description="Whether to run the transformation tasks in the silver layer",
        ),
        "run_aggregation": Param(
            default=True,
            type="boolean",
            description="Whether to run the aggregation tasks in the gold layer",
        ),
    },
)
def pipeline_bronze_silver_gold():

    # -----------------------------------------------------------------------
    # Sentinel tasks — give the graph clear entry / exit points and are
    # ideal hooks for notifications, sensors, or data-quality gates later.
    # -----------------------------------------------------------------------

    start = EmptyOperator(task_id="start_pipeline")
    end = EmptyOperator(task_id="end_pipeline")

    # -----------------------------------------------------------------------
    # BRONZE — raw ingestion, one task per source, all in parallel
    # -----------------------------------------------------------------------

    with TaskGroup("bronze") as bronze_group:
        for form in FORMS:
            _docker_task(
                task_id=f"scrape_{form.lower()}",
                image="scraper:latest",
                command=(
                    "python scraper/main.py"
                    " --date '{{ ds }}'"
                    " --animals 'all_records'"
                    " --basins  'all_records'"
                    f" --form    '{form}'"
                    " --per     '{{ params.per }}'"
                    " --timeout '{{ params.timeout }}'"
                ),
            )
            # EmptyOperator(task_id=f"scrape_{form.lower()}")

    # Sentinel: all bronze tasks must finish before silver starts
    bronze_done = EmptyOperator(task_id="bronze_completed")

    # -----------------------------------------------------------------------
    # SILVER — clean / validate / enforce schema, one task per entity
    # -----------------------------------------------------------------------

    with TaskGroup("silver") as silver_group:
        for entity in SILVER_ENTITIES:
            _docker_task(
                task_id=f"transform_{entity}",
                image="transform:latest",  # replace with image
                command=(
                    "python transform/main.py"
                    f" --entity  '{entity}'"
                    " --date '{{ ds }}'"
                    " --dry-run        '{{ params.dry_run }}'"
                ),
            )
            # EmptyOperator(task_id=f"transform_{entity}")

    # Sentinel: all silver tasks must finish before gold starts
    silver_done = EmptyOperator(task_id="silver_completed")

    # -----------------------------------------------------------------------
    # GOLD — aggregations / marts / ML features, one task per mart
    # -----------------------------------------------------------------------

    with TaskGroup("gold") as gold_group:
        for mart in GOLD_MARTS:
            # _docker_task(
            #     task_id=f"build_{mart}",
            #     image="aggregator:latest",  # replace with image
            #     command=(
            #         "python aggregator/main.py"
            #         f" --mart    '{mart}'"
            #         " --interval-start '{{ data_interval_start }}'"
            #         " --interval-end   '{{ data_interval_end }}'"
            #         " --dry-run        '{{ params.dry_run }}'"
            #     ),
            # )
            EmptyOperator(task_id=f"build_{mart}")

    # -----------------------------------------------------------------------
    # Wire the pipeline
    #
    #   start
    #     └─► [bronze.*]  (parallel)
    #               └─► bronze_done
    #                       └─► [silver.*]  (parallel)
    #                                 └─► silver_done
    #                                         └─► [gold.*]  (parallel)
    #                                                   └─► end
    # -----------------------------------------------------------------------

    (
        start
        >> bronze_group
        >> bronze_done
        >> silver_group
        >> silver_done
        >> gold_group
        >> end
    )


pipeline_bronze_silver_gold()
