from typing import Iterable, Iterator


# be careful not to make the context more important than the text
MAX_SUBJECT_LEN = 20
MAX_COMMITIEE_LEN = 20
METADATA_FORMAT = "[sub:{subject} comm:{comm}]{text}"


def embed_metadata_in_utterance(
    utter_list: list[str], file_data: dict
):
    for u in utter_list:
        s = METADATA_FORMAT.format(
            subject=file_data["subject"][:MAX_SUBJECT_LEN],
            comm=file_data["committee"][:MAX_COMMITIEE_LEN],
            text=u
        )
        yield s


def strip_metadata_one(s: str) -> str:
    if s and s[0] == '[':
        i = s.find(']')
        if i != -1:
            return s[i+1:].lstrip()
    return s


def strip_metadata_many(utter_list: Iterable[str]) -> Iterator[str]:
    for u in utter_list:
        yield strip_metadata_one(u)
