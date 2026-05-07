- add all forms: RDA, FIC, PLN, etc.
- backfill to get past date records (decide start and end dates)
- pass timeout for bandar request as parameter in dag with default for 2 minutes (test other times)
- correct warning  The `airflow.models.param.Param` attribute is deprecated. Please use `'airflow.sdk.Param'`

- remember the bandar report link is https://libgeo.univali.br/bandar/report
![alt text](assets/image.png)


- difference between triger and data interval timetables https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/timetable.html#differences-between-trigger-and-data-interval-timetables