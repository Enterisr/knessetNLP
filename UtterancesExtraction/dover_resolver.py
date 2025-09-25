from rapidfuzz import fuzz
import logging
import json
import re

from UtterancesExtraction.bad_dover_exception import BadDoverException
from utils.logger_config import get_logger
from processing.mk_database import get_mks

logger = get_logger(__name__)


class DoverResolver:
    def __init__(self, min_ratio_for_rapidfuzz=75):
        self.min_ratio = min_ratio_for_rapidfuzz
        self.mks_by_name = self._build_name_index()
        self.rapidfuzz_cache = {}
        self.no_match_person = []

    def _build_name_index(self) -> dict:
        """Build name index from MK data."""
        mks_by_name = {}
        mk_data_instance = get_mks()
        for mk_id, mk_data in mk_data_instance.items():
            if "FirstName" in mk_data and "LastName" in mk_data:
                full_name = f"{mk_data['FirstName']} {mk_data['LastName']}"
                mks_by_name[full_name] = {**mk_data, 'mk_id': mk_id}
        return mks_by_name

    def remove_title_from_dover(self, dover_str: str):
        dover_str = dover_str.replace(' – מ"מ היו"ר', "")
        dover_str = dover_str.replace(' – היו"ר', "")
        dover_str = dover_str.replace('היו"ר ', "")
        dover_str = dover_str.replace('יושב-ראש הכנסת ', "")
        dover_str = dover_str.replace('יו"ר ', "")
        pattern = r"(שר|שרת)\s+\S+"
        dover_str = re.sub(pattern, "", dover_str)
        return dover_str

    def extract_name_key_from_dover(self, dover_str: str) -> str:
        dover_str = self.remove_title_from_dover(dover_str)

        match = re.match(r"^(.*?) \(", dover_str)
        if match:
            name = match.group(1)
        else:
            name = dover_str
        # logger.debug(
        #     f"extracted doverkey: {name} from dover_str: {dover_str}")
        return name

    def fallback_to_rapidfuzz_(self, name: str):
        rapidfuzz_cache_entry = self.rapidfuzz_cache.get(name)
        if rapidfuzz_cache_entry is not None:
            return (rapidfuzz_cache_entry["max_mk_key"],
                    rapidfuzz_cache_entry["max_sim_mk"],
                    rapidfuzz_cache_entry["max_ratio"])

        max_ratio = 0
        max_sim_mk = {}
        max_mk_key = ""
        for mk_key, mk_meta in self.mks_by_name.items():
            ratio = fuzz.token_sort_ratio(name, mk_key)
            if (ratio > max_ratio):
                max_ratio = ratio
                max_sim_mk = mk_meta
                max_mk_key = mk_key
        self.rapidfuzz_cache[name] = {"max_ratio": max_ratio,
                                      "max_sim_mk": max_sim_mk, "max_mk_key": max_mk_key}
        if self.min_ratio > max_ratio:
            raise BadDoverException(f"Can't find mk to match {name}")
        return max_mk_key, max_sim_mk, max_ratio

    def resolve_mk(self, speaker: str, mks_in_meeting: list):
        speaker_key = self.extract_name_key_from_dover(
            speaker)
        if speaker_key in mks_in_meeting:
            mk_meta = self.mks_by_name.get(speaker_key)
            if mk_meta is not None:
                return speaker_key, mk_meta
            try:
                rapidfuzz_match, mk_meta, ratio = self.fallback_to_rapidfuzz_(
                    speaker_key)
                logger.info(
                    f"Rapidfuzz search for {speaker_key}, found: {rapidfuzz_match} with certainty: {ratio}")
                return rapidfuzz_match, mk_meta
            except BadDoverException:
                self.no_match_person.append(speaker_key)
                logger.error(
                    f"Can't find match for {speaker_key} with rapidfuzz match set as a min of {self.min_ratio}")
        return {"speaker_key": None, "mk_meta": None}
