from typing import Dict
from typing import List
from typing import Optional
from typing import Union


def decimal_to_binary(decimal: Union[int, str]) -> str:
    """Convert decimal to binary 32-bit

    Parameters
    ----------
    decimal : int or str
        Decimal form.

    Returns
    ----------
    str
        Binary form.

    Examples
    ----------
    >>> __decimal_to_binary(59)
    111011
    >>> __decimal_to_binary("462")
    111001110
    """
    if type(decimal) is str:
        decimal = int(decimal)

    binary = str(bin(decimal))[2:]
    return f"{int(binary):032}"


def binary_to_decimal(binary: str) -> int:
    """Convert binary to decimal

    Parameters
    ----------
    binary : str
        Binary form.

    Returns
    ----------
    int
        Decimal form.

    Examples
    ----------
    >>> __binary_to_decimal(111001110)
    462
    >>> __decimal_to_binary(110001)
    49
    """
    return int(binary, 2)


class MODIS:
    LAYERS: List[str] = [
        "Coarse Resolution Granule Time",
        "Coarse Resolution Number Mapping",
        "n pixels averaged"
    ]
    ESSENTIAL: List[str] = ["CRGT", "CRNM", "NPA"]

    NUM_MAPPINGS: Dict[str, str] = {
            "CLD": "0-7",
            "CLD_SHDW": "8-15",
            "ADJ_CLD": "16-23",
            "SNW": "24-31",
        }


class TargetSublayers:
    def __init__(self, platform: str, override_layers: Optional[Union[str, list]] = None):

        self.possible_platforms = {"MODIS": MODIS}

        if not override_layers:
            if platform not in self.possible_platforms:
                raise ValueError(f"`platform` layers for {platform} not found")
            else:
                self.name = platform
                self.platform = self.possible_platforms[platform]
        else:
            self.layers = override_layers

    def __str__(self) -> str:
        return f"""
        {self.name}
        {len(self.layers)} layer(s)
        {len(self.essential)} essential layer(s)

        Layers
        -------
        {self.layers}

        Essential Layers
        -------
        {self.essential}

        Number Mappings
        -------
        {self.num_map}
        """

    def __repr__(self) -> str:
        return f"<{self.name} Sublayers>"

    @property
    def layers(self) -> List[str]:
        return self.platform.LAYERS

    @property
    def essential(self) -> List[str]:
        return self.platform.ESSENTIAL

    @property
    def num_map(self) -> List[str]:
        return self.platform.NUM_MAPPINGS

    @staticmethod
    def make_abbreviation(target: str) -> str:
        """Make abbreviation of str

        Join first letter of each word

        """
        return "".join([word[0] for word in target.split()]).upper()




        
