"""
Simple MK data wrapper - replaces the global MKS variable pattern.

This module provides a simple wrapper around MK data loading,
making it more Pythonic without overcomplicating things.

Usage:
    from processing.mk_database import get_mks
    
    # Get the MK data instance (singleton, no globals!)
    mks = get_mks()
    
    # Get MK data by ID
    mk_data = mks.get("30874")  # Returns dict or None
    
    # Check if MK exists
    if "30874" in mks:
        print("MK exists")
    
    # Iterate over all MKs
    for mk_id, mk_data in mks.items():
        print(f"MK {mk_id}: {mk_data['FirstName']} {mk_data['LastName']}")
"""

import json
from pathlib import Path
from typing import Dict, Optional, Union
from utils.logger_config import get_logger

logger = get_logger(__name__)


class MKData:
    """
    Simple wrapper for MK data that replaces the global MKS variable.
    Just loads the data once and provides a clean interface.
    """

    _instance: Optional['MKData'] = None

    def __new__(cls) -> 'MKData':
        """Singleton pattern - only create one instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Load MK data if not already loaded."""
        if hasattr(self, '_data'):
            return

        self._data: Dict[str, Dict] = {}
        self._load_data()

    def _load_data(self) -> None:
        """Load MK data from JSON file."""
        project_root = Path(__file__).parent.parent
        mks_path = project_root / "mks_data.json"

        try:
            with open(mks_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
            logger.info(
                f"Successfully loaded {len(self._data)} MKs from {mks_path}")
        except FileNotFoundError:
            logger.error(f"MKs data file not found at {mks_path}")
            self._data = {}
        except json.JSONDecodeError:
            logger.error(f"Error parsing MKs JSON data at {mks_path}")
            self._data = {}

    def get(self, mk_id: Union[str, int], default=None) -> Optional[Dict]:
        """Get MK data by ID (same interface as dict.get())."""
        return self._data.get(str(mk_id), default)

    def __getitem__(self, mk_id: Union[str, int]) -> Dict:
        """Allow dict-like access: mk_data[mk_id]."""
        return self._data[str(mk_id)]

    def __contains__(self, mk_id: Union[str, int]) -> bool:
        """Allow 'in' operator: mk_id in mk_data."""
        return str(mk_id) in self._data

    def keys(self):
        """Get all MK IDs."""
        return self._data.keys()

    def values(self):
        """Get all MK data."""
        return self._data.values()

    def items(self):
        """Get all (mk_id, mk_data) pairs."""
        return self._data.items()


# Function to get the MK data instance - no global variables!
def get_mks() -> MKData:
    """Get the MK data instance (singleton)."""
    return MKData()
