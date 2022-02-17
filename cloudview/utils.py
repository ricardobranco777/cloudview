"""
Helper functions
"""

from datetime import datetime

import timeago

from dateutil import parser
from pytz import utc


def fix_date(date, time_format=None):
    """
    Converts datetime object or string to local time or the
    timezone specified by the TZ environment variable
    """
    if isinstance(date, str):
        # The parser returns datetime objects
        date = parser.parse(date)
    if isinstance(date, datetime):
        # GCP doesn't return UTC dates
        date = utc.normalize(date)
        if time_format is not None:
            return date.astimezone().strftime(time_format)
        return timeago.format(date, datetime.now(tz=utc))
    return ""
