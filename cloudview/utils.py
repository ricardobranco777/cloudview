"""
Helper functions
"""

import traceback
from datetime import datetime

from dateutil import parser
from dateutil.relativedelta import relativedelta
from pytz import utc


def exception(exc: Exception, trace=False) -> str:
    """
    Describe exception with traceback
    """
    return "".join([
        traceback.format_exc() if trace else "",
        f"{exc.__class__.__name__}: {exc}",
    ])


def get_age(date: datetime):
    """
    Get age
    """
    age = relativedelta(datetime.now(tz=utc), date)
    string = "".join([
        f"{age.years}y" if age.years else "",
        f"{age.months}M" if age.months else "",
        f"{age.days}d" if age.days else "",
        f"{age.hours}h" if age.hours else "",
        f"{age.minutes}m" if age.minutes else "",
        f"{age.seconds}s" if age.seconds else "",
    ])
    if string == "":
        string = "0s"
    return string


def utc_date(date: str) -> datetime:
    """
    return UTC normalized datetime object from date string
    """
    return utc.normalize(parser.parse(date))


def fix_date(date: datetime, time_format=None):
    """
    Converts datetime object to local time or the
    timezone specified by the TZ environment variable
    """
    if time_format is not None:
        return date.astimezone().strftime(time_format)
    return get_age(date)
