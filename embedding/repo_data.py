# pojo to hold repo data
from faiss import IndexFlatIP


class RepoData:
    def __init__(self, database: IndexFlatIP, utternaces: list[str],) -> None:
        self.database = database
        self.utternaces = utternaces
