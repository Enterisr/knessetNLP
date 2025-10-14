import argparse
import pandas as pd
from processing.expose_repo import init_repo_server
from processing.df_builder import (
    recreate_utterances_from_df,
)
import faiss
from processing.repo_data import RepoData
from utils.logger_config import get_logger
import os

logger = get_logger(__name__)
DEFAULT_DF_FILE = "filtered_utterances_data.pkl"
DEFAULT_VECTOR_DB_FILE = "committie_index"

def run():
    """Run the Knesset NLP production server with command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Knesset NLP production server")

    parser.add_argument("--committee-index-path", dest="committee_index_path", type=str,
                       help="Custom path to the committee index file",default=DEFAULT_VECTOR_DB_FILE)
    parser.add_argument("--df-path", dest="df_path", type=str,
                       help="Custom path to the filtered DataFrame file",default=DEFAULT_DF_FILE)
    args = parser.parse_args()
    # Validate input files before starting server
    validate_files(args.committee_index_path, args.df_path)
    
    def init_repo_function(_):
        return init_prod_repo(
            committee_index_path=args.committee_index_path,
            df_path=args.df_path,
        )
    
    init_repo_server(
        force_refresh=False,
        init_repo_func=init_repo_function
    )

def validate_files(vector_db_path: str, df_path: str):
    """
    Validate that the required files exist.
    
    Args:
        vector_db_path: Path to the vector database
        df_path: Path to the DataFrame file
        
    Raises:
        FileNotFoundError: If any of the required files doesn't exist
    """
    if not os.path.exists(vector_db_path):
        raise FileNotFoundError(f"Vector database not found at: {vector_db_path}")
    
    if not os.path.exists(df_path):
        raise FileNotFoundError(f"DataFrame file not found at: {df_path}")

def init_prod_repo(committee_index_path:str, df_path:str)->RepoData:
    #assume all of the files are correct
    df = pd.read_pickle(df_path)
    utterances = recreate_utterances_from_df(df)
    logger.info(f"Loaded DataFrame with {len(df)} rows from file and reconstructed {len(utterances)} utterances from DF.")
    logger.info("Loading existing FAISS index from file...")
    index = faiss.read_index(str(committee_index_path))
    logger.info(f"Loaded FAISS index with {index.ntotal} vectors")
   
    return RepoData(index,df)



if __name__ == "__main__":
    run()
