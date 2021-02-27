from datetime import datetime
from typing import Optional
from skyimage.utils.utils import buffer_value
from numpy import ndarray
import matplotlib.pyplot as plt
import numpy as np


class GroundImage:
    def __init__(self, path: str, target_time: Optional(datetime),
                 aquisition_time: Optional(datetime),
                 time_delta: Optional(int),
                 SI: Optional(ndarray),
                 BI: Optional(ndarray),
                 BI_stats: Optional(dict),
                 SI_stats: Optional(dict),
                 n_total: Optional(int),
                 prcnt_CLD: Optional(float)):

        self.path: str = path
        self.target_time: datetime = target_time
        self.aquisition_time: datetime = aquisition_time
        self.sky_time_delta: int = time_delta
        self.BI: ndarray = BI
        self.SI: ndarray = SI
        self.BI_stats: dict = BI_stats
        self.SI_stats: dict = SI_stats
        self.n_total: int = n_total
        self.prcnt_CLD: float = prcnt_CLD

    @property
    def j_day(self) -> str:
        j_day: int = self.target_time.timetuple().tm_yday
        return buffer_value(j_day, 3)

    @property
    def j_day_full(self) -> str:
        j_day: int = self.target_time.timetuple().tm_yday
        year: int = self.target_time.year
        return str(year) + buffer_value(j_day, 3)

    @property
    def sky_time_delta(self) -> int:
        if not hasattr(self, 'sky_time_delta'):
            delta = self.aquisition_time - self.target_time
            return delta.seconds

        else:
            return self.sky_time_delta

    def show_graph(self, save: Optional[bool] = None,
                   file_name: Optional[str] = None):

        if not hasattr(self, 'BI') or not hasattr(self, 'SI'):
            raise ValueError(
                "GroundImage object must have `BI` and `SI` values")

        BI: ndarray = self.BI.flatten()
        SI: ndarray = self.SI.flatten()

        x: ndarray = BI[np.logical_not(np.isnan(BI))]
        y: ndarray = SI[np.logical_not(np.isnan(SI))]

        plt.xlabel("BI")
        plt.ylabel("SI")

        plt.hist2d(x, y, (50, 50), cmap=plt.cm.jet)

        x_step = [0, 0.1, 0.35, 0.7, 0.8, 1]
        y_step = [1, 0.6, 0.35, 0.15, 0.1, 0]
        plt.plot(x_step, y_step, "w")

        cb = plt.colorbar()

        if save:
            plt.savefig(file_name, dpi=100)
            # TODO fix
            # one of these works
            cb.remove()
            plt.close()
            plt.close("all")
            plt.clf()
            plt.cla()