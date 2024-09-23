from datetime import datetime, timedelta


def date_and_hour_to_time_slot_str(date_str, start_hour, in_utc=False,
                                   with_millis=True):
    """
    Uses the given date string and hour to generate a time slot string for X
    formatted as "YYYY-MM-DDTHH:MM:SS.MSSZ", e.g. "2021-12-25T17:59:59.999Z".

    Arguments"
        `date_str`: A date string formatted as YYYY-MM-DD.
        `start_hour`: The slot's start hour provided as an integer 6 < i < 24.
        `in_utc`: Whether the given arguments are already in UTC.
        `with_millis`: Whether the returned string should end with ".000Z".
    """
    if not in_utc:
        start_hour = apply_utc_diff(start_hour)

    base_str = f"{date_str}T{str(start_hour).zfill(2)}:00:00"

    if with_millis:
        return f"{base_str}.000Z"

    return base_str


def apply_utc_diff(hour):
    """
    Converts the given `hour` to UTC based on the difference between the user's
    timezone and UTC.

    Note that this naive implementation does not account for hour differences
    that leak into the previous or next day.
    """
    return hour + (datetime.utcnow().hour - datetime.now().hour)


def seconds_diff(start_str, end_str):
    """
    Computes and returns the difference in hours between the two given time
    strings."""
    start = start_str if isinstance(start_str, datetime) \
        else datetime.strptime(start_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    end = datetime.strptime(end_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    return int((end - start).total_seconds())
