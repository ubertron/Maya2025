from datetime import datetime
from typing import Optional


def get_date_time_string(date_time: Optional[datetime] = None):
    """
    Get the supplied time as a formatted string
    :param date_time:
    :return:
    """
    date_time = date_time if date_time else datetime.now()
    return datetime.strftime(date_time, "%Y-%m-%d %H:%M:%S")


if __name__ == '__main__':
    print(get_date_time_string())
