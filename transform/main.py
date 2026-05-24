import io
import sys
import argparse
import logging
import time
import os
from io import BytesIO
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta, timezone

dir = Path(__file__).parent.parent
sys.path.append(str(dir))
print("Current sys.path:", sys.path)


from utils.storage_client import MinioS3Client
from utils.utility_functions import str_to_bool, bronze_path, silver_path
from transform.src.ra_transform import RATransformer
from transform.src.rda_transform import RDATransformer

_TRANSFORMER_REGISTRY = {
    "RA": RATransformer,
    "RDA": RDATransformer,
}

BUCKET_NAME = os.getenv("BUCKET")

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Silver transform")
    p.add_argument(
        "--entity", required=True, type=str, help="RA or RDA", choices=["RA", "RDA"]
    )
    p.add_argument(
        "--date", type=str, default=datetime.now(timezone.utc).date().isoformat()
    )
    p.add_argument(
        "--dry-run",
        type=str_to_bool,
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
    logger.info("date:           %s", args.date)
    logger.info("dry_run:        %s", args.dry_run)
    logger.info("Starting transform...")

    client = MinioS3Client(
        endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.getenv("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
    )

    # files = client.list_partition_files(
    #     bucket_name=BUCKET_NAME,
    #     partition_prefix=bronze_path(
    #         form=args.entity, date=datetime.fromisoformat(args.date).date(), filename=""
    #     ),
    # )
    # for file in files:
    #     logger.info("Found file: %s", file)

    latest_file_dict = client.get_latest_file(
        bucket_name=BUCKET_NAME,
        partition_prefix=bronze_path(
            form=args.entity, date=datetime.fromisoformat(args.date).date(), filename=""
        ),
    )
    if not latest_file_dict:
        logger.warning(f"No files found for entity {args.entity} on date {args.date}")
        return
    logger.info("Latest file: %s", latest_file_dict)
    buf: BytesIO = client.get_fileobj(
        bucket_name=BUCKET_NAME, key=latest_file_dict["Key"]
    )
    raw_df = pd.read_excel(buf)
    logger.info("Raw shape: %s", raw_df.shape)

    transformer = _TRANSFORMER_REGISTRY[args.entity]()
    clean_df = transformer.run(raw_df)
    logger.info("Clean shape: %s", clean_df.shape)
    key = silver_path(
        form=args.entity,
        date=datetime.fromisoformat(args.date).date(),
        filename="transformed.parquet",
    )
    if not args.dry_run:
        buffer = io.BytesIO()
        clean_df.to_parquet(buffer, index=False)
        buffer.seek(0)
        client.upload_fileobj(fileobj=buffer, bucket_name=BUCKET_NAME, key=key)

    logger.info("Transform completed successfully!")


if __name__ == "__main__":
    main()
