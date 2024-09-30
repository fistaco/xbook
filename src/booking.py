from datetime import datetime
import json
import requests
import time

from auth import auth, terminate_session
from booking_tag_id import (BookingTagId, BOOKING_TAG_ID_BOOKING_WINDOW_MAP,
    compute_hall_slot_booking_window)
from time_slot_manip import date_and_hour_to_time_slot_str, seconds_diff


def login_and_book_slot(uname, passw, mem_id, auth_meth, date, hour, in_utc,
                        tag_id=BookingTagId.GYM.value, subcategory_id=None):
    """
    Authenticates to X with the given credentials and attempts to book a time
    slot corresponding to the given start `hour` on the given `day` for the
    booking category corresponding to the given `tag_id`.
    """
    day_start = date_and_hour_to_time_slot_str(date, 0, in_utc=True)
    day_end = date_and_hour_to_time_slot_str(date, 23, in_utc=True)
    slot_str = date_and_hour_to_time_slot_str(date, hour, in_utc=in_utc)

    attempt_booking(
        slot_str, day_start, day_end, mem_id, uname, passw, auth_meth, tag_id,
        subcategory_id
    )


def attempt_booking(slot_str, start_str, end_str, member_id, username, passw,
                    auth_method, tag_id, subcategory_id=None, interval=1):
    """
    Continuously checks in intervals of `interval` seconds if the time slot
    with the given `slot_str` is available and attempts to book it if it is. If
    the booking fails, the attempts resume.

    `start_str` and `end_str` determine the time range within which the search
    takes place.
    """
    print(f"Checking availability for gym slot at {slot_str}.")

    prev_time = time.time()
    while True:
        t = time.time()
        if t - prev_time < interval:
            continue

        prev_time = t  # Update time regardless of rest of loop

        slots = booking_schedule(start_str, end_str, tag_id)
        if slots is None:
            continue

        slot = find_slot(slot_str, slots, ignore_availability=False,
                         subcategory_id=subcategory_id)
        if not slot_is_bookable(slot):
            continue

        (session, token, mem_id_from_auth) = auth(username, passw, auth_method)
        if mem_id_from_auth is not None:
            member_id = mem_id_from_auth
        booked = book_slot(slot, member_id, session, token)

        if not booked:
            print(f"Failed to book slot at {slot_str}. Resuming attempts.")
            continue

        print(f"Succesfully booked slot at {slot_str} (UTC)!")
        print(f"Terminating session and exiting.")
        terminate_session(session)
        break


def booking_schedule(start_str, end_str, tag_id=BookingTagId.GYM.value):
    """
    Obtains the list of available bookings between the given `start_str` and
    `end_str` datetimes, which should be formatted as
    "YYYY-MM-DDTHH:00:00.000Z", e.g., 2022-03-07T15:00:00.000Z for 7 March,
    2022, 15:00.

    Note that X's backend stores timestamps in UTC (GMT+0), so any requests
    with time-related parameters should be formatted as such.
    """
    now_str = datetime.today().strftime("%Y-%m-%dT%H:%M:%S")
    url = f"https://backbone-web-api.production.delft.delcom.nl/bookable-s" + \
          f"lots?s=%7B%22startDate%22:%22{start_str}%22,%22endDate%22" + \
          f":%22{end_str}%22,%22tagIds%22:%7B%22$in%22:%5B{tag_id}%5D%7D,%" + \
          f"22availableFromDate%22:%7B%22$gt%22:%22{now_str}%22%7D,%22" + \
          f"availableTillDate%22:%7B%22$gte%22:%22{now_str}%22%7D%7D"

    try:
        data = json.loads(requests.get(url).text)["data"]
    except Exception as e:
        print(e)
        return None

    return data


def find_slot(time_slot_str, slots, ignore_availability=False,
              subcategory_id=None):
    """
    Finds a time slot starting at the given `time_slot_str` within `slots`.
    Can return `None` to keep on searching even when no slots are found.

    Arguments:
        `time_slot_str`: An X timestamp formatted as YYYY-MM-DDTHH:MM:SS.MSSZ
        `slots`: A list of dictionaries in which each dictionary at least
                 has the keys "bookingId", "bookableProductId",
                 "linkedProductId", "startDate", "endDate", "isAvailable",
                 "booking", and "product".
    """
    for slot in slots:
        if slot_match(slot, time_slot_str, subcategory_id):
            return slot

    if ignore_availability:
        return None

    print(f"Could not find a slot starting at {time_slot_str}. Exiting.")
    exit(0)


def slot_match(slot, time_slot_str, subcategory_id=None):
    """
    Determines and returns whether the given `slot` matches the filter defined
    by the given start time and category information.
    """
    return slot["startDate"] == time_slot_str and \
        subcategory_id is None or slot["bookableProductId"] == subcategory_id


def slot_is_bookable(slot, booking_tag_id=BookingTagId.GYM):
    """
    Determines and returns whether a slot is bookable by checking its
    availability and the remaining time until participants can start attempting
    to book.
    """
    seconds_until_slot = seconds_diff(datetime.utcnow(), slot["startDate"])

    booking_window = get_booking_window(booking_tag_id, slot)
    slot_within_booking_window = seconds_until_slot < booking_window

    return slot["isAvailable"] and slot_within_booking_window


def get_booking_window(booking_tag_id=BookingTagId.GYM, slot=None):
    """
    Returns the number of seconds that X allows between the booking time and
    start time for a time slot of the given `booking_tag_id`.
    """
    # Some categories can only be booked 3 days ahead of time, starting from
    # 00:00 rather than from the exact time of each individual slot
    if booking_tag_id.is_hall_category() and slot is not None:
        return compute_hall_slot_booking_window(slot["startDate"])

    # Assume an unreasonably large window by default for unknown categories
    return BOOKING_TAG_ID_BOOKING_WINDOW_MAP.get(booking_tag_id, 31536000)


def book_slot(slot, member_id, session, token=None):
    """
    Books the fitness time `slot` for the user with the given `member_id`.

    Returns whether or not the booking was successful.
    """
    print("Attempting to book slot...")

    url = "https://backbone-web-api.production.delft.delcom.nl/participations"
    payload = {
        # "organizationId": null,
        "memberId": member_id,
        "bookingId": slot.get("bookingId"),
        # "primaryPurchaseMessage": null,
        # "secondaryPurchaseMessage": null,
        "params": {
            "startDate": slot["startDate"],
            "endDate": slot["endDate"],
            "bookableProductId": slot["bookableProductId"],
            "bookableLinkedProductId": slot["linkedProductId"],
            "bookingId": slot.get("bookingId"),
            "invitedMemberEmails": [],
            "invitedGuests": [],
            "invitedOthers": []
            # "primaryPurchaseMessage": null,
            # "secondaryPurchaseMessage": null
        }
        # "dateOfRegistration": null
    }

    session.headers["authorization"] = f"Bearer {token}"
    r = session.post(url, json=payload)

    return r.status_code < 300


def cancel_slot(slot_id, session):
    """
    Cancels the time slot with the given `slot_id` that can be found in
    `reservations['data'][n]['participations']['id']` for reservation `n` for
    the authenticated user.

    Returns whether the booking was successfully cancelled.
    """
    url = f"https://backbone-web-api.production.delft.delcom.nl/participations/{slot_id}"
    r = session.delete(url)

    return r.ok
