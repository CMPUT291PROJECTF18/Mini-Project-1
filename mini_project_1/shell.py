#!/usr/bin/python
# -*- coding: utf-8 -*-

"""Main command shell for mini-project-1"""

import argparse
import sys
import cmd
import sqlite3
from getpass import getpass
from logging import getLogger

import pendulum

from mini_project_1.loginsession import LoginSession

__log__ = getLogger(__name__)


def logged_in(f):
    """Annotation to check if someone is logged in before attempting a
    command in the :class:`.MainProjectShell`"""
    def wrapper(*args):
        if args[0].login_session:
            return f(*args)
        else:
            __log__.error("you must be logged in to use this function")
    return wrapper


class MiniProjectShell(cmd.Cmd):
    """Main shell for mini-project-1"""
    intro = \
        "Welcome to mini-project-1 shell. Type help or ? to list commands\n"
    prompt = "mini-project-1>"
    login_session: LoginSession = None

    def __init__(self, database: sqlite3.Connection):
        """Initialize the mini-project-1 shell

        :param database: :class:`sqlite3.Connection` to the database to
        interact with the mini-project-1 shell
        """
        super().__init__()
        self.database = database

    def cmdloop(self, intro=None):
        # start a login command at start.
        self.do_login(None)
        super().cmdloop()

    # ===============================
    # Shell command definitions
    # ===============================

    def do_login(self, arg):
        """Login to the mini-project-1 database: login"""
        if self.login_session:
            __log__.error("already logged in")
        else:
            username = str(input("username: "))
            password = getpass("password: ")
            self.login(username, password)
            while not self.login_session:
                self.do_login(None)

    @logged_in
    def do_logout(self, arg):
        """Logout to the mini-project-1 database: logout"""
        self.logout()

    def do_exit(self, arg):
        """Logout (if needed) and exit out of the mini-project-1 shell: exit"""
        if self.login_session:
            self.logout()
        __log__.info("exiting mini-project-1 shell")
        self.database.close()
        return True

    @logged_in
    def do_offer_ride(self, arg):
        """Offer a ride"""
        # TODO:

    @logged_in
    def do_search_rides(self, arg):
        """Search for ride"""
        # TODO:

    @logged_in
    def do_list_bookings(self, arg):
        """List all the bookings that the user offers"""
        cur = self.database.cursor()
        list_bookings = 'SELECT DISTINCT bookings.* ' \
                        'FROM bookings, rides ' \
                        'WHERE rides.driver=? ' \
                        'AND rides.rno=bookings.rno;'
        cur.execute(list_bookings, (self.login_session.get_email(),))
        rows = cur.fetchall()
        for row in rows:
            print(row)

    @logged_in
    def do_book_member(self, arg):
        """Book other members on a ride"""
        # TODO:

    @logged_in
    def do_cancel_booking(self, arg):
        """Cancel a booking"""
        cur = self.database.cursor()
        parser = get_cancel_booking_parser()
        try:
            args = parser.parse_args(arg.split())
            cur.execute("DELETE FROM bookings WHERE bno = ? AND email = ?", (args.bno, self.login_session.get_email(),))
            # TODO: Spit out messages for ineffective commands
            # TODO: e.g. User has no rides, bno and email mismatch, etc.
        except ShellArgumentException:
            __log__.error("invalid cancel_booking argument")

    def help_cancel_booking(self):
        """Cancel a booking"""
        parser = get_cancel_booking_parser()
        parser.print_help()

    @logged_in
    def do_post_ride_request(self, arg):
        """Post a ride request"""
        parser = get_post_ride_request_parser()
        try:
            args = parser.parse_args(arg.split())

            # generate a new rid
            max_rid = self.database.execute("select max(r.rid) from requests r").fetchone()[0]
            if not max_rid:
                max_rid = 0
            rid = 1 + int(max_rid)

            # create and insert the new ride request
            self.database.execute(
                "INSERT INTO requests VALUES (?, ?, ?, ?, ?, ?)",
                (rid, self.login_session.get_email(), args.date.strftime("%Y-%m-%d"), args.pickup, args.dropoff, args.price))
            self.database.commit()
        except ShellArgumentException:
            __log__.error("invalid post_ride_request argument")

    def help_post_ride_request(self):
        """Post a ride request's parsers help message"""
        parser = get_post_ride_request_parser()
        parser.print_help()

    @logged_in
    def do_list_ride_requests(self, arg):
        """List all the user's ride requests"""
        cur = self.database.cursor()
        list_requests = 'SELECT DISTINCT * ' \
                        'FROM requests ' \
                        'WHERE email=?;'
        cur.execute(list_requests, (self.login_session.get_email().lower(),))
        rows = cur.fetchall()
        for row in rows:
            print(row)

    @logged_in
    def do_search_ride_requests(self, arg):
        """Search for a ride request"""
        # TODO:

    @logged_in
    def do_delete_ride_request(self, arg):
        """Delete a ride request"""
        # TODO:

    # ===============================
    # Shell functionality definitions
    # ===============================

    @logged_in
    def logout(self):
        """Logout method

        Set the shell's ``login_session`` to :obj:`None`.
        """
        email = self.login_session.get_email()
        self.login_session = None
        __log__.info("logged out user: {}".format(email))

    def login(self, email: str, password: str):
        """Login method

        Check if a :class:`LoginSession` already exists for the shell if not
        attempt to login with the given email and password.

        If the login attempt is successful set the shell's ``login_session``
        to the newly created :class:`LoginSession`.
        """
        if self.login_session:
            __log__.error("already logged in as user: {}".format(self.login_session.get_email()))
        else:
            user_hit = self.database.execute("select email, pwd from members where email = ? and pwd = ?",
                                             (email.lower(), password)).fetchone()
            if user_hit:
                self.login_session = LoginSession(user_hit[0], user_hit[1])
                __log__.info("logged in user: {}".format(user_hit[0]))
            else:
                __log__.warning("invalid login: bad username/password")


class ShellArgumentException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)


class ShellArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        raise ShellArgumentException(message)


def price(price_string: str) -> int:
    price = int(price_string)
    if price < 0:
        raise argparse.ArgumentTypeError(
            "invalid price: {} (please choose a non negative price)".format(
                price_string
            )
        )
    return price


def date(date_str: str) -> pendulum.DateTime:
    return pendulum.parse(date_str)


def get_post_ride_request_parser() -> ShellArgumentParser:
    parser = ShellArgumentParser(
        add_help=False,
        description="Post a ride request")

    parser.add_argument("date", type=date,
                        help="Date the ride should start on")
    parser.add_argument("pickup",
                        help="The location code for the pickup location of the ride")
    parser.add_argument("dropoff",
                        help="The location code for the dropoff location of the ride")
    parser.add_argument("price", type=price,
                        help="The maximum amount you are willing to pay per seat for the ride")
    return parser


def get_cancel_booking_parser() -> ShellArgumentParser:
    parser = ShellArgumentParser(
        add_help=False,
        description="Cancel a Booking")

    parser.add_argument("bno", type=int,
                        help="The booking identification number")
    return parser
