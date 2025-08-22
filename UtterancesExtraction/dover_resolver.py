from rapidfuzz import fuzz
import logging
import json
import re


from logger_config import get_logger

logger = get_logger(__name__)


class DoverResolver:
    def __init__(self, min_ratio_for_rapidfuzz=60):
        min_ratio = min_ratio_for_rapidfuzz
        self.mks = self.load_mks_data()
        self.mks_by_name = self.transfer_mks_to_name_format()
        self.rapidfuzz_cache = {}

    def transfer_mks_to_name_format(self) -> dict:
        mks_by_name = {}
        for key in self.mks.keys():
            new_key = self.mks[key]["FirstName"]+" "+self.mks[key]["LastName"]
            mks_by_name[new_key] = self.mks[key]
        return mks_by_name

    def extract_name_key_from_dover(self, dover_str: str) -> str:
        dover_str = dover_str.replace(' – מ"מ היו"ר', "")
        dover_str = dover_str.replace(' – היו"ר', "")
        dover_str = dover_str.replace('היו"ר ', "")
        dover_str = dover_str.replace('יושב-ראש הכנסת ', "")
        dover_str = dover_str.replace('יו"ר ', "")

        match = re.match(r"^(.*?) \(", dover_str)
        if match:
            name = match.group(1)
        else:
            name = dover_str
        logger.debug(
            f"extracted doverkey: {name} from dover_str: {dover_str}")
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
        return max_mk_key, max_sim_mk, max_ratio

    def resolve_mk(self, speaker: str, mks_in_meeting: list):
        speaker_key = self.extract_name_key_from_dover(
            speaker)
        if speaker_key in mks_in_meeting:
            try:
                mk_meta = self.mks_by_name[speaker_key]
            except KeyError:
                rapidfuzz_match, mk_meta, ratio = self.fallback_to_rapidfuzz_(
                    speaker_key)
                logger.info(
                    f"Rapidfuzz search for {speaker_key}, found: {rapidfuzz_match} with certainty: {ratio}")
            return speaker_key, mk_meta
        return {"speaker_key": None, "mk_meta": None}

    def load_mks_data(self):

        try:
            with open('mks_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(
                "mks_data.json file not found. Returning empty dictionary.")
            return {}
        except json.JSONDecodeError:
            logger.error(
                "Error parsing mks_data.json. Returning empty dictionary.")
            return {}
