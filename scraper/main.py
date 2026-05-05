import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from io import BytesIO
import logging

dir = Path(__file__).parent.parent
sys.path.append(str(dir))
print("Current sys.path:", sys.path)

from src.bandar_scraper import BandarScraper
from utils.storage_client import MinioS3Client

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser()
parser.add_argument("--interval-start", type=str, default=datetime.now().isoformat())
parser.add_argument("--interval-end", type=str, default=datetime.now().isoformat())
parser.add_argument("--animals", type=str, default="all_records")
parser.add_argument("--basins", type=str, default="all_records")
parser.add_argument("--form", type=str, default="RA")
args = parser.parse_args()

print("Interval-start:", args.interval_start)
print("Interval-end:", args.interval_end)

client = MinioS3Client(
    endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
    access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
    secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
)

bandar = BandarScraper()

bandar.authenticate()

interval_start = datetime.fromisoformat(args.interval_start)
interval_end = datetime.fromisoformat(args.interval_end)

xlsx_bytes = bandar.export_report(
    date_start=interval_start,
    date_end=interval_end,
    animals=args.animals,
    basins=args.basins,
    form=args.form,
)

if xlsx_bytes is None:
    logger.info("Nothing to export, skipping file upload")
else:
    fileobj = BytesIO(xlsx_bytes) if isinstance(xlsx_bytes, bytes) else xlsx_bytes
    client.upload_fileobj(
        fileobj=fileobj,
        bucket_name="raw",
        key=f"{str(args.form).lower()}/bandar_report_{interval_start}_to_{interval_end}.xlsx",
    )
