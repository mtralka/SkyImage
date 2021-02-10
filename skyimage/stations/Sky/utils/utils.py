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
