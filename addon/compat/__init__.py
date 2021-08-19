from typing import TYPE_CHECKING
from .v1 import v1_compat

if TYPE_CHECKING:
    from ..firstrun import Version


def compat(prev_version: "Version") -> None:
    """Executes code for compatability from older versions."""
    if prev_version == "-1.-1":
        return
    elif prev_version < "2.0":
        print("Review Hotmouse: Running v1_compat()")
        v1_compat()
