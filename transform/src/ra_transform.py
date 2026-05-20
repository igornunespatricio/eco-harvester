# transform/src/ra_transformer.py

import pandas as pd

import transform.config.config_ra_transform as ra_config
from src.base_transformer import BaseTransformer


class RATransformer(BaseTransformer):
    def __init__(self):
        super().__init__(form="RA", config=ra_config)

    def post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        df["sighting_start_datetime"], df["sighting_end_datetime"] = (
            self.build_datetimes(
                date=df["event_date"],
                start_time=df["sighting_start_time"],
                end_time=df["sighting_end_time"],
            )
        )

        df["shutdown_request_datetime"], df["shutdown_datetime"] = self.build_datetimes(
            date=df["event_date"],
            start_time=df["shutdown_request_time"],
            end_time=df["shutdown_time"],
        )
        return df
