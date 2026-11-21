from __future__ import annotations

"""mapgrid 命令行入口。

参数校验失败返回退出码 2，写文件失败返回 1，成功返回 0。
"""

import argparse
import sys
from pathlib import Path
from typing import NoReturn

from .model import Bounds, CoordError, generate_questions, validate_bounds
from .render import render_worksheet

DEFAULT_OUTPUT: str = "mapgrid.html"
DEFAULT_TITLE: str = "经纬网练习"
MAX_TITLE_LENGTH: int = 80


class _ArgumentParser(argparse.ArgumentParser):
    """把 argparse 的错误转换为中文 CoordError，便于统一处理退出码。"""

    def error(self, message: str) -> NoReturn:
        translated = (
            message.replace("unrecognized arguments:", "无法识别的参数：")
            .replace("the following arguments are required:", "缺少必需参数：")
            .replace("expected one argument", "需要一个取值")
        )
        if translated.startswith("argument "):
            translated = "参数 " + translated[len("argument ") :]
        raise CoordError(f"命令行参数无效：{translated}")


def _int_arg(text: str) -> int:
    """argparse 的整数类型转换，失败时给出中文提示。"""
    try:
        return int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"请输入整数，收到 {text!r}") from exc


def _build_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = _ArgumentParser(
        prog="mapgrid",
        description="生成 A4 经纬网练习纸，含找坐标、写坐标与答案页。",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"输出 HTML 文件路径（默认 {DEFAULT_OUTPUT}）",
    )
    parser.add_argument(
        "--lat-min",
        type=_int_arg,
        default=-60,
        help="纬度最小值，-90 到 90（默认 -60）",
    )
    parser.add_argument(
        "--lat-max",
        type=_int_arg,
        default=60,
        help="纬度最大值，-90 到 90（默认 60）",
    )
    parser.add_argument(
        "--lon-min",
        type=_int_arg,
        default=-180,
        help="经度最小值，-180 到 180（默认 -180）",
    )
    parser.add_argument(
        "--lon-max",
        type=_int_arg,
        default=180,
        help="经度最大值，-180 到 180（默认 180）",
    )
    parser.add_argument(
        "--step",
        type=_int_arg,
        default=15,
        help="经纬网格步长，1 到 90（默认 15）",
    )
    parser.add_argument(
        "--questions",
        type=_int_arg,
        default=8,
        help="题目数量，1 到 20（默认 8）",
    )
    parser.add_argument(
        "--seed",
        type=_int_arg,
        default=None,
        help="随机种子，指定后题目可复现",
    )
    parser.add_argument(
        "--no-answers",
        action="store_true",
        help="不生成答案页",
    )
    parser.add_argument(
        "--title",
        default=DEFAULT_TITLE,
        help=f"练习纸标题（默认「{DEFAULT_TITLE}」）",
    )
    return parser


def _validate_args(args: argparse.Namespace) -> Bounds:
    """校验全部命令行参数，返回经纬范围四元组。"""
    lat_min = args.lat_min
    lat_max = args.lat_max
    lon_min = args.lon_min
    lon_max = args.lon_max
    step = args.step

    validate_bounds(lat_min, lat_max, lon_min, lon_max, step)

    if not 1 <= args.questions <= 20:
        raise CoordError(f"题目数量必须在 1 到 20 之间，收到 {args.questions}")
    if not isinstance(args.title, str) or not args.title.strip():
        raise CoordError("标题不能为空")
    if len(args.title) > MAX_TITLE_LENGTH:
        raise CoordError(f"标题长度不能超过 {MAX_TITLE_LENGTH} 个字符")
    if not isinstance(args.output, str) or not args.output.strip():
        raise CoordError("输出路径不能为空")

    return (lat_min, lat_max, lon_min, lon_max)


def main(argv: list[str] | None = None) -> int:
    """命令行主函数：成功返回 0，参数错误返回 2，写文件失败返回 1。"""
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 2
    except CoordError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    try:
        bounds = _validate_args(args)
        questions = generate_questions(args.questions, bounds, args.seed)
    except CoordError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    try:
        content = render_worksheet(
            bounds,
            args.step,
            questions,
            title=args.title,
            show_answers=not args.no_answers,
        )
    except CoordError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2

    output_path = Path(args.output)
    try:
        output_path.write_text(content, encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"写入文件失败：{exc}", file=sys.stderr)
        return 1

    print(f"已生成 {output_path}（{len(questions)} 道题）")
    return 0
