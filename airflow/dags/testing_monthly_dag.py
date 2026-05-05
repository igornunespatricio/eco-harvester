from airflow.sdk import dag, task, get_current_context
import pendulum

from airflow.timetables.interval import CronDataIntervalTimetable


@dag(
    dag_id="sample_monthly_dag",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    schedule=CronDataIntervalTimetable("@monthly", timezone="UTC"),
    catchup=False,
    tags=["sample", "monthly"],
)
# @dag(
#     dag_id="sample_monthly_dag",
#     start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
#     schedule="@monthly",
#     catchup=False,
#     tags=["sample", "monthly"],
# )
def sample_monthly_dag():

    @task
    def print_interval_info():
        context = get_current_context()
        data_interval_start = context["data_interval_start"]
        data_interval_end = context["data_interval_end"]
        logical_date = context["logical_date"]
        print(f"Data Interval Start : {data_interval_start}")
        print(f"Data Interval End   : {data_interval_end}")
        print(f"Logical Date        : {logical_date}")

    print_interval_info()


sample_monthly_dag()


# @task
# def print_interval_info(data_interval_start=None, data_interval_end=None, logical_date=None):
#     print(f"Data Interval Start : {data_interval_start}")
#     print(f"Data Interval End   : {data_interval_end}")
#     print(f"Logical Date        : {logical_date}")

# print_interval_info(
#     data_interval_start="{{ data_interval_start }}",
#     data_interval_end="{{ data_interval_end }}",
#     logical_date="{{ logical_date }}",
# )

# @task
# def print_interval_info(**context):
#     print(f"Data Interval Start : {context['data_interval_start']}")
#     print(f"Data Interval End   : {context['data_interval_end']}")
#     print(f"Logical Date        : {context['logical_date']}")
