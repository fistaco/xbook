from enum import Enum

from fuzzywuzzy import process


class SubcategoryId(Enum):
    X1A = 4
    X1B = 5
    X3A = 16534
    X3B = 16533
    BEACH_COURT_1 = 36
    BEACH_COURT_2 = 37
    BEACH_COURT_3 = 38
    BEACH_COURT_4 = 39

    def __str__(self) -> str:
        """Represents this subcategory ID as a human-readable string."""
        return self.name.replace("_", " ").capitalize()

    @staticmethod
    def from_string(s):
        """
        Constructs and returns a subcateogry ID from the given category string
        `s` by fuzzy searching for the best match.

        >>> SubcategoryId.from_string("3a")
        <SubcategoryId.X3A: 16534>
        >>> SubcategoryId.from_string("court 1")
        <SubcategoryId.BEACH_COURT_1: 36>
        """
        match, _ = process.extractOne(s, SUBCATEGORY_ID_STRING_MAP.keys())
        return SUBCATEGORY_ID_STRING_MAP[match]


SUBCATEGORY_ID_STRING_MAP = {
    str(subcategory_id): subcategory_id
    for subcategory_id
    in list(SubcategoryId)
}
