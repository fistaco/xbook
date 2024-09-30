from datetime import datetime, timedelta, timezone
from enum import Enum

from fuzzywuzzy import process

from time_slot_manip import utc_seconds_difference


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
        """Represents this booking tag ID as a human-readable string."""
        return self.name.replace("_", " ").capitalize()
    
    def is_hall_category(self) -> bool:
        """
        Returns whether this booking tag ID is treated as a hall-like entity in X's
        backend.
        """
        return self in [
            BookingTagId.BEACH_VOLLEYBALL_COURT,
            BookingTagId.HALL_X1,
            BookingTagId.HALL_X2,
            BookingTagId.HALL_X3
        ]

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


# Contains constant time windows for booking tag IDs. If a category is not
# present in the map, it either has an unknown value or has to be computed at
# runtime.
BOOKING_TAG_ID_BOOKING_WINDOW_MAP = {
    BookingTagId.GYM: 604800  # 7 days
}


def compute_hall_slot_booking_window(start_str):
    """
    Computes the booking windows for hall-like booking tag IDs, which is equal
    to three days plus the hour at which the time slot commences.

    TODO: Check whether this window assumption is correct

    Arguments:
        `start_str`: A timestamp string representing a slot's start time (UTC).
    """
    start = datetime.strptime(start_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    return 259200 + (start.hour)*3600 + utc_seconds_difference()
