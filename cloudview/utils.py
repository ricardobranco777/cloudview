"""
Helper functions
"""

from datetime import datetime

from dateutil import parser
from dateutil.relativedelta import relativedelta
from pytz import utc


def get_age(date):
    """
    Get age
    """
    age = relativedelta(datetime.now(tz=utc), date)
    string = ""
    if age.years:
        string = f"{age.years}y"
    if age.months:
        string += f"{age.months}M"
    if age.days:
        string += f"{age.days}d"
    if age.hours:
        string += f"{age.hours}h"
    if age.minutes:
        string += f"{age.seconds}s"
    return string


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
        return get_age(date)
    return ""
