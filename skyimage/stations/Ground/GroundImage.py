from datetime import datetime
import glob
import logging
from typing import Dict
from typing import Optional
from typing import Union
import warnings

import matplotlib.pyplot as plt
import numpy as np
from numpy import ndarray
import pandas as pd
from skimage.io import imread
from skyimage.stations.Ground.utils.image import f_above_or_below
from skyimage.stations.Ground.utils.utils import STDDelta
from skyimage.utils.utils import Station as StationObject
from skyimage.utils.utils import buffer_value


class GroundImage:
    def __init__(
        self,
        target_time: datetime = None,
        direct_path: Optional[str] = None,
        ground_path: Optional[str] = None,
        station: Optional[StationObject] = None,
        time_delta: Optional[int] = None,
        file_format: str = "jpg",
        mask_path: Optional[str] = "skyimage\\stations\\Ground\\mask.npy",
        show_image: bool = False,
        save_image: bool = False,
    ):
        self.target_time: datetime = target_time
        self.direct_path: str = direct_path
        self.file_format = file_format

        if direct_path and ground_path:
            warnings.warn(
                "Both `ground_path and `direct_path` passed,\
                defaulting to `direct_path`",
                UserWarning,
                stacklevel=2,
            )

            self.direct_path = direct_path
        elif not direct_path:

            assert ground_path, "`ground_path` required when not using `direct_path`"
            assert target_time, "`target_time` required when not using `direct_path`"
            assert station, "`station` required when not using `direct_path"

            self.__find_matching_image(target_time, station.name, ground_path)
        else:
            if not time_delta:
                self.time_delta: int = self.time_delta()
            else:
                self.time_delta: int = time_delta

        self.mask_path: bool = mask_path
        self.show_image: bool = show_image
        self.save_image: bool = save_image
        self.processed: bool = False

        self.BI: ndarray
        self.SI: ndarray
        self.BI_stats: dict
        self.SI_stats: dict
        self.n_total: int
        self.prcnt_cld: float

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
    def name(self) -> str:
        date: str = self.j_day_full
        time: str = str(self.actual_time.strftime("%H:%M"))
        return f"{date}-{time}"

    def __str__(self) -> str:
        self_str: str = \
            f"""
            {self.name}
            {self.time_delta} second(s) from target
            """

        if self.processed:
            self_str = self_str + \
                f"""
                {self.prcnt_cld} % cloudy
                {self.n_total} total pixels
                BI
                {self.BI_stats}
                SI
                {self.SI_stats}
                """
        return self_str

    def __repr__(self) -> str:
        return f"<GroundImage {self.name}>"

    def time_delta(self) -> int:
        delta = self.actual_time - self.target_time
        return delta.seconds

    def __show_image(img: ndarray) -> None:
        plt.imshow(img)
        plt.show()

    def __save_image(img: ndarray, file_name: str) -> None:
        plt.imsave(file_name, img.astype("uint8"))

    def __find_matching_image(
        self, target_time: datetime, station: str, path: str
    ) -> None:
        """ Find path to desired image

            Uses
            ----------

            `self.file_format` : str
                File format of target image

            Parameters
            ----------

            `target_time` : datetime
                target image time

            `station` : str
                Name of target station

            `path` : str
                Path for image search

            Defines
            ----------
            `self.direct_path`
                path to target image

            `self.actual_time`
                time `direct_path` image was taken

            `self.time_delta`
                time delta in seconds from target time

            """
        file_format: str = self.file_format
        year: str = str(target_time.year)
        month: str = buffer_value(target_time.month, 2)
        day: str = buffer_value(target_time.day, 2)

        search_directory: str = f"/{station}/{year}/{month}/{day}/"

        matching_file_list = list(
            glob.iglob(path + f"{search_directory}*{year + month + day}*.{file_format}")
        )

        if not matching_file_list:
            raise FileNotFoundError(f"GROUND image for {target_time} not found")

        time_resolver: STDDelta = STDDelta()
        for file in matching_file_list:
            ground_std_idx: int = file.index(year + month + day)
            ground_std = datetime.strptime(
                file[ground_std_idx: ground_std_idx + 15], "%Y%m%dT%H%M%S"
            )
            std_delta = ground_std - target_time
            seconds_delta: int = std_delta.seconds
            time_resolver.min_resolver(ground_std, seconds_delta, file)

        if time_resolver.seconds > 7200:
            warnings.warn(
                f"""
                GROUND photo
                {time_resolver}
                target: {str(target_time)}
                """,
                UserWarning,
                stacklevel=2,
            )

        logging.info(
            f"""
            GROUND photo
            {time_resolver}
            target: {str(target_time)}
            """,
        )
        self.direct_path = time_resolver.path
        self.actual_time = time_resolver.std
        self.time_delta = time_resolver.seconds

    def run_all(
        self,
        show_image: bool = False,
        save_image: bool = False,
        show_time: bool = False,
    ) -> None:

        start_time: datetime = datetime.now()
        self.show_image = show_image
        self.save_image = save_image
        self.extract()
        self.process()

        if show_time:
            print(self.name + "-", datetime.now() - start_time)

    def extract(self) -> None:
        """Extract `BI` and `SI` for image at `self.direct_path`.

        Uses
        ----------

        `self.mask_path` : str
            Path to np.ndarray defining crop mask

        `self.direct_path` : str
            Path to target image

        `self.show_image` : bool
            Boolean determining if target image should
            be displayed

        `self.save_image` : bool
            Boolean determining if target image should
            be saved to disk

        `self.name` : str
            YYYY-JDAY-HH:MM of image

        Defines
        ----------
        `self.BI`
            Brightness Index of image
        `self.SI`
            Sky Index of image

        """

        crop_mask: ndarray = np.load(self.mask_path)

        img_arr: ndarray = imread(self.direct_path)

        img: ndarray = img_arr * crop_mask

        if self.show_image:
            self.__show_image(img)

        if self.save_image:
            img_file_name = self.name + ".png"
            self.__save_image(img, img_file_name)

        img: ndarray = img.astype("float")
        img[img == 0] = np.nan

        R: ndarray = img[:, :, 0] / 255
        G: ndarray = img[:, :, 1] / 255
        B: ndarray = img[:, :, 2] / 255

        SI: ndarray = (B - R) / (B + R)
        BI: ndarray = (R + G + B) / 3

        self.BI = BI
        self.SI = SI

    def process(self) -> None:
        """Process `self.BI` and `self.SI` for image at `self.direct_path`.

        Uses
        ----------
        `self.BI` : ndarray
            Image Brightness index

        `self.SI` : ndarray
            Image Sky Index

        Defines
        ----------
        `self.BI_stats` : dict
            Statistical information
            concerning image

        `self.SI_stats` : dict
            Statistical information
            concerning image

        `self.n_total` : int
            Total pixels in image

        `self.prcnt_cld` : float
            Percent clouds in image

        `self.processed` : bool
            Marker signaling object processed


        """

        def __extract_stats(array) -> Dict[str, float]:

            mean = round(np.nanmean(array), 2)
            max = round(np.nanmax(array), 2)
            min = round(np.nanmin(array), 2)

            return {"mean": mean, "max": max, "min": min}

        if not hasattr(self, "BI") or not hasattr(self, "SI"):
            raise ValueError(
                "GroundImage object must have `BI` and `SI` values before processing"
            )

        # we keep NaNs to preserve image shape
        # for reconstitution after cloud mask creation
        # BI = BI[np.logical_not(np.isnan(BI))]
        # SI = SI[np.logical_not(np.isnan(SI))]

        BI_stats: dict = __extract_stats(self.BI)
        SI_stats: dict = __extract_stats(self.SI)
        BI_SI_points = np.column_stack((self.BI.flatten(), self.SI.flatten()))

        x_step = [0, 0.1, 0.35, 0.7, 0.8, 1]
        y_step = [1, 0.6, 0.35, 0.15, 0.1, 0]
        boundary = np.column_stack((x_step, y_step))

        pixel_total: int = BI_SI_points[np.logical_not(np.isnan(BI_SI_points))].size / 2

        cloud_mask: list = []
        img_shape: tuple = self.BI.shape[0:2]
        number_clear: int = 0

        for point in BI_SI_points:
            results: int = f_above_or_below(point, boundary)
            cloud_mask.append(results)
            number_clear = number_clear + results

        cloud_mask = np.array(cloud_mask).reshape(img_shape)

        if self.show_image:
            self.__show_image(cloud_mask)

        if self.save_image:
            img_file_name = self.name + "_cld_mask.png"
            self.__save_image(img_file_name, cloud_mask)

        percent_cloud: float = round(
            ((pixel_total - number_clear) / pixel_total) * 100, 2
        )

        self.BI_stats = BI_stats
        self.SI_stats = SI_stats
        self.n_total = int(pixel_total)
        self.prcnt_cld = percent_cloud
        self.processed = True

    def results(self, as_dataframe: bool = False) -> Union[dict, pd.DataFrame]:

        if not self.processed:
            raise AssertionError("Object not processed")

        results = {
            "BI": self.BI_stats,
            "SI": self.SI_stats,
            "n_total": self.n_total,
            "prcnt_cld": self.prcnt_cld,
        }

        if as_dataframe:
            return pd.DataFrame.from_dict(results, orient="index")

        return results

    def show_graph(self, save: Optional[bool] = None, file_name: Optional[str] = None):

        if not hasattr(self, "BI") or not hasattr(self, "SI"):
            raise ValueError("GroundImage object must have `BI` and `SI` values")

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
