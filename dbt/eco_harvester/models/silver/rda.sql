{{ config(materialized='view') }}

SELECT *
FROM read_parquet({{ bronze_path('rda') }})