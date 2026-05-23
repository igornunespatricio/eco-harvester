{{ config(
    materialized='external',
    location=silver_location('rda')
) }}

WITH renamed AS (
    SELECT
        "Numero_processo"                                                        AS process_number,
        "Nome_processo"                                                          AS process_name,
        "Data de início (Primeira emissão sonora)"                               AS first_seismic_shot_date,
        "Data de término (Última emissão sonora)"                                AS last_seismic_shot_date,
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
        "data do evento"                                                         AS event_date,
        "hora inicio da deteccao"                                                AS detection_start_time,
        "hora final da deteccao"                                                 AS detection_end_time,
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
        "canhoes de ar / hora da solicitacao"                                    AS shutdown_request_time,
        "canhoes de ar / desligamento realizado"                                 AS shutdown_performed,
        "canhoes de ar / hora do desligamento"                                   AS shutdown_time,
        "canhoes de ar / tempo total de interrupcao"                             AS total_activity_interruption_min,
        "canhoes de ar / tempo total de deteccao"                                AS total_detection_time_min,
        "canhoes de ar / volume da fonte sismica"                                AS seismic_source_volume_cui,
        "descricao da deteccao"                                                  AS detection_description,
        "descricao de parametros"                                                AS parameters_description,
        "distancia inicial"                                                      AS initial_distance_m,
        "distancia final"                                                        AS final_distance_m,
        "menor distancia"                                                        AS closest_approach_distance_m,
        "hora de menor distancia"                                                AS closest_approach_time,
        "esforco visual"                                                         AS visual_effort,
        "status do registro"                                                     AS record_status,
        "observacoes gerais"                                                     AS general_notes,
        "ingested_at"                                                            AS ingested_at
    FROM read_parquet({{ bronze_path('rda') }})
),

ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY rda_number ORDER BY ingested_at DESC) AS rn
    FROM renamed
)

SELECT * EXCLUDE (rn)
FROM ranked
WHERE rn = 1