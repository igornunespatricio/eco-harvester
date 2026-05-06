from airflow.sdk import DAG, task, Param, get_current_context
import logging

with DAG(
    "params_tutorial_dag",
    params={"x": Param(5, type="integer", minimum=3), "my_int_param": 6},
) as dag:

    @task.python
    def example_task():
        ctx = get_current_context()
        logger = logging.getLogger("airflow.task")
        # This will print the default value, 6:
        logger.info(ctx["dag"].params["my_int_param"])
        # This will print the manually-provided value, 42:
        logger.info(ctx["params"]["my_int_param"])
        # This will print the default value, 5, since it wasn't provided manually:
        logger.info(ctx["params"]["x"])

    example_task()
