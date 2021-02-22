from datetime import datetime


class STDDelta:
    """
    Util object for optimizing time deltas
    """
    def __init__(self, std: datetime = None, seconds: int = 86400, file_path: str = None):
        self._std: datetime = std
        self._seconds: int = seconds
        self._path: str = file_path

    def __repr__(self) -> str:
        return f"""
        Object : {self._std}
        Seconds from target : {self._seconds}
        """

    @property
    def seconds(self):
        return self._seconds

    @property
    def std(self):
        return self._std

    @property
    def path(self):
        return self._path

    def min_resolver(self, std: datetime, seconds: int, file_path: str):
        """
        Modifies object attributes if 'seconds' is 
        smaller than current object val
        """

        if seconds >= self._seconds:
            return
        else:
            self._seconds = seconds
            self._std = std
            self._path = file_path
