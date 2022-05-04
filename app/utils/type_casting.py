from typing import Union


def to_bool(v: Union[str, int, float, bool]) -> bool:
    """
    Converts the following values to True:
    - integer numbers > 0
    - strings y, yes, true, t (case-insensitive)
    - Booleans True
    """
    try:
        v = float(v)
    except ValueError:
        pass

    if isinstance(v, float):
        return v != 0

    if isinstance(v, str):
        return v.lower() in ("y", "yes", "t", "true")

    return v
