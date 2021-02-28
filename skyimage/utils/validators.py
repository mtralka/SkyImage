import datetime
import os
from typing import List


def validate_file_path(path: str, name: str) -> str:
    assert os.path.isdir(path), f"{name} is not a directory"

    return path


def validate_year(year: str or int) -> int:
    return int(year)


def validate_datetime(j_day: str or int or list, year: int) -> List[str] and list:
    def validate_j_day(j_day: str or int) -> bool:
        if type(j_day) is str:
            j_day = int(j_day)

        if j_day < 0 or j_day > 365:
            return False
        else:
            return True

    processed_j_day: list = []
    valid_j_days: list = []
    valid_stds: list = []

    if not j_day or not year:
        raise ValueError("Julian day or year not defined")

    if type(j_day) is int:
        processed_j_day = [str(j_day)]
    elif type(j_day) is str:

        if "-" in j_day:
            split = j_day.split("-")

            if len(split) != 2:
                raise ValueError("Julian day values incorrect. Must be split with '-'")

            start = int(split[0])
            end = int(split[1]) + 1

            for num in range(start, end, 1):
                processed_j_day.append(num)
        else:
            processed_j_day = [int(j_day)]

    elif type(j_day) is list:
        processed_j_day = [int(day) for day in j_day]

    else:
        raise TypeError(f"Julian day is {type(j_day)} must be string or int")

    for day in processed_j_day:
        if not validate_j_day(day):
            raise ValueError("Julian value is out of 0 - 365 range")
        valid_j_days.append(f"{int(day):03}")

    for day in valid_j_days:
        valid_stds.append(datetime.datetime.strptime(str(year) + str(day), "%Y%j"))

    return valid_j_days, valid_stds
