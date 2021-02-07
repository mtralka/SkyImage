

def buffer_value(value: str or int, buffer_length: int) -> str:

    if type(value) is int:
        return f"{value:0{buffer_length}}"
    elif type(value) is str:
        return f"{int(value):0{buffer_length}}"
    else:
        raise TypeError("Value must be int or string")
