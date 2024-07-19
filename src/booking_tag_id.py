from enum import Enum

from fuzzywuzzy import process


class BookingTagId(Enum):
    STRENGTH = 5
    GYM = 28
    BEACH_VOLLEYBALL_COURT = 88
    BODY_POWER = 121
    HALL_X1 = 147
    HALL_X2 = 148
    HALL_X3 = 149
    POWER_KICK = 161

    def __str__(self) -> str:
        """Represents this booking tag ID as a string by """
        return self.name.replace("_", " ").capitalize()

    @staticmethod
    def from_string(s):
        """
        Constructs and returns a booking tag ID from the given category string
        `s` by fuzzy searching for the best match.

        >>> BookingTagId.from_string("gYm")
        <BookingTagId.GYM: 28>
        >>> BookingTagId.from_string("beach")
        <BookingTagId.BEACH_VOLLEYBALL_COURT: 88>
        """
        match, _ = process.extractOne(s, BOOKING_TAG_ID_STRING_MAP.keys())
        return BOOKING_TAG_ID_STRING_MAP[match]


BOOKING_TAG_ID_STRING_MAP = {
    str(booking_tag_id): booking_tag_id
    for booking_tag_id
    in list(BookingTagId)
}
