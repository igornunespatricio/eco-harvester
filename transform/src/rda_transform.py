# transform/src/rda_transformer.py

import pandas as pd
import transform.config.config_rda_transform as rda_config
from src.base_transformer import BaseTransformer


class RDATransformer(BaseTransformer):
    def __init__(self):
        super().__init__(form="RDA", config=rda_config)

    def post_process(self, df: pd.DataFrame) -> pd.DataFrame:
        df["total_activity_interruption_min"] = self.hhmm_to_minutes(
            df["total_activity_interruption_time"]
        )
        df = df.drop(columns=["total_activity_interruption_time"])
        return df
