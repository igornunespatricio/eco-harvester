from airflow.providers.docker.operators.docker import DockerOperator
from airflow.sdk import dag
import pendulum
import os

# MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
# MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
# MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "")


@dag(
    schedule=None,
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["example"],
)
def scraper():
    """
    ### Scraper DAG
    This DAG uses the DockerOperator to run the scraper container.
    """

    DockerOperator(
        task_id="run_scraper",
        image="scraper:latest",
        command="python scraper/src/bandar_scraper.py",
        auto_remove="success",
        network_mode="eco-harvester-network",
        environment={
            "MINIO_ENDPOINT": MINIO_ENDPOINT,
            "MINIO_ACCESS_KEY": MINIO_ACCESS_KEY,
            "MINIO_SECRET_KEY": MINIO_SECRET_KEY,
        },
        mount_tmp_dir=False,
    )


scraper()
