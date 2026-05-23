import importlib
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
import sys
import pandas as pd


class BaseTransformer:
    """
    Config-driven transformer for all form types.

    Instantiate with the form name and a config module (imported or inline).
    No subclassing needed unless a form requires custom transformation logic
    beyond what the config can express.

    Usage:
        import transform.config.config_ra_transform as ra_config

        raw_df      = storage_client.read(...)       # handled externally
        transformer = BaseTransformer(form="RA", config=ra_config)
        clean_df    = transformer.run(raw_df)
        storage_client.write(clean_df, ...)          # handled externally

    Overriding for a form with custom logic:
        Subclass BaseTransformer and pass the config to super().__init__().

        import transform.config.config_rda_transform as rda_config

        class RDATransformer(BaseTransformer):
            def __init__(self):
                super().__init__(form="RDA", config=rda_config)

            def _parse_dates(self, df):
                # RDA uses a different date format
                ...
    """

    _TRUTHY = {"true", "sim", "yes", "1"}
    _FALSY = {"false", "não", "nao", "no", "0"}

    def __init__(self, form: str, config):
        self.form = form.upper()
        self.logger = logging.getLogger(f"{self.__class__.__name__}[{self.form}]")
        self._config = config
        self.logger.debug(
            "Config set to '%s'.", getattr(config, "__name__", repr(config))
        )

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
        df = self._drop_columns(df)
        df = self._rename_columns(df)
        df = self._parse_dates(df)
        df = self._validate_times(df)
        df = self._cast_nullable_ints(df)
        df = self._cast_booleans(df)
        df = self._drop_duplicates(df)
        df = self.post_process(df)
        df = self._add_metadata(df)
        return df

    # ------------------------------------------------------------------
    # Pipeline steps  (each reads its rules from self._config)
    # ------------------------------------------------------------------

    def _drop_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop columns listed in config.COLUMNS_TO_DROP (matched against raw names)."""
        to_drop = getattr(self._config, "COLUMNS_TO_DROP", [])
        present = [c for c in to_drop if c in df.columns]
        if present:
            df = df.drop(columns=present)
            self.logger.info("Dropped columns: %s", present)
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
            df[col] = pd.to_numeric(df[col], errors="coerce").round().astype("Int64")
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
        for col in getattr(self._config, "BOOL_COLUMNS", []):
            if col not in df.columns:
                self.logger.warning("Bool column '%s' not found, skipping.", col)
                continue
            before_nulls = df[col].isna().sum()
            df[col] = (
                df[col]
                .map(
                    lambda v: (
                        True
                        if str(v).strip().lower() in self._TRUTHY
                        else False if str(v).strip().lower() in self._FALSY else None
                    )
                )
                .astype("boolean")
            )
            after_nulls = df[col].isna().sum()
            new_nulls = after_nulls - before_nulls
            if new_nulls:
                self.logger.warning(
                    "Column '%s': %d value(s) could not be cast to boolean — set to NaN.",
                    col,
                    new_nulls,
                )
            else:
                self.logger.info("Cast column '%s' to boolean successfully.", col)
        return df

    def post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        """Hook for subclass-specific transformations. No-op by default."""
        return df

    def _drop_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop duplicate rows and log how many were removed."""
        before = len(df)
        df = df.drop_duplicates()
        dropped = before - len(df)
        if dropped:
            self.logger.info("Dropped %d duplicate rows.", dropped)
        return df

    def _add_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Stamp every row with processing metadata."""
        df["_processed_at"] = datetime.now(tz=timezone.utc).isoformat()
        df["_transformer"] = f"{self.__class__.__name__}[{self.form}]"
        self.logger.info("Metadata columns created")
        return df

    def hhmm_to_minutes(self, series: pd.Series) -> pd.Series:
        """Convert 'HH:MM' duration strings to total minutes as Int64. Invalid formats become NA."""

        def _convert(v):
            if pd.isna(v):
                return pd.NA
            parts = str(v).strip().split(":")
            if len(parts) != 2:
                self.logger.warning("Unexpected duration format %r — setting to NA.", v)
                return pd.NA
            try:
                return int(parts[0]) * 60 + int(parts[1])
            except ValueError:
                self.logger.warning("Could not parse duration %r — setting to NA.", v)
                return pd.NA

        return series.map(_convert).astype("Int64")

    def build_datetimes(
        self, date: pd.Series, start_time: pd.Series, end_time: pd.Series
    ):
        """
        Build start_datetime and end_datetime Series from date, start_time, and end_time.
        If end_time < start_time, the end date is the next day.

        Parameters:
            date: pd.Series of dates (datetime or date objects)
            start_time: pd.Series of times (datetime.time or strings like "22:45")
            end_time: pd.Series of times (datetime.time or strings like "00:24")

        Returns:
            start_datetime: pd.Series of combined start datetimes
            end_datetime: pd.Series of combined end datetimes
        """
        date_col = date.name or "date"
        start_time_col = start_time.name or "start_time"
        end_time_col = end_time.name or "end_time"

        try:
            date = pd.to_datetime(date).dt.normalize()
            start_time = pd.to_timedelta(
                pd.to_datetime(start_time.astype(str), format="%H:%M").dt.strftime(
                    "%H:%M:%S"
                )
            )
            end_time = pd.to_timedelta(
                pd.to_datetime(end_time.astype(str), format="%H:%M").dt.strftime(
                    "%H:%M:%S"
                )
            )

            crosses_midnight = end_time <= start_time
            end_date = date + pd.to_timedelta(crosses_midnight.astype(int), unit="D")

            start_datetime = date + start_time
            end_datetime = end_date + end_time

        except Exception as e:
            self.logger.warning(
                "build_datetimes: failed to build datetimes from columns '%s', '%s', '%s' — %s",
                date_col,
                start_time_col,
                end_time_col,
                e,
            )
            return None, None

        self.logger.info(
            "build_datetimes: '%s' and '%s' built successfully from '%s', '%s', '%s'.",
            "start_datetime",
            "end_datetime",
            date_col,
            start_time_col,
            end_time_col,
        )
        return start_datetime, end_datetime


if __name__ == "__main__":
    import logging
    import os
    from io import BytesIO

    import pandas as pd
    import transform.config.config_ra_transform as ra_config

    from utils.storage_client import MinioS3Client

    logging.basicConfig(
        level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s"
    )

    SOURCE_BUCKET = "raw"
    SOURCE_KEY = "ra/bandar_report_2025-01-01_to_2025-01-31.xlsx"

    client = MinioS3Client(
        endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
    )

    buf: BytesIO = client.get_fileobj(SOURCE_BUCKET, SOURCE_KEY)
    raw_df: pd.DataFrame = pd.read_excel(buf)
    print(f"Raw shape : {raw_df.shape}")
    for col in raw_df.columns:
        print(f"  {col:<70s} {str(raw_df[col].dtype)}")

    transformer = BaseTransformer(form="RA", config=ra_config)
    clean_df = transformer.run(raw_df)

    print(f"\nClean shape : {clean_df.shape}")
    print(f"\nClean columns & dtypes:")
    for col in clean_df.columns:
        print(f"  {col:<70s} {str(clean_df[col].dtype)}")
