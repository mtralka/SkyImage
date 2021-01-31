import glob
import logging
from typing import Dict
from typing import List

import numpy as np
import rasterio as rio
from skyimage.utils.models import Stations
from skyimage.utils.validators import validate_coords
from skyimage.utils.validators import validate_datetime
from skyimage.utils.validators import validate_file_path
from skyimage.utils.validators import validate_modis_target_layers
from skyimage.utils.validators import validate_station_positions


class Sky:
    def __init__(
        self,
        j_days: int or str or list = None,
        year: int = None,
        path: str = None,
        file_format: str = "hdf",
        coords: List[float] = None,
        station: str = None,
        station_positions: Stations = None,
        skip_validation: bool = False,
        target_layers: List[str] = None,
    ):

        self.path: str = validate_file_path(path, "MODIS")
        self.target_layers: List[str] = validate_modis_target_layers(target_layers)
        self.station_positions: Stations = validate_station_positions(station_positions)
        self.coords: List[float, float] = validate_coords(
            coords, station, self.station_positions
        )
        self.j_days, self.stds = validate_datetime(j_days, year)
        self.file_format: str = file_format

        self.scenes: Dict[str, str] = self.find_matching_scenes()
        self.scenes_metadata: Dict[str, dict] = {
            k: self.get_metadata(v) for k, v in self.scenes.items()
        }
        self.scenes_sublayers: Dict[str, str] = {
            k: self.find_target_sublayers(v) for k, v in self.scenes.items()
        }
        self.raw_poi: Dict[str, Dict[str, object]] = {
            k: self.extract_poi_data(v) for k, v in self.scenes_sublayers.items()
        }
        self.poi: Dict[str, dict] = {
            k: self.process_poi_data(v) for k, v in self.raw_poi.items()
        }
        # self.process_poi_data()

    def __decimal_to_binary(self, decimal: int or str) -> str:
        if type(decimal) is str:
            decimal = int(decimal)
        return str(bin(decimal))[2:]

    def __binary_to_decimal(self, binary: str) -> int:
        return int(binary, 2)

    def find_matching_scenes(self) -> Dict:

        year: str = str(self.stds[0].year)
        j_days: list = self.j_days
        path = self.path
        file_format = self.file_format
        matching_scenes: Dict = {}

        for day in j_days:
            user_selection = 0
            matching_file_list = list(
                glob.iglob(path + f"/{year}/*{year + day}*.{file_format}")
            )

            if not matching_file_list:
                raise FileNotFoundError(f"MODIS scene {year}-{day} not found")
            elif len(matching_file_list) > 1:
                pass
                #  for index, file in enumerate(matching_file_list):
                #     print(f"{index} | {file}") # TODO make this prettier and present time
                #  user_selection = int(input("Which file would you like?"))
                #  raise LookupError("Multiple matching files found")
            else:
                logging.info(f"MODIS scene {year}-{day} found")

            matching_scenes[year + day] = matching_file_list[user_selection]

        return matching_scenes

    def get_metadata(self, target) -> Dict:
        with rio.open(target) as ds:
            meta = ds.meta
        return meta

    def find_target_sublayers(self, layer: str) -> Dict:
        target_layers = self.target_layers
        found_layers = {}

        with rio.open(layer) as ds:
            crs = ds.read_crs()
            for name in ds.subdatasets:
                for target in target_layers:
                    if target in name:
                        logging.info(f"{target} layer found")
                        abbrev = "".join([word[0] for word in target.split()]).upper()
                        found_layers[abbrev] = name
        return found_layers

    def extract_poi_data(self, sub_layers: Dict) -> Dict:
        lat = self.coords[0]
        lon = self.coords[1]
        poi_dict = {}

        for key, val in sub_layers.items():
            with rio.open(val) as ds:
                self.crs = ds.read_crs()
                py, px = ds.index(lon, lat)
                # window = rio.windows.Window(px - 1, py - 1, 3, 3)
                window = rio.windows.Window(px - 1, py - 1, 1, 1)
                arr = ds.read(1, window=window)
                logging.info(f"{key}\n{window}\n{arr}")
                poi_dict[key] = arr
        return poi_dict

    def process_poi_data(self, raw_data: Dict) -> Dict:
        def __find_percent(num, total=None) -> float:
            if not total:
                total = pixel_total
            return num / total

        processed_dict = {}

        if "CRGT" in raw_data.keys():
            processed_dict["time_utc"] = int(np.mean(raw_data["CRGT"]))
        else:
            raise KeyError(
                "Unable to assert MODIS scene aquisition time. Check CRGT sublayer "
            )

        if "CRNM" and "NPA" in raw_data.keys():

            NUM_MAPPINGS = {
                "CLD": "0-7",
                "CLD_SHDW": "8-15",
                "ADJ_CLD": "16-23",
                "SNW": "24-31",
            }

            pixel_total = raw_data["NPA"].sum()
            # processed_dict["n_pixel_total"] = n_pixel_total

            crnm = raw_data["CRNM"].flatten()

            cld, cld_shdw, adj_cld, snw = 0, 0, 0, 0
            for pixel in crnm:
                binary = self.__decimal_to_binary(str(pixel))
                # TODO binary solving for cover

            processed_dict["n_CLD"] = cld
            processed_dict["n_CLD_SHW"] = cld_shdw
            processed_dict["n_ADJ_CLD"] = adj_cld
            processed_dict["n_SNW"] = snw
            processed_dict["n_TOTAL"] = pixel_total

            processed_dict["prcnt_CLD"] = __find_percent(cld)
            processed_dict["prcnt_CLD_SHW"] = __find_percent(cld_shdw)
            processed_dict["prcnt_ADJ_CLD"] = __find_percent(adj_cld)
            processed_dict["prcnt_SNW"] = __find_percent(snw)
            
            # processed_dict["prcnt_cover"] = {
            #     "CLD": __find_percent(cld),
            #     "CLD_SHW": __find_percent(cld_shdw),
            #     "ADJ_CLD": __find_percent(adj_cld),
            #     "SNW": __find_percent(snw),
            # }
            # processed_dict["n_pixels"] = {
            #     "CLD": cld,
            #     "CLD_SHW": cld_shdw,
            #     "ADJ_CLD": adj_cld,
            #     "SNW": snw,
            #     "TOTAL": pixel_total,
            # }
        else:
            raise KeyError(
                "Unable to assert MODIS cloud cover. Check CRNM and NPA sublayers"
            )

        return processed_dict
