from __future__ import annotations

"""经纬网练习纸的 HTML / SVG 渲染。

所有外部文本（标题、城市名等）都会经过 HTML 转义，页面使用 A4 打印排版。
"""

from dataclasses import dataclass
from html import escape
from typing import Sequence

from .model import (
    Bounds,
    CoordError,
    Question,
    _unpack_bounds,
    format_lat,
    format_lon,
    hemisphere,
    project,
    ticks,
    validate_bounds,
)

SVG_WIDTH: float = 800.0
SVG_HEIGHT: float = 520.0
PAD_LEFT: float = 64.0
PAD_RIGHT: float = 64.0
PAD_TOP: float = 46.0
PAD_BOTTOM: float = 50.0

PAGE_CSS: str = """
@page { size: A4; margin: 0 }
* { box-sizing: border-box }
html, body { margin: 0; padding: 0 }
body {
  background: #eef1f5;
  color: #1f2933;
  font-family: "Noto Sans SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}
.page {
  width: 210mm;
  min-height: 297mm;
  padding: 12mm;
  box-sizing: border-box;
  overflow: hidden;
  background: #ffffff;
  margin: 0 auto 8mm;
}
.content { width: 98%; margin: 0 auto }
h1 {
  margin: 0 0 1.5mm;
  padding-bottom: 2mm;
  border-bottom: 0.6mm solid #1f2933;
  font-size: 21pt;
  letter-spacing: 0.08em;
}
h2 {
  margin: 5mm 0 2.5mm;
  font-size: 13.5pt;
  color: #1f2933;
}
.subtitle { margin: 0 0 4mm; color: #52606d; font-size: 10.5pt }
.hint { margin: 2.5mm 0 0; color: #616e7c; font-size: 9pt; line-height: 1.5 }
.map-wrap {
  width: 100%;
  padding: 2mm;
  border: 0.35mm solid #9aa5b1;
  border-radius: 1.5mm;
  background: #fbfcfd;
}
svg.grid-svg { display: block; width: 100%; height: auto }
.grid-line { stroke: #d9e2ec; stroke-width: 0.9 }
.axis-line { stroke: #7b8794; stroke-width: 2.2 }
.map-frame { fill: none; stroke: #334155; stroke-width: 1.4 }
.tick-label { fill: #334155; font-size: 12px; font-family: inherit }
.axis-label { fill: #334155; font-size: 12px; font-weight: 700; font-family: inherit }
.marker-circle {
  fill: #ffffff;
  stroke: #b91c1c;
  stroke-width: 2;
}
.read-marker .marker-circle { fill: #fff1f2 }
.answer-marker .marker-circle { fill: #e0f2fe; stroke: #0369a1 }
.marker-text { fill: #b91c1c; font-size: 11px; font-weight: 700; font-family: inherit }
.answer-marker .marker-text { fill: #0369a1 }
ol.questions {
  list-style: none;
  margin: 0;
  padding: 0;
  columns: 2;
  column-gap: 8mm;
}
ol.questions li {
  position: relative;
  break-inside: avoid;
  margin: 0 0 3.6mm;
  padding-left: 8mm;
  font-size: 10.5pt;
  line-height: 1.55;
}
.q-no {
  position: absolute;
  left: 0;
  top: 0;
  font-weight: 700;
  color: #b91c1c;
}
.blank {
  display: inline-block;
  width: 20mm;
  height: 1.05em;
  border-bottom: 0.35mm solid #1f2933;
  vertical-align: baseline;
}
.empty { color: #616e7c; font-size: 10.5pt }
.answer-map { width: 74%; margin: 0 auto }
table.answers {
  width: 100%;
  margin-top: 3.5mm;
  border-collapse: collapse;
  font-size: 9.5pt;
}
table.answers th,
table.answers td {
  border: 0.3mm solid #9aa5b1;
  padding: 1mm 1.5mm;
  text-align: center;
}
table.answers th { background: #eef2f6; font-weight: 700 }
.answer-note { margin: 2.5mm 0 0; color: #616e7c; font-size: 8.5pt }
.footer { margin-top: 3mm; text-align: center; color: #9aa5b1; font-size: 8pt }
@media print {
  body { background: #ffffff }
  .page { margin: 0; page-break-after: always }
  .page:last-child { page-break-after: auto }
}
"""


@dataclass(frozen=True)
class _Marker:
    """SVG 上要标注的一个点。"""

    label: str
    lon: int
    lat: int
    css_class: str


def _svg_xy(lon: int, lat: int, bounds: Bounds) -> tuple[float, float]:
    """把经纬度换算为 SVG 坐标（y 轴翻转，北在上）。"""
    fx, fy = project(lon, lat, bounds)
    inner_w = SVG_WIDTH - PAD_LEFT - PAD_RIGHT
    inner_h = SVG_HEIGHT - PAD_TOP - PAD_BOTTOM
    return (PAD_LEFT + fx * inner_w, PAD_TOP + (1.0 - fy) * inner_h)


def _render_marker(marker: _Marker, bounds: Bounds) -> str:
    """渲染单个编号点位。"""
    x, y = _svg_xy(marker.lon, marker.lat, bounds)
    label = escape(marker.label, quote=True)
    css_class = escape(marker.css_class, quote=True)
    return (
        f'<g class="marker {css_class}">'
        f'<circle class="marker-circle" cx="{x:.2f}" cy="{y:.2f}" r="11"/>'
        f'<text class="marker-text" x="{x:.2f}" y="{y:.2f}" '
        f'text-anchor="middle" dominant-baseline="central">{label}</text>'
        "</g>"
    )


def _render_svg(bounds: Bounds, step: int, markers: Sequence[_Marker]) -> str:
    """渲染经纬网 SVG：网格线、四周刻度、赤道与本初子午线、点位。"""
    lat_min, lat_max, lon_min, lon_max = bounds
    inner_w = SVG_WIDTH - PAD_LEFT - PAD_RIGHT
    inner_h = SVG_HEIGHT - PAD_TOP - PAD_BOTTOM

    parts: list[str] = [
        (
            f'<svg class="grid-svg" viewBox="0 0 {SVG_WIDTH:.0f} {SVG_HEIGHT:.0f}" '
            'xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="{escape("经纬网练习图", quote=True)}">'
        ),
        f'<rect x="0" y="0" width="{SVG_WIDTH:.0f}" height="{SVG_HEIGHT:.0f}" fill="#ffffff"/>',
    ]

    lat_ticks = ticks(lat_min, lat_max, step)
    lon_ticks = ticks(lon_min, lon_max, step)

    for lat_tick in lat_ticks:
        if lat_tick == 0:
            continue
        _, y = _svg_xy(lon_min, lat_tick, bounds)
        parts.append(
            f'<line class="grid-line" x1="{PAD_LEFT:.2f}" y1="{y:.2f}" '
            f'x2="{PAD_LEFT + inner_w:.2f}" y2="{y:.2f}"/>'
        )
    for lon_tick in lon_ticks:
        if lon_tick == 0:
            continue
        x, _ = _svg_xy(lon_tick, lat_min, bounds)
        parts.append(
            f'<line class="grid-line" x1="{x:.2f}" y1="{PAD_TOP:.2f}" '
            f'x2="{x:.2f}" y2="{PAD_TOP + inner_h:.2f}"/>'
        )

    if lat_min <= 0 <= lat_max:
        _, equator_y = _svg_xy(lon_min, 0, bounds)
        parts.append(
            f'<line class="axis-line" x1="{PAD_LEFT:.2f}" y1="{equator_y:.2f}" '
            f'x2="{PAD_LEFT + inner_w:.2f}" y2="{equator_y:.2f}"/>'
        )
        parts.append(
            f'<text class="axis-label" x="{PAD_LEFT + inner_w - 4:.2f}" '
            f'y="{equator_y - 5:.2f}" text-anchor="end">赤道</text>'
        )

    if lon_min <= 0 <= lon_max:
        prime_x, _ = _svg_xy(0, lat_min, bounds)
        parts.append(
            f'<line class="axis-line" x1="{prime_x:.2f}" y1="{PAD_TOP:.2f}" '
            f'x2="{prime_x:.2f}" y2="{PAD_TOP + inner_h:.2f}"/>'
        )
        parts.append(
            f'<text class="axis-label" x="{prime_x + 5:.2f}" y="{PAD_TOP + 15:.2f}" '
            'text-anchor="start">本初子午线</text>'
        )

    for lat_tick in lat_ticks:
        _, y = _svg_xy(lon_min, lat_tick, bounds)
        label = escape(format_lat(lat_tick))
        parts.append(
            f'<text class="tick-label" x="{PAD_LEFT - 10:.2f}" y="{y + 4:.2f}" '
            f'text-anchor="end">{label}</text>'
        )
        parts.append(
            f'<text class="tick-label" x="{PAD_LEFT + inner_w + 10:.2f}" y="{y + 4:.2f}" '
            f'text-anchor="start">{label}</text>'
        )

    for lon_tick in lon_ticks:
        x, _ = _svg_xy(lon_tick, lat_min, bounds)
        label = escape(format_lon(lon_tick))
        parts.append(
            f'<text class="tick-label" x="{x:.2f}" y="{PAD_TOP - 12:.2f}" '
            f'text-anchor="middle">{label}</text>'
        )
        parts.append(
            f'<text class="tick-label" x="{x:.2f}" y="{PAD_TOP + inner_h + 20:.2f}" '
            f'text-anchor="middle">{label}</text>'
        )

    for marker in markers:
        if not (lat_min <= marker.lat <= lat_max and lon_min <= marker.lon <= lon_max):
            continue
        parts.append(_render_marker(marker, bounds))

    parts.append(
        f'<rect class="map-frame" x="{PAD_LEFT:.2f}" y="{PAD_TOP:.2f}" '
        f'width="{inner_w:.2f}" height="{inner_h:.2f}"/>'
    )
    parts.append("</svg>")
    return "".join(parts)


def _render_questions(questions: Sequence[Question]) -> str:
    """渲染题目列表：plot 给坐标，read 标点位并留作答线。"""
    if not questions:
        return '<p class="empty">暂无题目，请调整参数后重试。</p>'

    items: list[str] = []
    for index, question in enumerate(questions, start=1):
        city_name = escape(question.city.name)
        coordinate = f"{format_lat(question.lat)}，{format_lon(question.lon)}"
        if question.kind == "plot":
            body = (
                f"请在图中标出坐标为 <strong>{coordinate}</strong> 的位置"
                f"（{city_name}）。"
            )
        else:
            body = (
                f"图中 <strong>{index}</strong> 号点标出了 {city_name}，"
                '请写出它的坐标：纬度 <span class="blank"></span>，'
                '经度 <span class="blank"></span>。'
            )
        items.append(
            f'<li class="question {escape(question.kind, quote=True)}">'
            f'<span class="q-no">{index}.</span>'
            f'<span class="q-body">{body}</span>'
            "</li>"
        )
    return '<ol class="questions">' + "".join(items) + "</ol>"


def _render_answers(questions: Sequence[Question], bounds: Bounds, step: int) -> str:
    """渲染答案页：点位图、坐标表与半球信息。"""
    markers = [
        _Marker(str(index), question.lon, question.lat, "answer-marker")
        for index, question in enumerate(questions, start=1)
    ]
    svg = _render_svg(bounds, step, markers)

    rows: list[str] = []
    for index, question in enumerate(questions, start=1):
        kind_text = "找位置" if question.kind == "plot" else "写坐标"
        rows.append(
            "<tr>"
            f"<td>{index}</td>"
            f"<td>{escape(question.city.name)}</td>"
            f"<td>{format_lat(question.lat)}</td>"
            f"<td>{format_lon(question.lon)}</td>"
            f"<td>{hemisphere(question.lat, question.lon)}</td>"
            f"<td>{kind_text}</td>"
            "</tr>"
        )

    return (
        '<div class="map-wrap answer-map">'
        f"{svg}"
        "</div>"
        '<table class="answers">'
        "<thead><tr>"
        "<th>题号</th><th>城市</th><th>纬度</th><th>经度</th><th>半球</th><th>题型</th>"
        "</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
        '<p class="answer-note">'
        "说明：赤道（0° 纬线）按惯例归入北半球，"
        "本初子午线（0° 经线）按惯例归入东半球。"
        "</p>"
    )


def _render_document(title: str, body: str) -> str:
    """拼装完整的 HTML 文档。"""
    safe_title = escape(title)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{safe_title}</title>\n"
        f"<style>{PAGE_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        f"{body}\n"
        "</body>\n"
        "</html>\n"
    )


def render_worksheet(
    bounds: Bounds,
    step: int,
    questions: list[Question],
    title: str = "经纬网练习",
    show_answers: bool = True,
) -> str:
    """生成完整的 A4 练习纸 HTML；show_answers 控制是否追加答案页。"""
    lat_min, lat_max, lon_min, lon_max = _unpack_bounds(bounds)
    validate_bounds(lat_min, lat_max, lon_min, lon_max, step)

    if not isinstance(questions, list):
        raise CoordError("题目列表必须是列表")
    for question in questions:
        if not isinstance(question, Question):
            raise CoordError("题目列表中的每一项都必须是 Question 实例")
        if not lat_min <= question.lat <= lat_max:
            raise CoordError(f"题目「{question.city.name}」的纬度超出当前范围")
        if not lon_min <= question.lon <= lon_max:
            raise CoordError(f"题目「{question.city.name}」的经度超出当前范围")
    if not isinstance(title, str) or not title.strip():
        raise CoordError("标题必须是非空字符串")

    safe_title = escape(title)
    read_markers = [
        _Marker(str(index), question.lon, question.lat, "read-marker")
        for index, question in enumerate(questions, start=1)
        if question.kind == "read"
    ]
    worksheet_svg = _render_svg(bounds, step, read_markers)
    questions_html = _render_questions(questions)
    subtitle = (
        f"纬度 {format_lat(lat_min)} 至 {format_lat(lat_max)}，"
        f"经度 {format_lon(lon_min)} 至 {format_lon(lon_max)}"
    )

    pages: list[str] = [
        '<section class="page worksheet">'
        '<div class="content">'
        f"<h1>{safe_title}</h1>"
        f'<p class="subtitle">经纬网练习纸 · {subtitle}</p>'
        f'<div class="map-wrap">{worksheet_svg}</div>'
        '<p class="hint">提示：赤道与本初子午线已加粗；'
        "纬度刻度标注在左右两侧，经度刻度标注在上下两侧。</p>"
        "<h2>练习</h2>"
        f"{questions_html}"
        '<div class="footer">mapgrid · eastyou</div>'
        "</div>"
        "</section>"
    ]

    if show_answers:
        pages.append(
            '<section class="page answers">'
            '<div class="content">'
            "<h1>参考答案</h1>"
            f'<p class="subtitle">{safe_title} · 共 {len(questions)} 道题</p>'
            f"{_render_answers(questions, bounds, step)}"
            '<div class="footer">mapgrid · eastyou</div>'
            "</div>"
            "</section>"
        )

    return _render_document(title, "\n".join(pages))
