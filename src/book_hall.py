#!/usr/bin/env python3
import code
import getpass
import requests

from auth import AuthMethod
from booking import login_and_book_slot, booking_schedule
from booking_tag_id import BookingTagId
from time_slot_manip import date_and_hour_to_time_slot_str


# Note: all gym slots have a 'booking' field, but that's not necessarily the case for other categories -> how do you book those, then?
# -> All slots seem to be equally bookable on the given date
# -> Different courts are identified by different values for the 'bookableProductId' field: values 36-39 corresponds to courts 1-4
# -> Booking request is done with a bookableLinkedProductId, startDate, endDate and bookableProductId.
date = "2024-07-20"
day_start = date_and_hour_to_time_slot_str(date, 0, in_utc=True)
day_end = date_and_hour_to_time_slot_str(date, 23, in_utc=True)
slots = booking_schedule(day_start, day_end, BookingTagId.BEACH_VOLLEYBALL_COURT.value)


# === X1 Hall product request ===
# Can book up to 72 hours in advance
# Auth is actually not required for this request
# url = "https://backbone-web-api.production.delft.delcom.nl/products/20045?join=translations&join=childProducts&join=childProducts.translations&join=linkedSubscriptions&join=linkedSubscriptions.translations&join=parentBookableProducts&join=parentBookableProducts.translations&join=documents&join=childProducts.documents&join=surveyParents"

# r = requests.get(url, verify=False)

# Interesting fields
# bookable: false
# availableAsBookableSlot: true
# bookableSlotsMinutesAhead: 4320
# "adminCode": "803300"
# "price": 39

# === Bookable slots ===
# Doesn't require auth
# url = 'https://backbone-web-api.production.delft.delcom.nl/bookable-slots?s={"startDate":"2024-07-17T22:00:00.000Z","endDate":"2024-07-18T22:00:00.000Z","tagIds":{"$in":[24]},"availableFromDate":{"$gt":"2024-07-17T19:11:29.254Z"},"availableTillDate":{"$gte":"2024-07-17T22:00:00.000Z"}}&join=linkedProduct&join=linkedProduct.translations&join=product&join=product.translations' # Same as URL for gym, but with tagIds 24 instead of 22
# tagId 20 is for outdoor facilities, though you'll have to filter on slot['linkedProduct']['description'] == 'Room Rental - Beach Volleyball Court' or slot['linkedProduct']['productCode'] == 'GTI-GTI105'
# Even better: just use tagId 88 to target beach volleyball courts exclusively
# r = requests.get(url, verify=False)

# === Booking ===
# For the gym, a booking requires a bookableProductId, linkedProductId, and bookingId
login_and_book_slot("fiske_schijlen@hotmail.com", getpass.getpass("password: "), None, AuthMethod.OTHER, "2024-07-20", 20, False, BookingTagId.BEACH_VOLLEYBALL_COURT.value)
# code.interact(local=locals())
