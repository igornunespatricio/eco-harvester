- change the path in scraper/main.py to save the files inside a folder in the raw bucket instead of directly in the bucket (prefix the files with the form argument)
- remove the bunch of 0's from the datetime from filename
- add dags or tasks (decide what is better) for forms RDA, FIC, PLN, etc.
- backfill to get past date records (decide start and end dates)
- find lag time for records to be available in website

- remember the bandar report link is https://libgeo.univali.br/bandar/report