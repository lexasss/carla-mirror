import sys
from typing import Optional

import numpy as np
from . import surface

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal

_kind = Literal["P", "p", "R", "r", "G", "g", "B", "b", "A", "a", "C", "c"]

def surface_to_array(
    array: np.ArrayLike[np.uint8],
    surface: surface.Surface,
    kind: Optional[_kind] = ...,
    opaque: Optional[int] = ...,
    clear: Optional[int] = ...,
) -> None: ...
def array_to_surface(surface: surface.Surface, array: np.ArrayLike[np.uint8]) -> None: ...
def map_to_array(array1: np.ArrayLike[np.uint8], array2: np.ArrayLike[np.uint8], surface: surface.Surface) -> None: ...
def make_surface(array: np.ArrayLike[np.uint8]) -> surface.Surface: ...

