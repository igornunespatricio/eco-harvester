- rebuild silver transformation to partition by year and month of event date and deduplicate based on latest uploaded file in bronze year/month/day, continue in transform/main.py and test in pipeline dag

- create buckets environment variables and use them across the files
- create logger utility function or class

- remember the bandar report link is https://libgeo.univali.br/bandar/report
![alt text](assets/image.png)


- difference between triger and data interval timetables https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/timetable.html#differences-between-trigger-and-data-interval-timetables