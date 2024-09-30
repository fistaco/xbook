#!/usr/bin/env python
import argparse
import getpass
import json
import os
import urllib3

from auth import AuthMethod
from booking import login_and_book_slot
from booking_tag_id import BookingTagId
from constants import BEACH_VOLLEYBALL_COURT_PRODUCT_IDS
from subcategory_id import SubcategoryId

# The certificate for x.tudelft.nl is untrusted, which produces many warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def parse_args():
    parser = argparse.ArgumentParser(
        prog="xbook", description="Book an activity time slot at X.")

    parser.add_argument("date", metavar="date", type=str,
        help="The date on which you want to book a time slot. Example: 2024-01-13")
    parser.add_argument("hour", metavar="hour", type=int,
        help="The hour at which your desired slot commences. Example: 09")

    parser.add_argument("--password", metavar="password", type=str, nargs=1,
        help="The password you use to log in to X's website.")
    parser.add_argument("--utc", action="store_true",
        help="Whether or not the provided date and hour are in UTC.")

    parser.add_argument("--booking-category", "-b", type=str,
        help="The category for which xbook should book a slot.", default="gym")
    parser.add_argument("--court", "-c", type=int, choices=[1, 2, 3, 4],
        help="The beach volleyball court to book.", default=None)

    return parser.parse_args()


def load_config():
    """
    Returns a tuple of variables containing the values from "./config.json" and
    a `username` variable containing the `netid` or `email` according to the
    configured `auth_method`.
    """
    config_path = f"{os.path.dirname(__file__)}/../config.json"
    with open(config_path, "r") as f:
        config = json.load(f)

        netid = config["netid"]
        email = config["email"]
        member_id = config["member_id"]
        if member_id:
            member_id = int(member_id)
        auth_method = AuthMethod[config["auth_method"].upper()]
        username = netid if auth_method == AuthMethod.TUD_SSO \
            else email

    return (username, member_id, auth_method)


def process_args(args):
    """
    Processes and returns the given command line arguments for usage during
    booking.
    """
    tag_id = BookingTagId.from_string(args.booking_category).value

    subcategory_id = None
    if args.court:
        subcategory_id = BEACH_VOLLEYBALL_COURT_PRODUCT_IDS[args.court]
    if tag_id != BookingTagId.GYM.value:
        subcategory_id = SubcategoryId.from_string(args.booking_category).value

    return (tag_id, subcategory_id)


if __name__ == "__main__":
    args = parse_args()
    (username, member_id, auth_method) = load_config()

    password = getpass.getpass("Password for X login: ") if not args.password \
        else args.password[0]

    (tag_id, subcategory_id) = process_args(args)

    login_and_book_slot(
        username, password, member_id, auth_method, args.date, args.hour,
        args.utc, tag_id, subcategory_id
    )
