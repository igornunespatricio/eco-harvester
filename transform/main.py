import io
import sys
import argparse
import logging
import time
import os
from io import BytesIO
from pathlib import Path
import pandas as pd
from datetime import datetime

dir = Path(__file__).parent.parent
sys.path.append(str(dir))
print("Current sys.path:", sys.path)


from transform.src.ra_transform import RATransformer
from transform.src.rda_transform import RDATransformer

_TRANSFORMER_REGISTRY = {
    "RA": RATransformer,
    "RDA": RDATransformer,
}
from transform.src.base_transformer import BaseTransformer
from utils.storage_client import MinioS3Client

logger = logging.getLogger(__name__)

SOURCE_BUCKET = "raw"
DESTINATION_BUCKET = "silver"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Silver transform")
    p.add_argument(
        "--entity", required=True, type=str, help="RA or RDA", choices=["RA", "RDA"]
    )
    p.add_argument(
        "--interval-start",
        required=True,
        type=str,
        help="Start date of the records to be extracted",
    )
    p.add_argument(
        "--interval-end",
        required=True,
        type=str,
        help="End date of the records to be extracted",
    )
    p.add_argument(
        "--dry-run",
        type=bool,
        default=False,
        help="True to avoid writing to the silver layer. (default: %(default)s)",
    )
    return p.parse_args()


def main() -> None:
    # logging.basicConfig(level=logging.INFO)
    logging.basicConfig(
        level=logging.INFO, format="%(name)s | %(levelname)s | %(message)s"
    )
    args = parse_args()

    logger.info("entity:         %s", args.entity)
    logger.info("interval_start: %s", args.interval_start)
    logger.info("interval_end:   %s", args.interval_end)
    logger.info("dry_run:        %s", args.dry_run)
    logger.info("Starting transform...")

    start = datetime.fromisoformat(args.interval_start).date()
    end = datetime.fromisoformat(args.interval_end).date()
    source_key = f"{str(args.entity).lower()}/bandar_report_{start}_to_{end}.xlsx"
    destionation_key = source_key.replace("xlsx", "parquet")

    logger.info("source_key: %s", source_key)
    client = MinioS3Client(
        endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
    )
    buf: BytesIO = client.get_fileobj(SOURCE_BUCKET, source_key)
    raw_df = pd.read_excel(buf)
    logger.info("Raw shape: %s", raw_df.shape)

    transformer = _TRANSFORMER_REGISTRY[args.entity]()
    clean_df = transformer.run(raw_df)
    logger.info("Clean shape: %s", clean_df.shape)

    if not args.dry_run:
        # TODO: write clean_df to the silver layer
        buffer = io.BytesIO()
        clean_df.to_parquet(buffer, index=False)
        buffer.seek(0)
        client.upload_fileobj(
            fileobj=buffer, bucket_name=DESTINATION_BUCKET, key=destionation_key
        )

    logger.info("Transform completed successfully!")


if __name__ == "__main__":
    main()
