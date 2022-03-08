from typing import Union


def to_bool(v: Union[str, int, bool]) -> bool:
    try:
        v = int(v)
    except ValueError:
        pass

    if isinstance(v, int):
        return v != 0

    if isinstance(v, str):
        return v.lower() in ("y", "yes", "t", "true")

    return v
