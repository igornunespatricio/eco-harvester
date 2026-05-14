import sys
import argparse
import logging
import time
from pathlib import Path

dir = Path(__file__).parent.parent
sys.path.append(str(dir))
print("Current sys.path:", sys.path)

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Silver transform")
    p.add_argument("--entity", required=True, type=str)
    p.add_argument("--interval-start", required=True, type=str)
    p.add_argument("--interval-end", required=True, type=str)
    p.add_argument("--dry-run", type=bool, default=False)
    return p.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = parse_args()

    logger.info("entity:         %s", args.entity)
    logger.info("interval_start: %s", args.interval_start)
    logger.info("interval_end:   %s", args.interval_end)
    logger.info("dry_run:        %s", args.dry_run)
    logger.info("Starting transform...")
    logger.info("Simulating work by sleeping for 600 seconds...")
    time.sleep(600)
    logger.info("Transform completed successfully!")


if __name__ == "__main__":
    main()
