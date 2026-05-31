{{ config(
    materialized='external',
    location=silver_location('rda')
) }}

WITH renamed AS (
    SELECT
        "Numero_processo"                                                        AS process_number,
        "Nome_processo"                                                          AS process_name,
        "Data de início (Primeira emissão sonora)"                               AS first_seismic_shot_date_raw,
        "Data de término (Última emissão sonora)"                                AS last_seismic_shot_date_raw,
        "Situação do Projeto"                                                    AS project_status,
        "numero"                                                                 AS rda_number,
        "edd"                                                                    AS edd,
        "ra"                                                                     AS ra_number,
        "operador de map responsavel / 1 / ctf"                                  AS map_operator_1_ctf,
        "operador de map responsavel / 2 / ctf"                                  AS map_operator_2_ctf,
        "operador de map responsavel / 3 / ctf"                                  AS map_operator_3_ctf,
        "usuario observador responsavel / 1 / ctf"                               AS user_observer_1_ctf,
        "usuario observador responsavel / 2 / ctf"                               AS user_observer_2_ctf,
        "usuario observador responsavel / 3 / ctf"                               AS user_observer_3_ctf,
        "data do evento"                                                         AS event_date_raw,
        "hora inicio da deteccao"                                                AS detection_start_time_raw,
        "hora final da deteccao"                                                 AS detection_end_time_raw,
        "latitude"                                                               AS latitude,
        "longitude"                                                              AS longitude,
        "profundidade"                                                           AS depth_m,
        "estado do mar"                                                          AS sea_state,
        "ondulacao do mar"                                                       AS swell,
        "velocidade do vento"                                                    AS wind_speed_knots,
        "navio sismico / nome"                                                   AS seismic_vessel_name,
        "identificacao / identificacao da deteccao / identificacao"              AS species_identification,
        "identificacao / grupo misto"                                            AS mixed_group,
        "identificacao / identificacao visual"                                   AS visual_identification,
        "identificacao / tipo de som detectado"                                  AS detected_sound_type,
        "identificacao / outro tipo de som detectado"                            AS other_detected_sound_type,
        "identificacao / frequencia minima"                                      AS min_frequency_hz,
        "identificacao / frequencia maxima"                                      AS max_frequency_hz,
        "identificacao / forca do sinal"                                         AS signal_strength,
        "identificacao / ruido ambiente"                                         AS ambient_noise,
        "identificacao / tecnicas de deteccao utilizadas"                        AS detection_techniques,
        "identificacao / outra tecnica de deteccao utilizada"                    AS other_detection_technique,
        "identificacao / confianca na identificacao"                             AS identification_confidence,
        "map / arranjo utilizado "                                               AS map_array_used,
        "map / numero de hidrofones "                                            AS map_hydrophone_count,
        "map / profundidade do arranjo map "                                     AS map_array_depth_m,
        "map / unidades de interface "                                           AS map_interface_units,
        "map / distancia entre pares de hidrofones "                             AS map_hydrophone_pair_distance_m,
        "map / distancia das fontes sonoras para a popa do navio "               AS map_sound_source_to_stern_m,
        "map / distancia do h1 do cabo map para a popa do navio "                AS map_h1_to_stern_m,
        "map / gravacao de audio "                                               AS map_audio_recording,
        "canhoes de ar / estado da fonte sismica"                                AS seismic_source_status,
        "canhoes de ar / acao realizada"                                         AS action_taken,
        "canhoes de ar / desligamento solicitado"                                AS shutdown_requested,
        "canhoes de ar / hora da solicitacao"                                    AS shutdown_request_time_raw,
        "canhoes de ar / desligamento realizado"                                 AS shutdown_performed,
        "canhoes de ar / hora do desligamento"                                   AS shutdown_time_raw,
        "canhoes de ar / tempo total de interrupcao"                             AS total_activity_interruption_raw,
        "canhoes de ar / tempo total de deteccao"                                AS total_detection_time_min,
        "canhoes de ar / volume da fonte sismica"                                AS seismic_source_volume_cui,
        "descricao da deteccao"                                                  AS detection_description,
        "descricao de parametros"                                                AS parameters_description,
        "distancia inicial"                                                      AS initial_distance_m,
        "distancia final"                                                        AS final_distance_m,
        "menor distancia"                                                        AS closest_approach_distance_m,
        "hora de menor distancia"                                                AS closest_approach_time_raw,
        "esforco visual"                                                         AS visual_effort,
        "status do registro"                                                     AS record_status,
        "observacoes gerais"                                                     AS general_notes,
        "ingested_at"                                                            AS ingested_at
    FROM read_parquet({{ bronze_path('rda') }})
),

-- ── Step 1: deduplicate — keep the most recently ingested record per RDA ────
deduped AS (
    SELECT
        * EXCLUDE (rn)
    FROM (
        SELECT
            *,
            ROW_NUMBER() OVER (PARTITION BY rda_number ORDER BY ingested_at DESC) AS rn
        FROM renamed
    )
    WHERE rn = 1
),

-- ── Step 2: cast raw strings to proper types ────────────────────────────────
casted AS (
    SELECT
        -- identifiers & descriptors (already strings, kept as-is)
        process_number,
        process_name,
        project_status,
        rda_number,
        edd,
        ra_number,
        seismic_vessel_name,
        species_identification,
        mixed_group,
        detected_sound_type,
        other_detected_sound_type,
        identification_confidence,
        detection_techniques,
        other_detection_technique,
        sea_state,
        swell,
        seismic_source_status,
        action_taken,
        visual_effort,
        record_status,
        detection_description,
        parameters_description,
        general_notes,

        -- operator / observer ids
        map_operator_1_ctf,
        map_operator_2_ctf,
        map_operator_3_ctf,
        CAST(user_observer_1_ctf AS INTEGER)                                     AS user_observer_1_ctf,
        CAST(user_observer_2_ctf AS INTEGER)                                     AS user_observer_2_ctf,
        CAST(user_observer_3_ctf AS INTEGER)                                     AS user_observer_3_ctf,

        -- project dates  (DD/MM/YYYY → DATE)
        STRPTIME(first_seismic_shot_date_raw, '%d/%m/%Y')::DATE                  AS first_seismic_shot_date,
        STRPTIME(last_seismic_shot_date_raw,  '%d/%m/%Y')::DATE                  AS last_seismic_shot_date,

        -- event date
        STRPTIME(event_date_raw, '%d/%m/%Y')::DATE                               AS event_date,

        -- raw time strings cast to VARCHAR for timestamp assembly below
        -- (defensive cast: all-null batches can cause DuckDB to infer DOUBLE, breaking SPLIT_PART)
        CAST(detection_start_time_raw  AS VARCHAR)                               AS detection_start_time_raw,
        CAST(detection_end_time_raw    AS VARCHAR)                               AS detection_end_time_raw,
        CAST(shutdown_request_time_raw AS VARCHAR)                               AS shutdown_request_time_raw,
        CAST(shutdown_time_raw         AS VARCHAR)                               AS shutdown_time_raw,
        CAST(closest_approach_time_raw AS VARCHAR)                               AS closest_approach_time_raw,

        -- geospatial
        CAST(latitude  AS DOUBLE)                                                AS latitude,
        CAST(longitude AS DOUBLE)                                                AS longitude,
        CAST(depth_m   AS INTEGER)                                               AS depth_m,

        -- environmental
        CAST(wind_speed_knots AS DOUBLE)                                         AS wind_speed_knots,

        -- acoustic / identification
        CAST(min_frequency_hz AS INTEGER)                                        AS min_frequency_hz,
        CAST(max_frequency_hz AS INTEGER)                                        AS max_frequency_hz,
        CAST(signal_strength  AS INTEGER)                                        AS signal_strength,
        CAST(ambient_noise    AS INTEGER)                                        AS ambient_noise,

        -- boolean-like flags  ('Sim' → TRUE, 'Não' → FALSE)
        -- (cast to VARCHAR first: all-null batches cause DuckDB to infer DOUBLE, breaking string comparison)
        (CAST(visual_identification AS VARCHAR) = 'Sim')                         AS visual_identification,
        (CAST(shutdown_requested    AS VARCHAR) = 'Sim')                         AS shutdown_requested,
        (CAST(shutdown_performed    AS VARCHAR) = 'Sim')                         AS shutdown_performed,
        CASE
            WHEN CAST(map_audio_recording AS VARCHAR) = 'Sim' THEN TRUE
            WHEN CAST(map_audio_recording AS VARCHAR) = 'Não' THEN FALSE
            ELSE NULL
        END                                                                      AS map_audio_recording,

        -- MAP equipment
        CAST(map_array_used               AS INTEGER)                            AS map_array_used,
        CAST(map_hydrophone_count         AS INTEGER)                            AS map_hydrophone_count,
        CAST(map_array_depth_m            AS DOUBLE)                             AS map_array_depth_m,
        CAST(map_interface_units          AS INTEGER)                            AS map_interface_units,
        CAST(map_hydrophone_pair_distance_m   AS INTEGER)                        AS map_hydrophone_pair_distance_m,
        CAST(map_sound_source_to_stern_m      AS DOUBLE)                         AS map_sound_source_to_stern_m,
        CAST(map_h1_to_stern_m            AS INTEGER)                            AS map_h1_to_stern_m,

        -- distances
        CAST(initial_distance_m           AS INTEGER)                            AS initial_distance_m,
        CAST(final_distance_m             AS INTEGER)                            AS final_distance_m,
        CAST(closest_approach_distance_m  AS INTEGER)                            AS closest_approach_distance_m,

        -- shutdown & detection durations
        -- HH:MM string → integer minutes
        (
            CAST(SPLIT_PART(total_activity_interruption_raw, ':', 1) AS INTEGER) * 60
            + CAST(SPLIT_PART(total_activity_interruption_raw, ':', 2) AS INTEGER)
        )                                                                        AS total_activity_interruption_min,
        CAST(total_detection_time_min AS INTEGER)                                AS total_detection_time_min,
        CAST(seismic_source_volume_cui AS INTEGER)                               AS seismic_source_volume_cui,

        ingested_at
    FROM deduped
),

-- ── Step 3: assemble timestamps, handling midnight crossings ─────────────────
--
-- Pattern: combine event_date (a DATE) with a HH:MM string.
-- If end_time < start_time the detection crossed midnight, so end is event_date + 1.
-- Same logic applied to closest_approach_time, shutdown times, which
-- are within the detection window and can also be post-midnight.
--
timestamped AS (
    SELECT
        * EXCLUDE (
            detection_start_time_raw,
            detection_end_time_raw,
            shutdown_request_time_raw,
            shutdown_time_raw,
            closest_approach_time_raw
        ),

        -- detection start: always on event_date
        (event_date::TIMESTAMP + INTERVAL (
            CAST(SPLIT_PART(detection_start_time_raw, ':', 1) AS INTEGER) * 60
            + CAST(SPLIT_PART(detection_start_time_raw, ':', 2) AS INTEGER)
        ) MINUTE)                                                                AS detection_start_ts,

        -- detection end: +1 day if end_time < start_time (midnight crossing)
        (
            CASE
                WHEN detection_end_time_raw < detection_start_time_raw
                    THEN (event_date + INTERVAL 1 DAY)::TIMESTAMP
                ELSE event_date::TIMESTAMP
            END
            + INTERVAL (
                CAST(SPLIT_PART(detection_end_time_raw, ':', 1) AS INTEGER) * 60
                + CAST(SPLIT_PART(detection_end_time_raw, ':', 2) AS INTEGER)
            ) MINUTE
        )                                                                        AS detection_end_ts,

        -- closest approach: post-midnight if its time < start_time
        CASE
            WHEN closest_approach_time_raw IS NULL THEN NULL
            ELSE (
                CASE
                    WHEN closest_approach_time_raw < detection_start_time_raw
                        THEN (event_date + INTERVAL 1 DAY)::TIMESTAMP
                    ELSE event_date::TIMESTAMP
                END
                + INTERVAL (
                    CAST(SPLIT_PART(closest_approach_time_raw, ':', 1) AS INTEGER) * 60
                    + CAST(SPLIT_PART(closest_approach_time_raw, ':', 2) AS INTEGER)
                ) MINUTE
            )
        END                                                                      AS closest_approach_ts,

        -- shutdown request: no midnight crossing logic needed, treated as a
        -- point-in-time within the detection window anchored to event_date
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

        -- shutdown performed: post-midnight relative to shutdown_request_time_raw,
        -- since the relevant window is request → performed, not detection start → performed
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