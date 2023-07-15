from datetime import datetime
from pytz import utc
from freezegun import freeze_time
from cloudview.utils import get_age, fix_date


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


def test_fix_date():
    # Test case with a string date
    date_string = "2022-01-01T12:00:00Z"
    expected_date = datetime(2022, 1, 1, 12, 0, 0, tzinfo=utc)
    assert fix_date(date_string) == get_age(expected_date)

    # Test case with a datetime object
    date_object = datetime(2023, 5, 15, 18, 30, 0, tzinfo=utc)
    expected_date = date_object.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    assert fix_date(date_object, "%Y-%m-%d %H:%M:%S") == expected_date

    # Test case with an invalid date
    #invalid_date = "invalid"
    #assert fix_date(invalid_date) == ""

    # Test case with an empty date
    empty_date = None
    assert fix_date(empty_date) == ""
