from typing import Any, Callable, Tuple, Optional, Dict, TypeVar, Union
import numpy as np

_S = TypeVar('_S')

def spline_filter1d(input: np.ArrayLike[_S],
                    order: int = ...,
                    axis: int = ...,
                    output: np.ndarray[Any] = ...,
                    mode: str = ...) -> np.ArrayLike[_S]: ...
def spline_filter(input: np.ArrayLike[_S],
                  order: int = ...,
                  output: np.ndarray[Any] = ...,
                  mode: str = ...) -> np.ArrayLike[_S]: ...
def geometric_transform(input: np.ArrayLike[_S],
                        mapping: Callable[[Tuple[int,...]], Tuple[int,...]],
                        output_shape: Optional[Tuple[int,...]] = ...,
                        output: Optional[np.ArrayLike[Any]] = ...,
                        order: int = ...,
                        mode: str = ...,
                        cval: float = ...,
                        prefilter: bool = ...,
                        extra_arguments: Optional[Tuple[Any,...]] =...,
                        extra_keywords: Optional[Dict[str,Any]]=...) -> np.ArrayLike[_S]: ...
def map_coordinates(input: np.ArrayLike[_S],
                    coordinates: Any,
                    output: Optional[np.ArrayLike[Any]] = ...,
                    order: int = ...,
                    mode: str = ...,
                    cval: float = ...,
                    prefilter: bool = ...) -> np.ArrayLike[_S]: ...
# def affine_transform(input, matrix, offset: float = ..., output_shape: Incomplete | None = ..., output: Incomplete | None = ..., order: int = ..., mode: str = ..., cval: float = ..., prefilter: bool = ...): ...
# def shift(input, shift, output: Incomplete | None = ..., order: int = ..., mode: str = ..., cval: float = ..., prefilter: bool = ...): ...
def zoom(input: np.ArrayLike[_S],
         zoom: Union[float, Tuple[float, ...]],
         output: Optional[np.ArrayLike[Any]] = ...,
         order: int = ...,
         mode: str = ...,
         cval: float = ...,
         prefilter: bool = ..., 
         grid_mode: bool = ...) -> np.ArrayLike[_S]: ...
# def rotate(input, angle, axes=..., reshape: bool = ..., output: Incomplete | None = ..., order: int = ..., mode: str = ..., cval: float = ..., prefilter: bool = ...): ...
