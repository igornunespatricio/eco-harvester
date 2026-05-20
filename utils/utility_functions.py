import argparse
import datetime
import os

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
    """Construct the s3/Minio path for a given form, date and filename in the bronze layer with year, month and day partition."""
    return f"{BRONZE_PATH}/{form.lower()}/year={date.year}/month={date.month:02d}/day={date.day:02d}/{filename}"


def silver_path(form: str, date: datetime.date, filename: str) -> str:
    """Construct the s3/Minio path for a given form, date and filename in the silver layer with year and month partition."""
    filename_prefix = f"day={date.day:02d}"
    return f"silver/{form.lower()}/year={date.year}/month={date.month:02d}/{filename_prefix}_{filename}"
