# transform/src/ra_transformer.py

import transform.config.config_ra_transform as ra_config
from src.base_transformer import BaseTransformer


class RATransformer(BaseTransformer):
    def __init__(self):
        super().__init__(form="RA", config=ra_config)
