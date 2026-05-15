# ---------------------------------------------------------------------------
# config_rda_transform.py
#
# All transformation rules for the RDA (Relatório de Detecção Acústica) form.
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
    "numero": "detection_number",
    "ra": "sighting_report_ref",
    # --- project dates ---
    "Data de início (Primeira emissão sonora)": "first_seismic_shot_date",
    "Data de término (Última emissão sonora)": "last_seismic_shot_date",
    # --- operator / observer CTF codes ---
    "operador de map responsavel / 1 / ctf": "map_operator_1_ctf",
    "operador de map responsavel / 2 / ctf": "map_operator_2_ctf",
    "operador de map responsavel / 3 / ctf": "map_operator_3_ctf",
    "usuario observador responsavel / 1 / ctf": "user_observer_1_ctf",
    "usuario observador responsavel / 2 / ctf": "user_observer_2_ctf",
    "usuario observador responsavel / 3 / ctf": "user_observer_3_ctf",
    # --- detection event ---
    "data do evento": "event_date",
    "hora inicio da deteccao": "detection_start_time",
    "hora final da deteccao": "detection_end_time",
    # --- detection coordinates ---
    "latitude": "latitude",
    "longitude": "longitude",
    "profundidade": "depth_m",
    # --- environmental conditions ---
    "estado do mar": "sea_state",
    "ondulacao do mar": "swell",
    "velocidade do vento": "wind_speed_knots",
    # --- vessel ---
    "navio sismico / nome": "vessel_name",
    # --- identification ---
    "identificacao / identificacao da deteccao / identificacao": "species_identification",
    "identificacao / grupo misto": "mixed_group",
    "identificacao / identificacao visual": "visual_identification",
    "identificacao / tipo de som detectado": "detected_sound_type",
    "identificacao / outro tipo de som detectado": "other_detected_sound_type",
    "identificacao / frequencia minima": "min_frequency_hz",
    "identificacao / frequencia maxima": "max_frequency_hz",
    "identificacao / forca do sinal": "signal_strength",
    "identificacao / ruido ambiente": "ambient_noise",
    "identificacao / tecnicas de deteccao utilizadas": "detection_techniques",
    "identificacao / outra tecnica de deteccao utilizada": "other_detection_technique",
    "identificacao / confianca na identificacao": "identification_confidence",
    # --- MAP array ---
    "map / arranjo utilizado ": "map_array_used",
    "map / numero de hidrofones ": "map_hydrophone_count",
    "map / profundidade do arranjo map ": "map_array_depth_m",
    "map / unidades de interface ": "map_interface_units",
    "map / distancia entre pares de hidrofones ": "map_hydrophone_pair_distance_m",
    "map / distancia das fontes sonoras para a popa do navio ": "map_source_to_stern_distance_m",
    "map / distancia do h1 do cabo map para a popa do navio ": "map_h1_to_stern_distance_m",
    "map / gravacao de audio ": "map_audio_recording",
    # --- air guns / seismic source ---
    "canhoes de ar / estado da fonte sismica": "seismic_source_status",
    "canhoes de ar / acao realizada": "action_taken",
    "canhoes de ar / desligamento solicitado": "shutdown_requested",
    "canhoes de ar / hora da solicitacao": "shutdown_request_time",
    "canhoes de ar / desligamento realizado": "shutdown_performed",
    "canhoes de ar / hora do desligamento": "shutdown_time",
    "canhoes de ar / tempo total de interrupcao": "total_activity_interruption_time",
    "canhoes de ar / tempo total de deteccao": "total_detection_duration_min",
    "canhoes de ar / volume da fonte sismica": "seismic_source_volume_cui",
    # --- detection description / distances ---
    "descricao da deteccao": "detection_description",
    "descricao de parametros": "parameter_description",
    "distancia inicial": "initial_distance_m",
    "distancia final": "final_distance_m",
    "menor distancia": "closest_approach_distance_m",
    "hora de menor distancia": "closest_approach_time",
    # --- visual effort / record metadata ---
    "esforco visual": "visual_effort",
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
    "detection_start_time",
    "detection_end_time",
    "shutdown_request_time",
    "shutdown_time",
    "total_activity_interruption_time",
    "closest_approach_time",
]


# ---------------------------------------------------------------------------
# 4. Nullable integer columns  → Int64  (float64 with NaN → Int64 with <NA>)
#    Use the FINAL name (after rename).
# ---------------------------------------------------------------------------
NULLABLE_INT_COLUMNS: list[str] = [
    # --- CTF codes (operators may be absent) ---
    "map_operator_3_ctf",
    "user_observer_2_ctf",
    "user_observer_3_ctf",
    # --- acoustic signal properties ---
    "min_frequency_hz",
    "max_frequency_hz",
    "signal_strength",
    "ambient_noise",
    # --- MAP array measurements (some nullable) ---
    "map_hydrophone_count",
    "map_interface_units",
    "map_hydrophone_pair_distance_m",
    "map_h1_to_stern_distance_m",
    # --- environmental conditions (nullable in current data) ---
    # "sea_state",
    # "swell",
    "wind_speed_knots",
    # --- distances ---
    "initial_distance_m",
    "final_distance_m",
    "closest_approach_distance_m",
    # --- seismic source ---
    "seismic_source_volume_cui",
    "total_detection_duration_min",
]


# ---------------------------------------------------------------------------
# 5. Boolean columns  → pandas boolean (nullable)
#    Use the FINAL name (after rename).
# ---------------------------------------------------------------------------
BOOL_COLUMNS: list[str] = [
    "mixed_group",
    "visual_identification",
    "shutdown_requested",
    "shutdown_performed",
    "map_audio_recording",
]


# ---------------------------------------------------------------------------
# 6. Columns to drop  (always empty in current exports)
#    Use the EXACT raw name (before rename) — dropped before rename runs.
# ---------------------------------------------------------------------------
COLUMNS_TO_DROP: list[str] = [
    "edd",
]
