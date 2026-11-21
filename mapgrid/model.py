from __future__ import annotations

"""mapgrid 的数据模型：经纬度校验、刻度、格式化与题目生成。

本模块只依赖 Python 标准库，所有面向外部输入的校验失败都会抛出 CoordError。
"""

import random
from dataclasses import dataclass
from typing import Optional, Tuple

LAT_LIMIT: int = 90
LON_LIMIT: int = 180
MIN_STEP: int = 1
MAX_STEP: int = 90
MIN_QUESTIONS: int = 1
MAX_QUESTIONS: int = 20

Bounds = Tuple[int, int, int, int]

# 赤道与本初子午线按地理惯例分别归入北半球、东半球。
NORTH_HEMISPHERE: str = "北半球"
SOUTH_HEMISPHERE: str = "南半球"
EAST_HEMISPHERE: str = "东半球"
WEST_HEMISPHERE: str = "西半球"


class CoordError(ValueError):
    """经纬度、题目参数或输出参数非法时抛出的异常。"""


def _require_int(value: object, label: str) -> int:
    """确认 value 是整数（排除布尔值），否则抛出 CoordError。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise CoordError(f"{label}必须是整数，收到 {value!r}")
    return value


def _validate_lat(value: object, label: str = "纬度") -> int:
    """校验纬度是否位于 -90 到 90 之间。"""
    number = _require_int(value, label)
    if not -LAT_LIMIT <= number <= LAT_LIMIT:
        raise CoordError(f"{label}必须在 -90 到 90 之间，收到 {number}")
    return number


def _validate_lon(value: object, label: str = "经度") -> int:
    """校验经度是否位于 -180 到 180 之间。"""
    number = _require_int(value, label)
    if not -LON_LIMIT <= number <= LON_LIMIT:
        raise CoordError(f"{label}必须在 -180 到 180 之间，收到 {number}")
    return number


def _validate_step(step: object, label: str = "网格步长") -> int:
    """校验步长是否位于 1 到 90 之间。"""
    number = _require_int(step, label)
    if not MIN_STEP <= number <= MAX_STEP:
        raise CoordError(f"{label}必须在 1 到 90 之间，收到 {number}")
    return number


def _unpack_bounds(bounds: object) -> Bounds:
    """把外部传入的经纬范围拆成四个整数，并校验格式。"""
    if not isinstance(bounds, tuple) or len(bounds) != 4:
        raise CoordError("经纬范围必须是 (lat_min, lat_max, lon_min, lon_max) 四元组")
    lat_min, lat_max, lon_min, lon_max = bounds
    return (
        _require_int(lat_min, "纬度最小值"),
        _require_int(lat_max, "纬度最大值"),
        _require_int(lon_min, "经度最小值"),
        _require_int(lon_max, "经度最大值"),
    )


def validate_bounds(
    lat_min: int,
    lat_max: int,
    lon_min: int,
    lon_max: int,
    step: int,
) -> None:
    """校验经纬范围与网格步长，非法时抛出中文 CoordError。"""
    lat_min = _validate_lat(lat_min, "纬度最小值")
    lat_max = _validate_lat(lat_max, "纬度最大值")
    lon_min = _validate_lon(lon_min, "经度最小值")
    lon_max = _validate_lon(lon_max, "经度最大值")
    step = _validate_step(step, "网格步长")

    if lat_min >= lat_max:
        raise CoordError(f"纬度最小值必须小于最大值，收到 {lat_min} 与 {lat_max}")
    if lon_min >= lon_max:
        raise CoordError(f"经度最小值必须小于最大值，收到 {lon_min} 与 {lon_max}")


def ticks(start: int, end: int, step: int) -> list[int]:
    """生成包含 end 的等差刻度序列；非法参数抛出 CoordError。"""
    start = _require_int(start, "起始刻度")
    end = _require_int(end, "结束刻度")
    step = _validate_step(step, "刻度步长")

    if start > end:
        raise CoordError(f"起始刻度不能大于结束刻度，收到 {start} 与 {end}")

    values: list[int] = []
    current = start
    while current <= end:
        values.append(current)
        current += step
    if values[-1] != end:
        values.append(end)
    return values


def format_lat(value: int) -> str:
    """把整数纬度格式化为 0° / 30°N / 30°S 形式。"""
    number = _validate_lat(value)
    if number == 0:
        return "0°"
    if number > 0:
        return f"{number}°N"
    return f"{-number}°S"


def format_lon(value: int) -> str:
    """把整数经度格式化为 0° / 120°E / 60°W 形式。"""
    number = _validate_lon(value)
    if number == 0:
        return "0°"
    if number > 0:
        return f"{number}°E"
    return f"{-number}°W"


def hemisphere(lat: int, lon: int) -> str:
    """返回南北半球与东西半球的组合，如「北半球 东半球」。

    赤道（纬度 0）归入北半球，本初子午线（经度 0）归入东半球。
    """
    lat = _validate_lat(lat)
    lon = _validate_lon(lon)
    north_south = NORTH_HEMISPHERE if lat >= 0 else SOUTH_HEMISPHERE
    east_west = EAST_HEMISPHERE if lon >= 0 else WEST_HEMISPHERE
    return f"{north_south} {east_west}"


def project(lon: int, lat: int, bounds: Bounds) -> tuple[float, float]:
    """等距圆柱投影：返回 0..1 的 (x, y)，y 向上为北。"""
    lat_min, lat_max, lon_min, lon_max = _unpack_bounds(bounds)
    validate_bounds(lat_min, lat_max, lon_min, lon_max, 1)

    lat = _validate_lat(lat)
    lon = _validate_lon(lon)
    if not lat_min <= lat <= lat_max:
        raise CoordError(f"纬度 {lat} 超出当前范围 {lat_min} 到 {lat_max}")
    if not lon_min <= lon <= lon_max:
        raise CoordError(f"经度 {lon} 超出当前范围 {lon_min} 到 {lon_max}")

    x = (lon - lon_min) / (lon_max - lon_min)
    y = (lat - lat_min) / (lat_max - lat_min)
    return (x, y)


@dataclass(frozen=True)
class CityPoint:
    """一个城市参考点，经度负数表示西经。"""

    name: str
    lat: int
    lon: int

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise CoordError("城市名称必须是非空字符串")
        _validate_lat(self.lat, f"城市「{self.name}」的纬度")
        _validate_lon(self.lon, f"城市「{self.name}」的经度")


CITIES: tuple[CityPoint, ...] = (
    CityPoint("北京", 40, 116),
    CityPoint("上海", 31, 121),
    CityPoint("广州", 23, 113),
    CityPoint("乌鲁木齐", 44, 88),
    CityPoint("拉萨", 30, 91),
    CityPoint("哈尔滨", 46, 127),
    CityPoint("台北", 25, 122),
    CityPoint("香港", 22, 114),
    CityPoint("东京", 36, 140),
    CityPoint("首尔", 38, 127),
    CityPoint("新加坡", 1, 104),
    CityPoint("伦敦", 51, 0),
    CityPoint("巴黎", 49, 2),
    CityPoint("莫斯科", 56, 38),
    CityPoint("开罗", 30, 31),
    CityPoint("纽约", 41, -74),
    CityPoint("洛杉矶", 34, -118),
    CityPoint("里约热内卢", -23, -43),
    CityPoint("悉尼", -34, 151),
    CityPoint("开普敦", -34, 18),
)


@dataclass(frozen=True)
class Question:
    """一道练习：plot 表示给坐标找位置，read 表示给位置写坐标。"""

    city: CityPoint
    lat: int
    lon: int
    kind: str

    def __post_init__(self) -> None:
        if not isinstance(self.city, CityPoint):
            raise CoordError("题目中的城市必须是 CityPoint 实例")
        _validate_lat(self.lat, "题目纬度")
        _validate_lon(self.lon, "题目经度")
        if self.kind not in ("plot", "read"):
            raise CoordError(f"题目类型必须是 plot 或 read，收到 {self.kind!r}")


def generate_questions(
    count: int,
    bounds: Bounds,
    seed: Optional[int] = None,
) -> list[Question]:
    """从范围内城市中抽取指定数量题目；种子相同则结果确定。"""
    count = _require_int(count, "题目数量")
    if not MIN_QUESTIONS <= count <= MAX_QUESTIONS:
        raise CoordError(f"题目数量必须在 1 到 20 之间，收到 {count}")

    lat_min, lat_max, lon_min, lon_max = _unpack_bounds(bounds)
    validate_bounds(lat_min, lat_max, lon_min, lon_max, 1)
    if seed is not None:
        seed = _require_int(seed, "随机种子")

    candidates = [
        city
        for city in CITIES
        if lat_min <= city.lat <= lat_max and lon_min <= city.lon <= lon_max
    ]
    if not candidates:
        raise CoordError("当前经纬范围内没有可选城市，请放宽经纬范围")
    if len(candidates) < count:
        raise CoordError(
            f"当前经纬范围内只有 {len(candidates)} 座可选城市，"
            f"不足以生成 {count} 道题，请放宽经纬范围或减少题目数量"
        )

    rng = random.Random(seed)
    picked = rng.sample(candidates, count)
    questions: list[Question] = []
    for index, city in enumerate(picked):
        kind = "plot" if index % 2 == 0 else "read"
        questions.append(Question(city=city, lat=city.lat, lon=city.lon, kind=kind))
    return questions
