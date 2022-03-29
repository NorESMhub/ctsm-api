"""
Geojson schemas currently only support points because other types are not needed.
"""
from typing import Generic, List, Optional, Tuple, TypeVar, Union

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

NumType = Union[float, int]
Properties = TypeVar("Properties")

BBox = Union[
    Tuple[NumType, NumType, NumType, NumType],  # 2D bbox
    Tuple[NumType, NumType, NumType, NumType, NumType, NumType],  # 3D bbox
]


class Point(BaseModel):
    type: str = Field("Point", const=True)
    coordinates: Tuple[float, float]


class Feature(GenericModel, Generic[Properties]):
    type: str = Field("Feature", const=True)
    geometry: Point
    properties: Optional[Properties]
    id: Optional[str]
    bbox: Optional[BBox]


class FeatureCollection(GenericModel, Generic[Properties]):
    type: str = Field("FeatureCollection", const=True)
    features: List[Feature[Properties]]
    bbox: Optional[BBox]
