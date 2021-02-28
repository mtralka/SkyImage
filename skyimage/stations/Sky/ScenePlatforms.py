from typing import Dict
from typing import List


class MODIS:
    LAYERS: List[str] = [
        "Coarse Resolution Granule Time",
        "Coarse Resolution Number Mapping",
        "n pixels averaged",
    ]
    ESSENTIAL: List[str] = ["CRGT", "CRNM", "NPA"]

    NUM_MAPPINGS: Dict[str, str] = {
        "CLD": "0-7",
        "CLD_SHDW": "8-15",
        "ADJ_CLD": "16-23",
        "SNW": "24-31",
    }
