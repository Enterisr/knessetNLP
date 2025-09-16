# pojo to hold repo data
from faiss import IndexFlatIP
import pandas as pd


class RepoData:
    def __init__(self, database: IndexFlatIP, df: pd.DataFrame, utterances=[]) -> None:
        self.database = database
        self.utternaces = utterances
        self.df = df
