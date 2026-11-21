from __future__ import annotations

"""render 模块的单元测试。"""

import unittest

from mapgrid.model import Bounds, CityPoint, CoordError, Question, generate_questions
from mapgrid.render import render_worksheet

DEFAULT_BOUNDS: Bounds = (-60, 60, -180, 180)


def sample_questions(count: int = 4) -> list[Question]:
    """生成用于渲染测试的确定性题目。"""
    return generate_questions(count, DEFAULT_BOUNDS, seed=7)


def single_question(kind: str, name: str = "测试城", lat: int = 10, lon: int = 20) -> list[Question]:
    """构造单道指定类型的题目。"""
    city = CityPoint(name, lat, lon)
    return [Question(city=city, lat=lat, lon=lon, kind=kind)]


class RenderBasicsTests(unittest.TestCase):
    """HTML 骨架、A4 排版与 SVG 网格。"""

    def setUp(self) -> None:
        self.html = render_worksheet(DEFAULT_BOUNDS, 15, sample_questions())

    def test_html_document_structure(self) -> None:
        self.assertTrue(self.html.startswith("<!DOCTYPE html>"))
        self.assertIn('<html lang="zh-CN">', self.html)
        self.assertIn('<meta charset="utf-8">', self.html)

    def test_a4_css(self) -> None:
        self.assertIn("@page { size: A4; margin: 0 }", self.html)
        self.assertIn("width: 210mm", self.html)
        self.assertIn("min-height: 297mm", self.html)
        self.assertIn("padding: 12mm", self.html)
        self.assertIn("width: 98%", self.html)

    def test_svg_grid_lines(self) -> None:
        self.assertGreaterEqual(self.html.count('class="grid-line"'), 20)
        self.assertIn('class="map-frame"', self.html)
        self.assertIn("grid-svg", self.html)

    def test_lat_tick_labels(self) -> None:
        self.assertIn(">60°N<", self.html)
        self.assertIn(">60°S<", self.html)
        self.assertIn(">45°N<", self.html)
        self.assertIn(">0°<", self.html)

    def test_lon_tick_labels(self) -> None:
        self.assertIn(">180°E<", self.html)
        self.assertIn(">180°W<", self.html)
        self.assertIn(">120°E<", self.html)
        self.assertIn(">0°<", self.html)

    def test_axis_lines_present(self) -> None:
        no_answers = render_worksheet(
            DEFAULT_BOUNDS, 15, sample_questions(), show_answers=False
        )
        self.assertEqual(no_answers.count('class="axis-line"'), 2)
        self.assertIn("赤道", no_answers)
        self.assertIn("本初子午线", no_answers)

    def test_axis_hidden_outside_bounds(self) -> None:
        bounds: Bounds = (20, 50, 60, 140)
        html = render_worksheet(
            bounds, 10, generate_questions(2, bounds, seed=1), show_answers=False
        )
        self.assertNotIn('<text class="axis-label"', html)


class RenderQuestionTests(unittest.TestCase):
    """题目列表的两种题型。"""

    def test_plot_prompt_has_coordinates(self) -> None:
        html = render_worksheet(
            DEFAULT_BOUNDS, 15, single_question("plot"), show_answers=False
        )
        self.assertIn("请在图中标出坐标为", html)
        self.assertIn("10°N，20°E", html)
        self.assertIn("测试城", html)
        self.assertNotIn('<span class="blank"></span>', html)

    def test_read_prompt_has_blanks(self) -> None:
        html = render_worksheet(
            DEFAULT_BOUNDS, 15, single_question("read"), show_answers=False
        )
        self.assertIn("请写出它的坐标", html)
        self.assertEqual(html.count('<span class="blank"></span>'), 2)
        self.assertIn('class="marker read-marker"', html)
        self.assertIn('class="marker-text"', html)

    def test_plot_question_not_marked(self) -> None:
        html = render_worksheet(
            DEFAULT_BOUNDS, 15, single_question("plot"), show_answers=False
        )
        self.assertNotIn('class="marker read-marker"', html)
        self.assertNotIn('class="marker answer-marker"', html)

    def test_question_numbering(self) -> None:
        html = render_worksheet(
            DEFAULT_BOUNDS, 15, sample_questions(4), show_answers=False
        )
        self.assertIn('<span class="q-no">1.</span>', html)
        self.assertIn('<span class="q-no">2.</span>', html)
        self.assertIn('<span class="q-no">3.</span>', html)
        self.assertIn('<span class="q-no">4.</span>', html)

    def test_empty_question_list(self) -> None:
        html = render_worksheet(DEFAULT_BOUNDS, 15, [], show_answers=False)
        self.assertIn("暂无题目", html)


class RenderAnswerTests(unittest.TestCase):
    """答案页开关与答案内容。"""

    def test_answers_page_by_default(self) -> None:
        html = render_worksheet(DEFAULT_BOUNDS, 15, sample_questions(4))
        self.assertIn("参考答案", html)
        self.assertIn('<table class="answers">', html)
        self.assertIn("半球", html)
        self.assertIn("北半球", html)
        self.assertIn('class="marker answer-marker"', html)

    def test_answers_page_contains_question_types(self) -> None:
        html = render_worksheet(DEFAULT_BOUNDS, 15, sample_questions(4))
        self.assertIn("找位置", html)
        self.assertIn("写坐标", html)

    def test_answers_disabled(self) -> None:
        html = render_worksheet(
            DEFAULT_BOUNDS, 15, sample_questions(4), show_answers=False
        )
        self.assertNotIn("参考答案", html)
        self.assertNotIn('class="marker answer-marker"', html)
        self.assertNotIn("南半球", html)

    def test_answer_table_has_city_and_hemisphere(self) -> None:
        city = CityPoint("北京", 40, 116)
        questions = [Question(city=city, lat=40, lon=116, kind="read")]
        html = render_worksheet(DEFAULT_BOUNDS, 15, questions)
        self.assertIn("北京", html)
        self.assertIn("北半球 东半球", html)

    def test_answer_note_documents_convention(self) -> None:
        html = render_worksheet(DEFAULT_BOUNDS, 15, sample_questions(2))
        self.assertIn("赤道（0° 纬线）按惯例归入北半球", html)
        self.assertIn("本初子午线（0° 经线）按惯例归入东半球", html)


class RenderEscapingTests(unittest.TestCase):
    """外部文本必须 HTML 转义。"""

    def test_title_escaped(self) -> None:
        html = render_worksheet(
            DEFAULT_BOUNDS,
            15,
            sample_questions(2),
            title='<script>alert("x")</script>',
        )
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_city_name_escaped(self) -> None:
        questions = single_question("plot", name="<b>危险</b>")
        html = render_worksheet(DEFAULT_BOUNDS, 15, questions)
        self.assertNotIn("<b>危险</b>", html)
        self.assertIn("&lt;b&gt;危险&lt;/b&gt;", html)

    def test_empty_title_rejected(self) -> None:
        with self.assertRaises(CoordError):
            render_worksheet(DEFAULT_BOUNDS, 15, sample_questions(2), title="   ")


class RenderValidationTests(unittest.TestCase):
    """渲染参数校验。"""

    def test_invalid_step(self) -> None:
        with self.assertRaises(CoordError):
            render_worksheet(DEFAULT_BOUNDS, 0, sample_questions(2))

    def test_invalid_bounds(self) -> None:
        with self.assertRaises(CoordError):
            render_worksheet((0, 0, -180, 180), 15, [])

    def test_question_out_of_bounds(self) -> None:
        city = CityPoint("城外", 80, 10)
        questions = [Question(city=city, lat=80, lon=10, kind="plot")]
        with self.assertRaises(CoordError):
            render_worksheet(DEFAULT_BOUNDS, 15, questions)

    def test_question_type_checked(self) -> None:
        with self.assertRaises(CoordError):
            render_worksheet(DEFAULT_BOUNDS, 15, ["bad"])  # type: ignore[list-item]

    def test_questions_must_be_list(self) -> None:
        with self.assertRaises(CoordError):
            render_worksheet(DEFAULT_BOUNDS, 15, ())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
