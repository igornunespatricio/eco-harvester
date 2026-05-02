from src.bandar_scraper import BandarScraper
import os

print(BandarScraper)
# print(os.getenv("EXECUTION_DATE", "no execution date"))

import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--execution-date", type=str)
parser.add_argument("--interval-start", type=str)
parser.add_argument("--interval-end", type=str)
parser.add_argument("--logical-date", type=str)
args = parser.parse_args()

print(args.execution_date)
print(args.interval_start)
print(args.interval_end)
print(args.logical_date)
