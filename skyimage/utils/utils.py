from typing import List
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

    """

    def __init__(self, name: str, coords: List[float]):
        self.name = name
        self.coords = coords

        @property
        def latitude(self) -> float:
            return self.coords[0]

        @property
        def longitude(self) -> float:
            return self.coords[1]
