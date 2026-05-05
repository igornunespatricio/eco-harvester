from airflow.providers.docker.operators.docker import DockerOperator
from airflow.timetables.interval import CronDataIntervalTimetable

from airflow.sdk import dag
import os

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "")

FORMS = ["RA", "RDA", "FIC", "PLN"]


def make_scraper_dag(form: str):
    @dag(
        dag_id=f"scraper_{form.lower()}",
        schedule=CronDataIntervalTimetable("@monthly", timezone="UTC"),
        catchup=False,
        tags=["scraper", form.lower()],
        is_paused_upon_creation=True,
    )
    def scraper():
        """
        ### Scraper DAG
        This DAG uses the DockerOperator to run the scraper container.
        """
        run = DockerOperator(
            task_id="run_scraper",
            image="scraper:latest",
            command=(
                "python scraper/main.py"
                " --interval-start '{{ data_interval_start }}'"
                " --interval-end '{{ data_interval_end }}'"
                " --animals 'all_records'"
                " --basins 'all_records'"
                f" --form '{form}'"
            ),
            auto_remove="success",
            network_mode="eco-harvester-network",
            environment={
                "MINIO_ENDPOINT": MINIO_ENDPOINT,
                "MINIO_ACCESS_KEY": MINIO_ACCESS_KEY,
                "MINIO_SECRET_KEY": MINIO_SECRET_KEY,
            },
            mount_tmp_dir=False,
        )
        return run

    return scraper


for form in FORMS:
    globals()[f"scraper_{form.lower()}"] = make_scraper_dag(form)()
