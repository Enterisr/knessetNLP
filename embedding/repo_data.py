# pojo to hold repo data
from faiss import IndexFlatIP
import pandas as pd


class RepoData:
    def __init__(self, database: IndexFlatIP, df: pd.DataFrame) -> None:
        self.database = database
        self.df = df
