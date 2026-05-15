# transform/src/ra_transformer.py

from src.base_transformer import BaseTransformer


class RATransformer(BaseTransformer):
    def __init__(self):
        super().__init__(form="RA")
