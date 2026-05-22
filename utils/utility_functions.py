import argparse
import datetime
import os
from io import BytesIO
import pandas as pd

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
BRONZE_PATH = os.getenv("BRONZE_PATH", "bronze")


def str_to_bool(v: str) -> bool:
    """Convert a string to a boolean value.
    Accepts 'true', '1', 'yes' (case-insensitive) as True,
    and 'false', '0', 'no' as False.
    Raises an error for invalid inputs.
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ("true", "1", "yes"):
        return True
    if v.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got: {v!r}")


def bronze_path(form: str, date: datetime.date, filename: str) -> str:
    """
    Construct the s3/Minio path for bronze layer.
    Pattern: {BRONZE_PATH}/{form}/year={year}/month={month:02d}/day={day:02d}/{filename}

    NOTE: This partition pattern is mirrored in dbt/eco_harvester/macros/bronze_path.sql
    If you change the pattern here, update the macro too.
    """
    return f"{BRONZE_PATH}/{form.lower()}/year={date.year}/month={date.month:02d}/day={date.day:02d}/{filename}"


def silver_path(form: str, date: datetime.date, filename: str) -> str:
    """Construct the s3/Minio path for a given form, date and filename in the silver layer with year and month partition."""
    filename_prefix = f"day={date.day:02d}"
    return f"silver/{form.lower()}/year={date.year}/month={date.month:02d}/{filename_prefix}_{filename}"


def xlsx_bytes_to_parquet(xlsx_bytes: bytes) -> bytes:
    """Convert xlsx bytes to parquet bytes."""
    df = pd.read_excel(BytesIO(xlsx_bytes), engine="openpyxl")
    parquet_buffer = BytesIO()
    df.to_parquet(parquet_buffer, index=False, engine="pyarrow")
    return parquet_buffer.getvalue()
