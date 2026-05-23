import sys
import os
import argparse
from pathlib import Path
from datetime import datetime, timezone
from io import BytesIO
import logging
from dotenv import load_dotenv
import pandas as pd

dir = Path(__file__).parent.parent
sys.path.append(str(dir))
print("Current sys.path:", sys.path)

load_dotenv(dotenv_path=dir / ".env")

from src.bandar_scraper import BandarScraper
from utils.storage_client import MinioS3Client
from utils.utility_functions import (
    bronze_path,
    df_to_parquet_bytes,
    add_ingested_at,
)

BUCKET_NAME = "netuno"

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument(
    "--date", type=str, default=datetime.now(timezone.utc).date().isoformat()
)
parser.add_argument("--animals", type=str, default="all_records")
parser.add_argument("--basins", type=str, default="all_records")
parser.add_argument("--form", type=str, default="RA")
parser.add_argument("--per", type=str, default="2500")
parser.add_argument("--timeout", type=int, default=300)
args = parser.parse_args()

client = MinioS3Client(
    endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ROOT_USER", "wrongkey"),
    secret_key=os.getenv("MINIO_ROOT_PASSWORD", "wrongkey"),
)

bandar = BandarScraper(
    timeout=args.timeout,
)

bandar.authenticate()

scraping_date = datetime.fromisoformat(args.date).date()


logger.info(f"Scraping date: {scraping_date}")

xlsx_bytes = bandar.export_report(
    date_start=scraping_date,
    date_end=scraping_date,
    animals=args.animals,
    basins=args.basins,
    form=args.form,
    per=args.per,
)

if xlsx_bytes is None:
    logger.info("Nothing to export, skipping file upload")
else:
    df = pd.read_excel(BytesIO(xlsx_bytes), engine="openpyxl")
    df = add_ingested_at(df)
    parquet_bytes = df_to_parquet_bytes(df)
    fileobj = BytesIO(parquet_bytes)
    key = bronze_path(
        args.form,
        scraping_date,
        f"run_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H-%M-%S')}.parquet",
    )
    client.upload_fileobj(
        fileobj=fileobj,
        bucket_name=BUCKET_NAME,
        key=key,
    )
    logger.info(f"File uploaded to bucket '{BUCKET_NAME}' with key: {key}")
