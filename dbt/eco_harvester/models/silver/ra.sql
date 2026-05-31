{{ config(
    materialized='external',
    location=silver_location('ra')
) }}

WITH renamed AS (
    SELECT
        "Numero_processo"                                                        AS process_number,
        "Nome_processo"                                                          AS process_name,
        "Data de início (Primeira emissão sonora)"                               AS first_seismic_shot_date_raw,
        "Data de término (Última emissão sonora)"                                AS last_seismic_shot_date_raw,
        "Situação do Projeto"                                                    AS project_status,
        "numero da deteccao"                                                     AS ra_number,
        "eda"                                                                    AS eda,
        "observador responsavel / 1 / ctf"                                       AS observer_1_ctf,
        "observador responsavel / 2 / ctf"                                       AS observer_2_ctf,
        "observador responsavel / 3 / ctf"                                       AS observer_3_ctf,
        "usuario observador responsavel / 1 / ctf"                               AS user_observer_1_ctf,
        "usuario observador responsavel / 2 / ctf"                               AS user_observer_2_ctf,
        "usuario observador responsavel / 3 / ctf"                               AS user_observer_3_ctf,
        "data do evento"                                                         AS event_date_raw,
        "hora inicio da avistagem"                                               AS sighting_start_time_raw,
        "hora final da avistagem"                                                AS sighting_end_time_raw,
        "hora entrada na area de exclusao"                                       AS exclusion_zone_entry_time_raw,
        "navio / nome"                                                           AS vessel_name,
        "direcao do navio"                                                       AS vessel_heading_deg,
        "estado do mar"                                                          AS sea_state,
        "visibilidade"                                                           AS visibility,
        "reflexo"                                                                AS glare,
        "vento"                                                                  AS wind_speed_knots,
        "ondulacao do mar"                                                       AS swell,
        "coordenada / 1 / latitude"                                              AS coord_1_lat,
        "coordenada / 1 / longitude"                                             AS coord_1_lon,
        "coordenada / 1 / profundidade"                                          AS coord_1_depth_m,
        "coordenada / 2 / latitude"                                              AS coord_2_lat,
        "coordenada / 2 / longitude"                                             AS coord_2_lon,
        "coordenada / 2 / profundidade"                                          AS coord_2_depth_m,
        "coordenada / 3 / latitude"                                              AS coord_3_lat,
        "coordenada / 3 / longitude"                                             AS coord_3_lon,
        "coordenada / 3 / profundidade"                                          AS coord_3_depth_m,
        "observacao / identificacao da avistagem / identificacao"                AS species_identification,
        "observacao / confianca da identificacao"                                AS identification_confidence,
        "observacao / descricao da confianca da identificacao"                   AS identification_confidence_description,
        "observacao / grupo"                                                     AS group_observation,
        "observacao / quantidade de adultos"                                     AS adult_count,
        "observacao / quantidade de filhotes"                                    AS calf_count,
        "observacao / comportamento"                                             AS behaviour,
        "observacao / outro comportamento"                                       AS other_behaviour,
        "observacao / caracteristicas observadas"                                AS observed_characteristics,
        "observacao / outra caracteristica observada"                            AS other_observed_characteristic,
        "observacao / posicao do animal ou grupo / 1 / posicao"                 AS animal_position_1,
        "observacao / posicao do animal ou grupo / 1 / hora"                    AS animal_position_1_time_raw,
        "observacao / posicao do animal ou grupo / 1 / menor distancia"         AS animal_position_1_closest,
        "observacao / posicao do animal ou grupo / 1 / distancia"               AS animal_position_1_distance_m,
        "observacao / posicao do animal ou grupo / 2 / posicao"                 AS animal_position_2,
        "observacao / posicao do animal ou grupo / 2 / hora"                    AS animal_position_2_time_raw,
        "observacao / posicao do animal ou grupo / 2 / menor distancia"         AS animal_position_2_closest,
        "observacao / posicao do animal ou grupo / 2 / distancia"               AS animal_position_2_distance_m,
        "observacao / posicao do animal ou grupo / 3 / posicao"                 AS animal_position_3,
        "observacao / posicao do animal ou grupo / 3 / hora"                    AS animal_position_3_time_raw,
        "observacao / posicao do animal ou grupo / 3 / menor distancia"         AS animal_position_3_closest,
        "observacao / posicao do animal ou grupo / 3 / distancia"               AS animal_position_3_distance_m,
        "canhoes de ar / estado da fonte sismica"                                AS seismic_source_status,
        "canhoes de ar / acao realizada"                                         AS action_taken,
        "canhoes de ar / desligamento solicitado"                                AS shutdown_requested,
        "canhoes de ar / hora da solicitacao"                                    AS shutdown_request_time_raw,
        "canhoes de ar / desligamento realizado"                                 AS shutdown_performed,
        "canhoes de ar / hora do desligamento"                                   AS shutdown_time_raw,
        "canhoes de ar / tempo total de interrupcao da atividade"                AS total_activity_interruption_min,
        "canhoes de ar / volume da fonte sismica"                                AS seismic_source_volume_cui,
        "canhoes de ar / hora de menor distancia"                                AS closest_approach_time_raw,
        "canhoes de ar / menor distancia da fonte sismica"                       AS closest_approach_distance_m,
        "map"                                                                    AS map_status,
        "status do registro"                                                     AS record_status,
        "observacoes gerais"                                                     AS general_notes,
        "ingested_at"                                                            AS ingested_at
    FROM read_parquet({{ bronze_path('ra') }})
),

-- ── Step 1: deduplicate — keep the most recently ingested record per RA ──────
deduped AS (
    SELECT * EXCLUDE (rn)
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (PARTITION BY ra_number ORDER BY ingested_at DESC) AS rn
        FROM renamed
    )
    WHERE rn = 1
),

-- ── Step 2: cast raw strings to proper types ──────────────────────────────────
casted AS (
    SELECT
        -- identifiers & descriptors
        process_number,
        process_name,
        project_status,
        ra_number,
        eda,
        vessel_name,
        seismic_source_status,
        action_taken,
        sea_state,
        visibility,
        glare,
        swell,
        species_identification,
        identification_confidence,
        identification_confidence_description,
        behaviour,
        other_behaviour,
        observed_characteristics,
        other_observed_characteristic,
        animal_position_1,
        animal_position_2,
        animal_position_3,
        map_status,
        record_status,
        general_notes,

        -- observer ids
        CAST(observer_1_ctf      AS INTEGER)                                     AS observer_1_ctf,
        CAST(observer_2_ctf      AS INTEGER)                                     AS observer_2_ctf,
        CAST(observer_3_ctf      AS INTEGER)                                     AS observer_3_ctf,
        CAST(user_observer_1_ctf AS INTEGER)                                     AS user_observer_1_ctf,
        CAST(user_observer_2_ctf AS INTEGER)                                     AS user_observer_2_ctf,
        CAST(user_observer_3_ctf AS INTEGER)                                     AS user_observer_3_ctf,

        -- project dates (DD/MM/YYYY → DATE)
        STRPTIME(first_seismic_shot_date_raw, '%d/%m/%Y')::DATE                  AS first_seismic_shot_date,
        STRPTIME(last_seismic_shot_date_raw,  '%d/%m/%Y')::DATE                  AS last_seismic_shot_date,

        -- event date
        STRPTIME(event_date_raw, '%d/%m/%Y')::DATE                               AS event_date,

        -- raw time strings cast to VARCHAR for timestamp assembly below
        -- (some arrive as DOUBLE/null from bronze; explicit cast prevents SPLIT_PART type errors)
        CAST(sighting_start_time_raw       AS VARCHAR)                           AS sighting_start_time_raw,
        CAST(sighting_end_time_raw         AS VARCHAR)                           AS sighting_end_time_raw,
        CAST(exclusion_zone_entry_time_raw AS VARCHAR)                           AS exclusion_zone_entry_time_raw,
        CAST(animal_position_1_time_raw    AS VARCHAR)                           AS animal_position_1_time_raw,
        CAST(animal_position_2_time_raw    AS VARCHAR)                           AS animal_position_2_time_raw,
        CAST(animal_position_3_time_raw    AS VARCHAR)                           AS animal_position_3_time_raw,
        CAST(shutdown_request_time_raw     AS VARCHAR)                           AS shutdown_request_time_raw,
        CAST(shutdown_time_raw             AS VARCHAR)                           AS shutdown_time_raw,
        CAST(closest_approach_time_raw     AS VARCHAR)                           AS closest_approach_time_raw,

        -- vessel
        CAST(vessel_heading_deg AS DOUBLE)                                       AS vessel_heading_deg,

        -- environmental (already numeric in bronze)
        CAST(wind_speed_knots AS INTEGER)                                        AS wind_speed_knots,

        -- coordinates & depths (already numeric in bronze)
        CAST(coord_1_lat     AS DOUBLE)                                          AS coord_1_lat,
        CAST(coord_1_lon     AS DOUBLE)                                          AS coord_1_lon,
        CAST(coord_1_depth_m AS INTEGER)                                         AS coord_1_depth_m,
        CAST(coord_2_lat     AS DOUBLE)                                          AS coord_2_lat,
        CAST(coord_2_lon     AS DOUBLE)                                          AS coord_2_lon,
        CAST(coord_2_depth_m AS INTEGER)                                         AS coord_2_depth_m,
        CAST(coord_3_lat     AS DOUBLE)                                          AS coord_3_lat,
        CAST(coord_3_lon     AS DOUBLE)                                          AS coord_3_lon,
        CAST(coord_3_depth_m AS INTEGER)                                         AS coord_3_depth_m,

        -- animal counts (already numeric in bronze)
        CAST(adult_count AS INTEGER)                                             AS adult_count,
        CAST(calf_count  AS INTEGER)                                             AS calf_count,

        -- boolean-like flags
        -- (cast to VARCHAR first: all-null batches cause DuckDB to infer DOUBLE, breaking string comparison)
        (CAST(group_observation AS VARCHAR) = 'Sim')                             AS group_observation,
        (CAST(shutdown_requested AS VARCHAR) = 'Sim')                            AS shutdown_requested,
        (CAST(shutdown_performed AS VARCHAR) = 'Sim')                            AS shutdown_performed,

        -- animal position closest flags (already bool in bronze)
        CAST(animal_position_1_closest AS BOOLEAN)                               AS animal_position_1_closest,
        CAST(animal_position_2_closest AS BOOLEAN)                               AS animal_position_2_closest,
        CAST(animal_position_3_closest AS BOOLEAN)                               AS animal_position_3_closest,

        -- animal position distances
        CAST(animal_position_1_distance_m AS INTEGER)                            AS animal_position_1_distance_m,
        CAST(animal_position_2_distance_m AS INTEGER)                            AS animal_position_2_distance_m,
        CAST(animal_position_3_distance_m AS INTEGER)                            AS animal_position_3_distance_m,

        -- shutdown & seismic
        -- total_activity_interruption_min is already numeric (float) in bronze, unlike RDA's HH:MM string
        CAST(total_activity_interruption_min AS DOUBLE)                          AS total_activity_interruption_min,
        CAST(seismic_source_volume_cui       AS INTEGER)                         AS seismic_source_volume_cui,
        CAST(closest_approach_distance_m     AS INTEGER)                         AS closest_approach_distance_m,

        ingested_at
    FROM deduped
),

-- ── Step 3: assemble timestamps, handling midnight crossings ──────────────────
--
-- Anchor: sighting_start_time_raw defines the base for midnight detection.
-- Any time column earlier than sighting_start_time_raw belongs to event_date + 1.
--
-- Exception — shutdown window: shutdown_ts compares against
-- shutdown_request_time_raw (not sighting start), since the relevant
-- window is request → performed.
--
timestamped AS (
    SELECT
        * EXCLUDE (
            sighting_start_time_raw,
            sighting_end_time_raw,
            exclusion_zone_entry_time_raw,
            animal_position_1_time_raw,
            animal_position_2_time_raw,
            animal_position_3_time_raw,
            shutdown_request_time_raw,
            shutdown_time_raw,
            closest_approach_time_raw
        ),

        -- sighting start: always anchored to event_date
        (
            event_date::TIMESTAMP
            + INTERVAL (
                CAST(SPLIT_PART(sighting_start_time_raw, ':', 1) AS INTEGER) * 60
                + CAST(SPLIT_PART(sighting_start_time_raw, ':', 2) AS INTEGER)
            ) MINUTE
        )                                                                        AS sighting_start_ts,

        -- sighting end: post-midnight if end < start
        (
            CASE
                WHEN sighting_end_time_raw < sighting_start_time_raw
                    THEN (event_date + INTERVAL 1 DAY)::TIMESTAMP
                ELSE event_date::TIMESTAMP
            END
            + INTERVAL (
                CAST(SPLIT_PART(sighting_end_time_raw, ':', 1) AS INTEGER) * 60
                + CAST(SPLIT_PART(sighting_end_time_raw, ':', 2) AS INTEGER)
            ) MINUTE
        )                                                                        AS sighting_end_ts,

        -- exclusion zone entry: post-midnight if time < sighting start
        CASE
            WHEN exclusion_zone_entry_time_raw IS NULL THEN NULL
            ELSE (
                CASE
                    WHEN exclusion_zone_entry_time_raw < sighting_start_time_raw
                        THEN (event_date + INTERVAL 1 DAY)::TIMESTAMP
                    ELSE event_date::TIMESTAMP
                END
                + INTERVAL (
                    CAST(SPLIT_PART(exclusion_zone_entry_time_raw, ':', 1) AS INTEGER) * 60
                    + CAST(SPLIT_PART(exclusion_zone_entry_time_raw, ':', 2) AS INTEGER)
                ) MINUTE
            )
        END                                                                      AS exclusion_zone_entry_ts,

        -- animal position timestamps: post-midnight if time < sighting start
        CASE
            WHEN animal_position_1_time_raw IS NULL THEN NULL
            ELSE (
                CASE
                    WHEN animal_position_1_time_raw < sighting_start_time_raw
                        THEN (event_date + INTERVAL 1 DAY)::TIMESTAMP
                    ELSE event_date::TIMESTAMP
                END
                + INTERVAL (
                    CAST(SPLIT_PART(animal_position_1_time_raw, ':', 1) AS INTEGER) * 60
                    + CAST(SPLIT_PART(animal_position_1_time_raw, ':', 2) AS INTEGER)
                ) MINUTE
            )
        END                                                                      AS animal_position_1_ts,

        CASE
            WHEN animal_position_2_time_raw IS NULL THEN NULL
            ELSE (
                CASE
                    WHEN animal_position_2_time_raw < sighting_start_time_raw
                        THEN (event_date + INTERVAL 1 DAY)::TIMESTAMP
                    ELSE event_date::TIMESTAMP
                END
                + INTERVAL (
                    CAST(SPLIT_PART(animal_position_2_time_raw, ':', 1) AS INTEGER) * 60
                    + CAST(SPLIT_PART(animal_position_2_time_raw, ':', 2) AS INTEGER)
                ) MINUTE
            )
        END                                                                      AS animal_position_2_ts,

        CASE
            WHEN animal_position_3_time_raw IS NULL THEN NULL
            ELSE (
                CASE
                    WHEN animal_position_3_time_raw < sighting_start_time_raw
                        THEN (event_date + INTERVAL 1 DAY)::TIMESTAMP
                    ELSE event_date::TIMESTAMP
                END
                + INTERVAL (
                    CAST(SPLIT_PART(animal_position_3_time_raw, ':', 1) AS INTEGER) * 60
                    + CAST(SPLIT_PART(animal_position_3_time_raw, ':', 2) AS INTEGER)
                ) MINUTE
            )
        END                                                                      AS animal_position_3_ts,

        -- closest approach: post-midnight if time < sighting start
        CASE
            WHEN closest_approach_time_raw IS NULL THEN NULL
            ELSE (
                CASE
                    WHEN closest_approach_time_raw < sighting_start_time_raw
                        THEN (event_date + INTERVAL 1 DAY)::TIMESTAMP
                    ELSE event_date::TIMESTAMP
                END
                + INTERVAL (
                    CAST(SPLIT_PART(closest_approach_time_raw, ':', 1) AS INTEGER) * 60
                    + CAST(SPLIT_PART(closest_approach_time_raw, ':', 2) AS INTEGER)
                ) MINUTE
            )
        END                                                                      AS closest_approach_ts,

        -- shutdown request: no midnight crossing needed, anchored to event_date
        CASE
            WHEN shutdown_request_time_raw IS NULL THEN NULL
            ELSE (
                event_date::TIMESTAMP
                + INTERVAL (
                    CAST(SPLIT_PART(shutdown_request_time_raw, ':', 1) AS INTEGER) * 60
                    + CAST(SPLIT_PART(shutdown_request_time_raw, ':', 2) AS INTEGER)
                ) MINUTE
            )
        END                                                                      AS shutdown_request_ts,

        -- shutdown performed: post-midnight relative to shutdown_request_time_raw
        CASE
            WHEN shutdown_time_raw IS NULL THEN NULL
            ELSE (
                CASE
                    WHEN shutdown_time_raw < shutdown_request_time_raw
                        THEN (event_date + INTERVAL 1 DAY)::TIMESTAMP
                    ELSE event_date::TIMESTAMP
                END
                + INTERVAL (
                    CAST(SPLIT_PART(shutdown_time_raw, ':', 1) AS INTEGER) * 60
                    + CAST(SPLIT_PART(shutdown_time_raw, ':', 2) AS INTEGER)
                ) MINUTE
            )
        END                                                                      AS shutdown_ts

    FROM casted
)

SELECT *
FROM timestamped