{% macro _path(layer_env, entity) -%}
s3://{{ env_var("BUCKET") }}/{{ env_var(layer_env) }}/{{ entity }}/year={{ var("year") }}/month={{ "%02d" | format(var("month")) }}/day={{ "%02d" | format(var("day")) }}
{%- endmacro %}

{% macro bronze_path(entity) -%}
    '{{ _path("BRONZE_PATH", entity) }}/*.parquet'
{%- endmacro %}

{% macro silver_path(entity) -%}
    '{{ _path("SILVER_PATH", entity) }}_*.parquet'
{%- endmacro %}

{% macro silver_location(entity) -%}
    {{ _path("SILVER_PATH", entity) }}_{{ var("year") }}{{ "%02d" | format(var("month")) }}{{ "%02d" | format(var("day")) }}.parquet
{%- endmacro %}