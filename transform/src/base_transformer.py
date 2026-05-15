import importlib
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
import sys


import pandas as pd

dir = Path(__file__).parent.parent.parent
sys.path.append(str(dir))
print("Current sys.path:", sys.path)

# ---------------------------------------------------------------------------
# Registry: maps form name → config module path
# Add a new entry here whenever a new form config is created.
# ---------------------------------------------------------------------------
CONFIG_REGISTRY: dict[str, str] = {
    "RA": "transform.config.config_ra_transform",
    "RDA": "transform.config.config_rda_transform",
}


class BaseTransformer:
    """
    Config-driven transformer for all form types.

    Instantiate with the form name and it loads the matching config
    automatically. No subclassing needed unless a form requires custom
    transformation logic beyond what the config can express.

    Usage:
        raw_df      = storage_client.read(...)       # handled externally
        transformer = BaseTransformer(form="RA")
        clean_df    = transformer.run(raw_df)
        storage_client.write(clean_df, ...)          # handled externally

    Adding a new form:
        1. Create  transform/config/config_<form>_transform.py
           with the same structure as config_ra_transform.py
        2. Add an entry to CONFIG_REGISTRY above — that's it.

    Overriding for a form with custom logic:
        Subclass BaseTransformer, call super().__init__(form) to load the
        config, then override only the step(s) that differ.

        class RDATransformer(BaseTransformer):
            def __init__(self):
                super().__init__(form="RDA")

            def _parse_dates(self, df):
                # RDA uses a different date format
                ...
    """

    def __init__(self, form: str):
        self.form = form.upper()
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{self.form}]")
        self._config = self._load_config(self.form)

    # ------------------------------------------------------------------
    # Config loading
    # ------------------------------------------------------------------

    def _load_config(self, form: str):
        if form not in CONFIG_REGISTRY:
            raise ValueError(
                f"Unknown form '{form}'. "
                f"Available forms: {sorted(CONFIG_REGISTRY.keys())}"
            )
        module_path = CONFIG_REGISTRY[form]
        try:
            config = importlib.import_module(module_path)
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                f"Config module for form '{form}' not found at '{module_path}'. "
                f"Make sure the file exists and the package is on sys.path."
            ) from e

        self.logger.debug("Loaded config from '%s'.", module_path)
        return config

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Runs the full transformation pipeline on the input DataFrame.
        Always operates on a copy — the original is never mutated.
        """
        self.logger.info("Starting transformation. Input shape: %s", df.shape)
        df = self.transform(df.copy())
        self.logger.info("Transformation complete. Output shape: %s", df.shape)
        return df

    # ------------------------------------------------------------------
    # Transformation pipeline
    # Override individual steps in a subclass when a form needs custom logic.
    # ------------------------------------------------------------------

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self._drop_empty_columns(df)
        df = self._rename_columns(df)
        df = self._parse_dates(df)
        df = self._validate_times(df)
        df = self._cast_nullable_ints(df)
        df = self._cast_booleans(df)
        df = self._drop_duplicates(df)
        df = self._add_metadata(df)
        return df

    # ------------------------------------------------------------------
    # Pipeline steps  (each reads its rules from self._config)
    # ------------------------------------------------------------------

    def _drop_empty_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop columns listed in config.COLUMNS_TO_DROP (matched against raw names)."""
        to_drop = getattr(self._config, "COLUMNS_TO_DROP", [])
        present = [c for c in to_drop if c in df.columns]
        if present:
            df = df.drop(columns=present)
            self.logger.info("Dropped empty columns: %s", present)
        return df

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename columns using config.COLUMN_RENAMES (exact raw name → final name)."""
        mapping = getattr(self._config, "COLUMN_RENAMES", {})
        unknown = [k for k in mapping if k not in df.columns]
        if unknown:
            self.logger.warning(
                "COLUMN_RENAMES references columns not found in DataFrame: %s", unknown
            )
        for old, new in mapping.items():
            if old in df.columns:
                self.logger.info("Renaming column %r → %r", old, new)
        return df.rename(columns=mapping)

    def _parse_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse dd/mm/yyyy string columns listed in config.DATE_COLUMNS into datetime64."""
        for col in getattr(self._config, "DATE_COLUMNS", []):
            if col not in df.columns:
                self.logger.warning("Date column '%s' not found, skipping.", col)
                continue
            df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors="coerce")
            nulls = df[col].isna().sum()
            if nulls:
                self.logger.warning(
                    "Column '%s': %d value(s) could not be parsed as date.", col, nulls
                )
            else:
                self.logger.info("Parsed date column '%s' successfully.", col)
        return df

    def _validate_times(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate columns listed in config.TIME_COLUMNS as 'HH:MM' strings.
        Values that don't match the pattern are set to NaN.
        """
        _time_re = re.compile(r"^\d{2}:\d{2}$")
        for col in getattr(self._config, "TIME_COLUMNS", []):
            if col not in df.columns:
                self.logger.warning("Time column '%s' not found, skipping.", col)
                continue
            mask_bad = df[col].notna() & ~df[col].astype(str).str.match(_time_re)
            if mask_bad.any():
                self.logger.warning(
                    "Column '%s': %d value(s) don't match HH:MM — setting to NaN.",
                    col,
                    mask_bad.sum(),
                )
                df.loc[mask_bad, col] = None
            else:
                self.logger.info("Validated time column '%s' successfully.", col)
        return df

    def _cast_nullable_ints(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cast columns in config.NULLABLE_INT_COLUMNS from float64 to pandas Int64."""
        for col in getattr(self._config, "NULLABLE_INT_COLUMNS", []):
            if col not in df.columns:
                self.logger.warning(
                    "Nullable-int column '%s' not found, skipping.", col
                )
                continue
            before_nulls = df[col].isna().sum()
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
            after_nulls = df[col].isna().sum()
            new_nulls = after_nulls - before_nulls
            if new_nulls:
                self.logger.warning(
                    "Column '%s': %d value(s) could not be cast to Int64 — set to NaN.",
                    col,
                    new_nulls,
                )
            else:
                self.logger.info("Cast column '%s' to Int64 successfully.", col)
        return df

    def _cast_booleans(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cast columns in config.BOOL_COLUMNS to pandas nullable boolean."""
        for col in getattr(self._config, "BOOL_COLUMNS", []):
            if col not in df.columns:
                self.logger.warning("Bool column '%s' not found, skipping.", col)
                continue
            df[col] = (
                df[col]
                .map(
                    lambda v: (
                        True
                        if str(v).strip().lower() == "true"
                        else False if str(v).strip().lower() == "false" else None
                    )
                )
                .astype("boolean")
            )
        return df

    def _drop_duplicates(
        self, df: pd.DataFrame, subset: Optional[list] = None
    ) -> pd.DataFrame:
        """Drop duplicate rows and log how many were removed."""
        before = len(df)
        df = df.drop_duplicates(subset=subset)
        dropped = before - len(df)
        if dropped:
            self.logger.info("Dropped %d duplicate rows.", dropped)
        return df

    def _add_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Stamp every row with processing metadata."""
        df["_processed_at"] = datetime.now(tz=timezone.utc).isoformat()
        df["_transformer"] = f"{self.__class__.__name__}[{self.form}]"
        return df


if __name__ == "__main__":
    import logging
    import os
    from io import BytesIO

    import pandas as pd

    from utils.storage_client import MinioS3Client

    logging.basicConfig(
        level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s"
    )

    SOURCE_BUCKET = "raw"
    SOURCE_KEY = "ra/bandar_report_2025-01-01_to_2025-01-31.xlsx"
    FORM = "ra"

    client = MinioS3Client(
        endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    )

    # --- read from MinIO into a DataFrame ---
    buf: BytesIO = client.get_fileobj(SOURCE_BUCKET, SOURCE_KEY)

    raw_df: pd.DataFrame = pd.read_excel(buf)
    print(f"Raw shape : {raw_df.shape}")
    for col in raw_df.columns:
        print(f"  {col:<70s} {str(raw_df[col].dtype)}")

    # # --- transform ---
    transformer = BaseTransformer(form=FORM)
    clean_df = transformer.run(raw_df)

    print(f"\nClean shape : {clean_df.shape}")
    print(f"\nClean columns & dtypes:")
    for col in clean_df.columns:
        print(f"  {col:<70s} {str(clean_df[col].dtype)}")
