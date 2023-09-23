# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

from datetime import datetime
from pytz import utc
from freezegun import freeze_time
from cloudview.utils import get_age, utc_date


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


def test_utc_date():
    date_strings = [
        "2022-06-12T17:33:16.000Z",
        "2023-05-02T14:17:18.7574445+00:00",
        "2023-08-27T04:34:57.302-07:00",
        "2023-03-23T15:18:01Z",
    ]

    expected_dates = [
        datetime(2022, 6, 12, 17, 33, 16, tzinfo=utc),
        datetime(2023, 5, 2, 14, 17, 18, 757444, tzinfo=utc),
        datetime(2023, 8, 27, 11, 34, 57, 302000, tzinfo=utc),
        datetime(2023, 3, 23, 15, 18, 1, tzinfo=utc),
    ]

    for date_str, expected_date in zip(date_strings, expected_dates):
        assert utc_date(date_str) == expected_date
