{{ config(
    materialized='external',
    location=silver_location('ra')
) }}

SELECT *
FROM read_parquet({{ bronze_path('ra') }})