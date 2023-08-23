"""
Helper functions
"""

import logging
import os
import stat
import sys
import traceback
from pathlib import Path
from datetime import datetime

import yaml
from dateutil import parser
from dateutil.relativedelta import relativedelta
from pytz import utc


def exception(exc: Exception, trace=False) -> str:
    """
    Describe exception with traceback
    """
    return "".join(
        [
            traceback.format_exc() if trace else "",
            f"{exc.__class__.__name__}: {exc}",
        ]
    )


def get_age(date: datetime):
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


def check_permissions(path: Path, insecure: bool = False) -> None:
    """
    Check file permissions
    """
    if path.stat().st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        if insecure:
            logging.warning("%s is world readable", path)
        else:
            logging.error("%s is world readable", path)
            sys.exit(1)


def check_leafs(tree: dict, insecure: bool = False) -> None:
    """
    Check a nested dict for string values containing files and check permissions
    """
    for value in tree.values():
        if isinstance(value, dict):
            check_leafs(value)
        elif isinstance(value, str):
            if os.path.isabs(value) and os.path.isfile(value):
                check_permissions(Path(value), insecure)


def get_config(path: Path, insecure: bool = False) -> dict:
    """
    Get configuration from yaml
    """
    check_permissions(path, insecure)

    last_modified_time = path.stat().st_mtime

    # Check if the current modification time is different from the last one
    if (
        hasattr(get_config, "last_modified_time")
        and get_config.last_modified_time == last_modified_time
    ):
        return get_config.cached_config

    # If the file has been modified, read the configuration
    with open(path, encoding="utf-8") as file:
        config = yaml.full_load(file)

        check_leafs(config, insecure)

        # Cache the configuration and modification time
        get_config.cached_config = config
        get_config.last_modified_time = last_modified_time

        return config
