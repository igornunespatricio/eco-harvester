{{ config(
    materialized='external',
    location=silver_location('rda')
) }}

SELECT *
FROM read_parquet({{ bronze_path('rda') }})