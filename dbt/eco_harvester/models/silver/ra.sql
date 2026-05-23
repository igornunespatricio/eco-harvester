{{ config(
    materialized='external',
    location=silver_location('ra')
) }}

WITH renamed AS (
    SELECT
        "Numero_processo"                                                        AS process_number,
        "Nome_processo"                                                          AS process_name,
        "Data de início (Primeira emissão sonora)"                               AS first_seismic_shot_date,
        "Data de término (Última emissão sonora)"                                AS last_seismic_shot_date,
        "Situação do Projeto"                                                    AS project_status,
        "numero da deteccao"                                                     AS ra_number,
        "eda"                                                                    AS eda,
        "observador responsavel / 1 / ctf"                                       AS observer_1_ctf,
        "observador responsavel / 2 / ctf"                                       AS observer_2_ctf,
        "observador responsavel / 3 / ctf"                                       AS observer_3_ctf,
        "usuario observador responsavel / 1 / ctf"                               AS user_observer_1_ctf,
        "usuario observador responsavel / 2 / ctf"                               AS user_observer_2_ctf,
        "usuario observador responsavel / 3 / ctf"                               AS user_observer_3_ctf,
        "data do evento"                                                         AS event_date,
        "hora inicio da avistagem"                                               AS sighting_start_time,
        "hora final da avistagem"                                                AS sighting_end_time,
        "hora entrada na area de exclusao"                                       AS exclusion_zone_entry_time,
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
        "observacao / posicao do animal ou grupo / 1 / hora"                    AS animal_position_1_time,
        "observacao / posicao do animal ou grupo / 1 / menor distancia"         AS animal_position_1_closest,
        "observacao / posicao do animal ou grupo / 1 / distancia"               AS animal_position_1_distance_m,
        "observacao / posicao do animal ou grupo / 2 / posicao"                 AS animal_position_2,
        "observacao / posicao do animal ou grupo / 2 / hora"                    AS animal_position_2_time,
        "observacao / posicao do animal ou grupo / 2 / menor distancia"         AS animal_position_2_closest,
        "observacao / posicao do animal ou grupo / 2 / distancia"               AS animal_position_2_distance_m,
        "observacao / posicao do animal ou grupo / 3 / posicao"                 AS animal_position_3,
        "observacao / posicao do animal ou grupo / 3 / hora"                    AS animal_position_3_time,
        "observacao / posicao do animal ou grupo / 3 / menor distancia"         AS animal_position_3_closest,
        "observacao / posicao do animal ou grupo / 3 / distancia"               AS animal_position_3_distance_m,
        "canhoes de ar / estado da fonte sismica"                                AS seismic_source_status,
        "canhoes de ar / acao realizada"                                         AS action_taken,
        "canhoes de ar / desligamento solicitado"                                AS shutdown_requested,
        "canhoes de ar / hora da solicitacao"                                    AS shutdown_request_time,
        "canhoes de ar / desligamento realizado"                                 AS shutdown_performed,
        "canhoes de ar / hora do desligamento"                                   AS shutdown_time,
        "canhoes de ar / tempo total de interrupcao da atividade"                AS total_activity_interruption_min,
        "canhoes de ar / volume da fonte sismica"                                AS seismic_source_volume_cui,
        "canhoes de ar / hora de menor distancia"                                AS closest_approach_time,
        "canhoes de ar / menor distancia da fonte sismica"                       AS closest_approach_distance_m,
        "map"                                                                    AS map_status,
        "status do registro"                                                     AS record_status,
        "observacoes gerais"                                                     AS general_notes,
        "ingested_at"                                                            AS ingested_at
    FROM read_parquet({{ bronze_path('ra') }})
),

ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY ra_number ORDER BY ingested_at DESC) AS rn
    FROM renamed
)

SELECT * EXCLUDE (rn)
FROM ranked
WHERE rn = 1