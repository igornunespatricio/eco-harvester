- use dbt for silver and gold layer transformations
- need to create column ingested_at in scraper data after transforming to pandas so it can be used by dbt to get latest record per id for deduplication 

- build gold layer

- create layer environment variables and use them in the bucket: create BRONZE, SILVER and GOLD environment variables
- create logger utility function or class
- implement parameters in pipeline dag to optionally run scraper, transformation and gold, running all by default


- remember the bandar report link is https://libgeo.univali.br/bandar/report
![alt text](assets/image.png)


- difference between triger and data interval timetables https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/timetable.html#differences-between-trigger-and-data-interval-timetables