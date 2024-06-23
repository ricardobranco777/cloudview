"""
Helper functions
"""

import os
from datetime import datetime

from dateutil import parser
from dateutil.relativedelta import relativedelta
from pytz import utc


def read_file(path: str) -> str:
    """
    Read file but raise RuntimeError if it has the wrong permissions
    """
    with open(path, encoding="utf-8") as file:
        if os.fstat(file.fileno()).st_mode & 0o77:
            raise RuntimeError(f"{path} has insecure permissions")
        return file.read()


def get_age(date: datetime) -> str:
    """
    Get age
    """
    age = relativedelta(datetime.now(tz=utc), date)
    string = "".join(
        [
            f"{age.years}y" if age.years else "",
            f"{age.months}M" if age.months else "",
            f"{age.days}d" if age.days else "",
            f"{age.hours}h" if age.hours else "",
            f"{age.minutes}m" if age.minutes else "",
            f"{age.seconds}s" if age.seconds else "",
        ]
    )
    if string == "":
        string = "0s"
    return string


def timeago(date: datetime) -> str:
    """
    Time ago
    """
    diff = datetime.now(tz=utc) - date
    seconds = int(diff.total_seconds())
    ago = "ago"
    if seconds < 0:
        ago = "in the future"
        seconds = abs(seconds)
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''} {ago}"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} {ago}"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} {ago}"
    days = hours // 24
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''} {ago}"
    months = days // 30
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''} {ago}"
    years = months // 12
    return f"{years} year{'s' if years != 1 else ''} {ago}"


def dateit(date: datetime, time_format: str = "%a %b %d %H:%M:%S %Z %Y") -> str:
    """
    Return date in desired format
    """
    date = date.astimezone()
    if time_format == "timeago":
        return timeago(date)
    if time_format == "age":
        return get_age(date)
    return date.strftime(time_format)


def utc_date(date: str | datetime) -> datetime:
    """
    Return UTC normalized datetime object from date
    """
    if isinstance(date, str):
        if date.isdigit():
            date = datetime.fromtimestamp(int(date))
        else:
            date = parser.parse(date)
    if date.tzinfo is not None:
        date = date.astimezone(utc)
    else:
        date = date.replace(tzinfo=utc)
    return date
