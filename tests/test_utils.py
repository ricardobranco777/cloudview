# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

from datetime import datetime
from pytz import utc
from freezegun import freeze_time
from cloudview.utils import get_age


@freeze_time("2023-07-15 10:30:00", tz_offset=0)
def test_get_age():
    # Test case with a date in the past
    past_date = datetime(1990, 1, 1, tzinfo=utc)
    expected_age = "33y6M14d10h30m"
    assert get_age(past_date) == expected_age

    # Test case with the current date
    current_date = datetime(2023, 7, 15, 10, 30, 0, tzinfo=utc)
    expected_age = "0s"
    assert get_age(current_date) == expected_age
