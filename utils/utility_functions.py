import argparse


def str_to_bool(v: str) -> bool:
    """Convert a string to a boolean value.
    Accepts 'true', '1', 'yes' (case-insensitive) as True,
    and 'false', '0', 'no' as False.
    Raises an error for invalid inputs.
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ("true", "1", "yes"):
        return True
    if v.lower() in ("false", "0", "no"):
        return False
    raise argparse.ArgumentTypeError(f"Boolean value expected, got: {v!r}")
