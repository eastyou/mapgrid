from __future__ import annotations

"""mapgrid：A4 经纬网练习纸生成器。"""

from .model import (
    CITIES,
    Bounds,
    CityPoint,
    CoordError,
    Question,
    format_lat,
    format_lon,
    generate_questions,
    hemisphere,
    project,
    ticks,
    validate_bounds,
)
from .render import render_worksheet

__version__ = "0.1.0"

__all__ = [
    "Bounds",
    "CITIES",
    "CityPoint",
    "CoordError",
    "Question",
    "format_lat",
    "format_lon",
    "generate_questions",
    "hemisphere",
    "project",
    "render_worksheet",
    "ticks",
    "validate_bounds",
]
