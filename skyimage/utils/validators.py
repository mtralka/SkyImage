import datetime
import json
from typing import List
import warnings

from skyimage.utils.models import Stations


def validate_year(year: str or int) -> int:
    return int(year)


def validate_coords(
    coords: List[float], selected_station: str, stations: Stations
) -> List[float]:

    valid_coords = []

    if coords and len(coords) == 2:
        # TODO add coordinate validation
        valid_coords = coords
    elif selected_station:
        if selected_station in stations:
            target_station = stations[selected_station]
            valid_coords = [target_station["lat"], target_station["lon"]]

        if len(valid_coords) == 0:
            raise KeyError("Selected Station not found")
    else:
        raise ValueError("lat / lon poi or station name not defined")

    return valid_coords


def validate_station_positions(positions: str or List[str] = None) -> Stations:
    valid_positions = []

    if positions:
        warnings.warn(
            "Overridding default station positions \
                        Make sure station coordinate projections match that of the files",
            UserWarning,
            stacklevel=2,
        )
        valid_positions = positions

    else:
        with open("skyimage\\stations.json") as f:
            valid_positions = json.load(f)

    return valid_positions


def validate_modis_target_sublayers(target_layers: List[str]) -> List[str]:

    valid_layers = []

    if target_layers:
        valid_layers = target_layers

        warnings.warn(
            "Overridding default MODIS target layers. \
                        Some layers are required for this program to function. Consult documentation",
            UserWarning,
            stacklevel=2,
        )
    else:
        valid_layers = [
            "Coarse Resolution Granule Time",
            "Coarse Resolution Number Mapping",
            "n pixels averaged",
        ]

    return valid_layers


def validate_file_path(path: str, name: str) -> str:
    if not path:
        raise LookupError(f"{name} path not specified")

    return path


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
