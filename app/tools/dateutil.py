import time
from dateutil import relativedelta


def get_date_month(now, month=0):
    """
    获取距离某个日期X月的日期,month为负则为之前X月的日期，为正则是之后的日期
    :param now:
    :param month:
    :return:
    """
    before_date = now + relativedelta.relativedelta(months=month)
    return before_date


def get_local_timestamp(local_time):
    local_timestamp = time.mktime(local_time.timetuple()) * 1000.0 + local_time.microsecond / 1000.0
    return local_timestamp
