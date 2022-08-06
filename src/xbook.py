#!/usr/bin/env python
import argparse
import getpass
import json
import os
import urllib3

from auth import AuthMethod
from booking import login_and_book_slot

# The certificate for x.tudelft.nl is untrusted, which produces many warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def parse_args():
    parser = argparse.ArgumentParser(
        prog="xbook", description="Book a fitness time slot at X.")

    parser.add_argument("date", metavar="date", type=str,
        help="The date on which you want to book a time slot (YYYY-MM-DD).")
    parser.add_argument("hour", metavar="hour", type=int,
        help="The hour at which your desired slot commences.")
    parser.add_argument("--password", metavar="password", type=str, nargs=1,
        help="The password you use to log in to X's website.")
    parser.add_argument("--utc", action="store_true",
        help="Whether or not the provided date and hour are in UTC.")

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


if __name__ == "__main__":
    args = parse_args()
    (username, member_id, auth_method) = load_config()

    passw = getpass.getpass("Password for X login: ") if not args.password \
        else args.password[0]

    login_and_book_slot(
        username, passw, member_id, auth_method, args.date, args.hour, args.utc
    )
