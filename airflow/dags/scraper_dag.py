from airflow.providers.docker.operators.docker import DockerOperator
from airflow.sdk import dag
import pendulum


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
        auto_remove="success",
        network_mode="eco-harvester-network",
        mount_tmp_dir=False,
    )


scraper()
