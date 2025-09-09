import datetime
import uuid


def get_unique_id() -> int:
    """Returns a unique integer based on a UUID."""
    return uuid.uuid4().int


def get_timestamp_with_microseconds() -> int:
    """Returns a timestamp with microsecond granularity."""
    return int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1_000_000)


def get_current_date_time():
    return datetime.datetime.now(datetime.timezone.utc)


# Example usage
# print(get_unique_id())
# print(get_unique_id())

# Example usage
# This is unique *for this one process* as long as calls are not within the same microsecond.
# print(get_timestamp_with_microseconds())
# print(get_timestamp_with_microseconds())
def convert_to_date(open_date, default_date):
    if open_date:
        return datetime.datetime.strptime(open_date, "%Y-%m-%d").date()
    return default_date
