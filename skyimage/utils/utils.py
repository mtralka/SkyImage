import json
from typing import List
from typing import Optional
from typing import Union
import warnings


def buffer_value(value: Union[str, int], buffer_length: int) -> str:

    if len(str(value)) > buffer_length:
        warnings.warn(
            "Length of `value` greater than `buffer_length`",
            UserWarning,
            stacklevel=0,
        )

    if type(value) is int:
        return f"{value:0{buffer_length}}"
    elif type(value) is str:
        return f"{int(value):0{buffer_length}}"
    else:
        raise TypeError("Value must be int or string")


class Station:
    """
    Station object

    Attributes
    ----------

    'name' : str
        Station name

    `coords` : List[float, float]
        Station coordinates

    `latitude` : float
        Station latitude

    `longitude` : float
        Station longitude

    `path` : str
        Override to JSON of possible stations

    Raises
    ----------

    KeyError
        if `name` not found in `path`

    """

    def __init__(self, name: str, coords: Optional[List[float]] = None, path: str = "skyimage\\stations.json"):

        self.name = name
        self.path = path
        if coords:
            self.coords = coords
        else:
            self.coords = self.__find_coords()

    @property
    def latitude(self) -> float:
        return self.coords[0]

    @property
    def longitude(self) -> float:
        return self.coords[1]

    def __find_coords(self) -> List[float]:

        with open(self.path) as f:
            valid_positions = json.load(f)

        if self.name in valid_positions:
            target_station = valid_positions[self.name]
        else:
            raise KeyError("Selected Station not found")

        return [target_station["lat"], target_station["lon"]]
