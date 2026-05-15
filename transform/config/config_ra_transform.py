# ---------------------------------------------------------------------------
# config_ra_transform.py
#
# All transformation rules for the RA (Relatório de Avistamento) form.
#
# Keys in every mapping are the EXACT raw column names as they come out of
# the xlsx — no normalisation is applied before consulting this file.
# That makes it immediately obvious what is being renamed or cast.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 1. Column renames  (exact raw name → final English snake_case name)
#    Every column in the source should have an entry here.
#    Columns not listed are kept with their original raw name.
# ---------------------------------------------------------------------------
COLUMN_RENAMES: dict[str, str] = {
    # --- project / process identifiers ---
    "Numero_processo": "process_number",
    "Nome_processo": "process_name",
    "Situação do Projeto": "project_status",
    "numero da deteccao": "detection_number",
    # --- project dates ---
    "Data de início (Primeira emissão sonora)": "first_seismic_shot_date",
    "Data de término (Última emissão sonora)": "last_seismic_shot_date",
    # --- observer CTF codes ---
    "observador responsavel / 1 / ctf": "observer_1_ctf",
    "observador responsavel / 2 / ctf": "observer_2_ctf",
    "observador responsavel / 3 / ctf": "observer_3_ctf",
    "usuario observador responsavel / 1 / ctf": "user_observer_1_ctf",
    "usuario observador responsavel / 2 / ctf": "user_observer_2_ctf",
    "usuario observador responsavel / 3 / ctf": "user_observer_3_ctf",
    # --- sighting event ---
    "data do evento": "event_date",
    "hora inicio da avistagem": "sighting_start_time",
    "hora final da avistagem": "sighting_end_time",
    "hora entrada na area de exclusao": "exclusion_zone_entry_time",
    # --- vessel ---
    "navio / nome": "vessel_name",
    "direcao do navio": "vessel_heading_deg",
    # --- environmental conditions ---
    "estado do mar": "sea_state",
    "visibilidade": "visibility",
    "reflexo": "glare",
    "vento": "wind_speed_knots",
    "ondulacao do mar": "swell",
    # --- sighting coordinates (set 1) ---
    "coordenada / 1 / latitude": "coord_1_lat",
    "coordenada / 1 / longitude": "coord_1_lon",
    "coordenada / 1 / profundidade": "coord_1_depth_m",
    # --- sighting coordinates (set 2) ---
    "coordenada / 2 / latitude": "coord_2_lat",
    "coordenada / 2 / longitude": "coord_2_lon",
    "coordenada / 2 / profundidade": "coord_2_depth_m",
    # --- sighting coordinates (set 3) ---
    "coordenada / 3 / latitude": "coord_3_lat",
    "coordenada / 3 / longitude": "coord_3_lon",
    "coordenada / 3 / profundidade": "coord_3_depth_m",
    # --- observation / identification ---
    "observacao / identificacao da avistagem / identificacao": "species_identification",
    "observacao / confianca da identificacao": "identification_confidence",
    "observacao / descricao da confianca da identificacao": "identification_confidence_description",
    "observacao / grupo": "group_observation",
    "observacao / quantidade de adultos": "adult_count",
    "observacao / quantidade de filhotes": "calf_count",
    "observacao / comportamento": "behaviour",
    "observacao / outro comportamento": "other_behaviour",
    "observacao / caracteristicas observadas": "observed_characteristics",
    "observacao / outra caracteristica observada": "other_observed_characteristic",
    # --- animal positions (set 1) ---
    "observacao / posicao do animal ou grupo / 1 / posicao": "animal_position_1",
    "observacao / posicao do animal ou grupo / 1 / hora": "animal_position_1_time",
    "observacao / posicao do animal ou grupo / 1 / menor distancia": "animal_position_1_closest",
    "observacao / posicao do animal ou grupo / 1 / distancia": "animal_position_1_distance_m",
    # --- animal positions (set 2) ---
    "observacao / posicao do animal ou grupo / 2 / posicao": "animal_position_2",
    "observacao / posicao do animal ou grupo / 2 / hora": "animal_position_2_time",
    "observacao / posicao do animal ou grupo / 2 / menor distancia": "animal_position_2_closest",
    "observacao / posicao do animal ou grupo / 2 / distancia": "animal_position_2_distance_m",
    # --- animal positions (set 3) ---
    "observacao / posicao do animal ou grupo / 3 / posicao": "animal_position_3",
    "observacao / posicao do animal ou grupo / 3 / hora": "animal_position_3_time",
    "observacao / posicao do animal ou grupo / 3 / menor distancia": "animal_position_3_closest",
    "observacao / posicao do animal ou grupo / 3 / distancia": "animal_position_3_distance_m",
    # --- air guns / seismic source ---
    "canhoes de ar / estado da fonte sismica": "seismic_source_status",
    "canhoes de ar / acao realizada": "action_taken",
    "canhoes de ar / desligamento solicitado": "shutdown_requested",
    "canhoes de ar / hora da solicitacao": "shutdown_request_time",
    "canhoes de ar / desligamento realizado": "shutdown_performed",
    "canhoes de ar / hora do desligamento": "shutdown_time",
    "canhoes de ar / tempo total de interrupcao da atividade": "total_activity_interruption_min",
    "canhoes de ar / volume da fonte sismica": "seismic_source_volume_cui",
    "canhoes de ar / hora de menor distancia": "closest_approach_time",
    "canhoes de ar / menor distancia da fonte sismica": "closest_approach_distance_m",
    # --- record metadata ---
    "map": "map_status",
    "status do registro": "record_status",
    "observacoes gerais": "general_notes",
}


# ---------------------------------------------------------------------------
# 2. Date columns  → datetime64  (source format: dd/mm/yyyy)
#    Use the FINAL name (after rename).
# ---------------------------------------------------------------------------
DATE_COLUMNS: list[str] = [
    "first_seismic_shot_date",
    "last_seismic_shot_date",
    "event_date",
]


# ---------------------------------------------------------------------------
# 3. Time columns  → validated "HH:MM" strings (bad values → NaN)
#    Use the FINAL name (after rename).
# ---------------------------------------------------------------------------
TIME_COLUMNS: list[str] = [
    "sighting_start_time",
    "sighting_end_time",
    "exclusion_zone_entry_time",
    "animal_position_1_time",
    "animal_position_2_time",
    "animal_position_3_time",
    "shutdown_request_time",
    "shutdown_time",
    "closest_approach_time",
]


# ---------------------------------------------------------------------------
# 4. Nullable integer columns  → Int64  (float64 with NaN → Int64 with <NA>)
#    Use the FINAL name (after rename).
# ---------------------------------------------------------------------------
NULLABLE_INT_COLUMNS: list[str] = [
    # --- already present ---
    "observer_2_ctf",
    "observer_3_ctf",
    "user_observer_3_ctf",
    # --- new: CTF completeness ---
    "observer_1_ctf",
    "user_observer_1_ctf",
    "user_observer_2_ctf",
    # --- new: nullable in current data ---
    "vessel_heading_deg",
    "animal_position_2_distance_m",
    "animal_position_3_distance_m",
    "seismic_source_volume_cui",
    # --- new: currently no nulls but whole-number semantics ---
    "sea_state",
    "wind_speed_knots",
    "adult_count",
    "calf_count",
    "animal_position_1_distance_m",
    "total_activity_interruption_min",
    "closest_approach_distance_m",
]


# ---------------------------------------------------------------------------
# 5. Boolean columns  → pandas boolean (nullable)
#    Use the FINAL name (after rename).
# ---------------------------------------------------------------------------
BOOL_COLUMNS: list[str] = [
    "animal_position_1_closest",
    "animal_position_2_closest",
    "animal_position_3_closest",
]


# ---------------------------------------------------------------------------
# 6. Columns to drop  (always empty in current exports)
#    Use the EXACT raw name (before rename) — dropped before rename runs.
# ---------------------------------------------------------------------------
COLUMNS_TO_DROP: list[str] = [
    "eda",
]
