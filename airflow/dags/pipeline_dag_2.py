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
from airflow.operators.python import ShortCircuitOperator
import pendulum
from cosmos import (
    DbtTaskGroup,
    ProjectConfig,
    ExecutionConfig,
    RenderConfig,
    ProfileConfig,
)
from cosmos.constants import ExecutionMode, LoadMode
from utils.storage_client import MinioS3Client

# ---------------------------------------------------------------------------
# Environment / config
# ---------------------------------------------------------------------------

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "")
BUCKET = os.getenv("BUCKET", "")

DOCKER_ENV = {
    "MINIO_ENDPOINT": MINIO_ENDPOINT,
    "MINIO_ROOT_USER": MINIO_ROOT_USER,
    "MINIO_ROOT_PASSWORD": MINIO_ROOT_PASSWORD,
    "BUCKET": os.getenv("BUCKET", ""),
    "BRONZE_PATH": os.getenv("BRONZE_PATH", ""),
    "SILVER_PATH": os.getenv("SILVER_PATH", ""),
    "GOLD_PATH": os.getenv("GOLD_PATH", ""),
    "DBT_PROFILES_DIR": "/app",
}

NETWORK = "eco-harvester-network"

DBT_PROJECT_PATH = "/opt/airflow/dbt/eco_harvester"

# ---------------------------------------------------------------------------
# Entities processed by each layer
# ---------------------------------------------------------------------------

FORMS = [
    "RA",
    "RDA",
]
SILVER_ENTITIES = [
    "RA",
    "RDA",
]

GOLD_MARTS = [
    "mart_detections",
    "mart_shutdowns",
    "mart_project_summary",
]


# ---------------------------------------------------------------------------
# Helper: build a DockerOperator
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
# Minio client
# ---------------------------------------------------------------------------
minio_client = MinioS3Client(
    endpoint=MINIO_ENDPOINT,
    access_key=MINIO_ROOT_USER,
    secret_key=MINIO_ROOT_PASSWORD,
)


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------


@dag(
    dag_id="pipeline_bronze_silver_gold_2",
    schedule="@daily",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    end_date=pendulum.datetime(2025, 1, 2, tz="UTC"),
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
    # Sentinel tasks
    # -----------------------------------------------------------------------

    start = EmptyOperator(task_id="start_pipeline")

    end = EmptyOperator(
        task_id="end_pipeline",
        trigger_rule="all_done",
    )

    # -----------------------------------------------------------------------
    # BRONZE — raw ingestion, one task per source, all in parallel
    # -----------------------------------------------------------------------

    with TaskGroup("bronze") as bronze_group:
        for form in FORMS:
            EmptyOperator(task_id=f"scrape_{form.lower()}")

    bronze_done = EmptyOperator(task_id="bronze_completed")

    # -----------------------------------------------------------------------
    # SILVER — clean / validate / enforce schema, one task per entity
    # -----------------------------------------------------------------------

    with TaskGroup("silver") as silver_group:
        dbt_group = DbtTaskGroup(
            group_id="dbt_transforms",
            project_config=ProjectConfig(dbt_project_path=DBT_PROJECT_PATH),
            profile_config=ProfileConfig(
                profile_name="eco_harvester",
                target_name="dev",
                profiles_yml_filepath="/opt/airflow/dbt/eco_harvester/profiles.yml",
            ),
            execution_config=ExecutionConfig(
                execution_mode=ExecutionMode.DOCKER,
                dbt_executable_path="dbt",
            ),
            render_config=RenderConfig(
                load_method=LoadMode.DBT_LS,
                select=["ra", "rda"],
            ),
            operator_args={
                "image": "dbt:latest",
                "network_mode": NETWORK,
                "environment": DOCKER_ENV,
                "auto_remove": "success",
                "mount_tmp_dir": False,
                "vars": "{ year: {{ ds[:4] }}, month: {{ ds[5:7] }}, day: {{ ds[8:10] }} }",
            },
        )

        check_tasks = []  # collect references

        for form in FORMS:
            check = ShortCircuitOperator(
                task_id=f"check_{form.lower()}_partition",
                python_callable=minio_client.partition_has_files,
                op_kwargs={
                    "bucket_name": BUCKET,
                    "partition_prefix": "{{ 'bronze/"
                    + form.lower()
                    + "/year=' ~ ds[:4] ~ '/month=' ~ ds[5:7] ~ '/day=' ~ ds[8:10] ~ '/' }}",
                },
                ignore_downstream_trigger_rules=True,
            )
            check_tasks.append(check)  # store reference

            task_key = f"silver.dbt_transforms.{form.lower()}_run"
            dbt_task = dbt_group.children.get(task_key)
            check >> dbt_task

    # Sentinel: wired directly to dbt tasks, bypassing TaskGroup boundary
    # so that a skipped form does not propagate skip to silver_completed
    silver_done = EmptyOperator(
        task_id="silver_completed",
        trigger_rule="all_done",
    )

    # -----------------------------------------------------------------------
    # GOLD — aggregations / marts / ML features, one task per mart
    # -----------------------------------------------------------------------

    with TaskGroup("gold") as gold_group:
        for mart in GOLD_MARTS:
            EmptyOperator(
                task_id=f"build_{mart}",
                trigger_rule="all_done",
            )

    # Wire the pipeline
    start >> bronze_group >> bronze_done >> silver_group

    # Wire check tasks directly to silver_done — they live outside dbt_transforms
    # TaskGroup so skip state won't propagate through a nested group boundary
    for check in check_tasks:
        check >> silver_done

    silver_done >> gold_group >> end


pipeline_bronze_silver_gold()
