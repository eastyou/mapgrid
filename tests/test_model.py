from __future__ import annotations

"""model 模块的单元测试。"""

import unittest

from mapgrid.model import (
    CITIES,
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

DEFAULT_BOUNDS = (-60, 60, -180, 180)


class FormatLatTests(unittest.TestCase):
    """format_lat 的分支覆盖。"""

    def test_zero(self) -> None:
        self.assertEqual(format_lat(0), "0°")

    def test_positive(self) -> None:
        self.assertEqual(format_lat(30), "30°N")

    def test_negative(self) -> None:
        self.assertEqual(format_lat(-30), "30°S")

    def test_positive_boundary(self) -> None:
        self.assertEqual(format_lat(90), "90°N")

    def test_negative_boundary(self) -> None:
        self.assertEqual(format_lat(-90), "90°S")

    def test_too_large(self) -> None:
        with self.assertRaises(CoordError):
            format_lat(91)

    def test_too_small(self) -> None:
        with self.assertRaises(CoordError):
            format_lat(-91)

    def test_non_integer(self) -> None:
        for value in (30.0, "30", True):
            with self.subTest(value=value):
                with self.assertRaises(CoordError):
                    format_lat(value)  # type: ignore[arg-type]


class FormatLonTests(unittest.TestCase):
    """format_lon 的分支覆盖。"""

    def test_zero(self) -> None:
        self.assertEqual(format_lon(0), "0°")

    def test_east(self) -> None:
        self.assertEqual(format_lon(120), "120°E")

    def test_west(self) -> None:
        self.assertEqual(format_lon(-60), "60°W")

    def test_positive_boundary(self) -> None:
        self.assertEqual(format_lon(180), "180°E")

    def test_negative_boundary(self) -> None:
        self.assertEqual(format_lon(-180), "180°W")

    def test_too_large(self) -> None:
        with self.assertRaises(CoordError):
            format_lon(181)

    def test_too_small(self) -> None:
        with self.assertRaises(CoordError):
            format_lon(-181)

    def test_non_integer(self) -> None:
        for value in (12.5, "12", False):
            with self.subTest(value=value):
                with self.assertRaises(CoordError):
                    format_lon(value)  # type: ignore[arg-type]


class HemisphereTests(unittest.TestCase):
    """hemisphere 的四种组合与边界。"""

    def test_north_east(self) -> None:
        self.assertEqual(hemisphere(40, 116), "北半球 东半球")

    def test_north_west(self) -> None:
        self.assertEqual(hemisphere(40, -74), "北半球 西半球")

    def test_south_east(self) -> None:
        self.assertEqual(hemisphere(-34, 151), "南半球 东半球")

    def test_south_west(self) -> None:
        self.assertEqual(hemisphere(-23, -43), "南半球 西半球")

    def test_equator_and_prime_meridian(self) -> None:
        self.assertEqual(hemisphere(0, 0), "北半球 东半球")

    def test_boundaries(self) -> None:
        self.assertEqual(hemisphere(90, 180), "北半球 东半球")
        self.assertEqual(hemisphere(-90, -180), "南半球 西半球")

    def test_invalid_value(self) -> None:
        with self.assertRaises(CoordError):
            hemisphere(91, 0)
        with self.assertRaises(CoordError):
            hemisphere(0, -181)


class ValidateBoundsTests(unittest.TestCase):
    """validate_bounds 的合法与非法情况。"""

    def test_default_bounds_valid(self) -> None:
        self.assertIsNone(validate_bounds(-60, 60, -180, 180, 15))

    def test_full_bounds_valid(self) -> None:
        self.assertIsNone(validate_bounds(-90, 90, -180, 180, 1))

    def test_lat_min_too_small(self) -> None:
        with self.assertRaises(CoordError):
            validate_bounds(-91, 60, -180, 180, 15)

    def test_lat_max_too_large(self) -> None:
        with self.assertRaises(CoordError):
            validate_bounds(-60, 91, -180, 180, 15)

    def test_lon_min_too_small(self) -> None:
        with self.assertRaises(CoordError):
            validate_bounds(-60, 60, -181, 180, 15)

    def test_lon_max_too_large(self) -> None:
        with self.assertRaises(CoordError):
            validate_bounds(-60, 60, -180, 181, 15)

    def test_lat_min_equals_lat_max(self) -> None:
        with self.assertRaises(CoordError):
            validate_bounds(10, 10, -180, 180, 15)

    def test_lat_reversed(self) -> None:
        with self.assertRaises(CoordError):
            validate_bounds(40, 10, -180, 180, 15)

    def test_lon_min_equals_lon_max(self) -> None:
        with self.assertRaises(CoordError):
            validate_bounds(-60, 60, 20, 20, 15)

    def test_lon_reversed(self) -> None:
        with self.assertRaises(CoordError):
            validate_bounds(-60, 60, 120, 20, 15)

    def test_step_zero(self) -> None:
        with self.assertRaises(CoordError):
            validate_bounds(-60, 60, -180, 180, 0)

    def test_step_negative(self) -> None:
        with self.assertRaises(CoordError):
            validate_bounds(-60, 60, -180, 180, -15)

    def test_step_too_large(self) -> None:
        with self.assertRaises(CoordError):
            validate_bounds(-60, 60, -180, 180, 91)

    def test_step_non_integer(self) -> None:
        with self.assertRaises(CoordError):
            validate_bounds(-60, 60, -180, 180, 15.0)  # type: ignore[arg-type]


class TicksTests(unittest.TestCase):
    """ticks 的端点包含与非法参数。"""

    def test_basic_sequence(self) -> None:
        self.assertEqual(ticks(-60, 60, 15), [-60, -45, -30, -15, 0, 15, 30, 45, 60])

    def test_includes_end_when_not_aligned(self) -> None:
        self.assertEqual(ticks(0, 10, 3), [0, 3, 6, 9, 10])

    def test_single_value(self) -> None:
        self.assertEqual(ticks(5, 5, 1), [5])

    def test_step_equals_span(self) -> None:
        self.assertEqual(ticks(0, 90, 90), [0, 90])

    def test_start_greater_than_end(self) -> None:
        with self.assertRaises(CoordError):
            ticks(10, 0, 5)

    def test_step_zero(self) -> None:
        with self.assertRaises(CoordError):
            ticks(0, 10, 0)

    def test_step_negative(self) -> None:
        with self.assertRaises(CoordError):
            ticks(0, 10, -1)

    def test_non_integer(self) -> None:
        with self.assertRaises(CoordError):
            ticks(0.0, 10, 1)  # type: ignore[arg-type]


class ProjectTests(unittest.TestCase):
    """project 的四个角点、中心点与越界行为。"""

    def setUp(self) -> None:
        self.bounds = (10, 50, 20, 80)

    def test_bottom_left(self) -> None:
        self.assertEqual(project(20, 10, self.bounds), (0.0, 0.0))

    def test_top_right(self) -> None:
        self.assertEqual(project(80, 50, self.bounds), (1.0, 1.0))

    def test_top_left(self) -> None:
        self.assertEqual(project(20, 50, self.bounds), (0.0, 1.0))

    def test_bottom_right(self) -> None:
        self.assertEqual(project(80, 10, self.bounds), (1.0, 0.0))

    def test_center(self) -> None:
        self.assertEqual(project(50, 30, self.bounds), (0.5, 0.5))

    def test_lat_out_of_bounds(self) -> None:
        with self.assertRaises(CoordError):
            project(50, 60, self.bounds)

    def test_lon_out_of_bounds(self) -> None:
        with self.assertRaises(CoordError):
            project(90, 30, self.bounds)

    def test_bad_bounds_shape(self) -> None:
        with self.assertRaises(CoordError):
            project(0, 0, (0, 10, 20))  # type: ignore[arg-type]

    def test_bad_bounds_values(self) -> None:
        with self.assertRaises(CoordError):
            project(0, 0, (10, 10, 20, 80))


class CityTests(unittest.TestCase):
    """CITIES 数据完整性。"""

    def test_at_least_sixteen_cities(self) -> None:
        self.assertGreaterEqual(len(CITIES), 16)

    def test_names_unique(self) -> None:
        names = [city.name for city in CITIES]
        self.assertEqual(len(names), len(set(names)))

    def test_coordinates_legal(self) -> None:
        for city in CITIES:
            with self.subTest(city=city.name):
                self.assertIsInstance(city.lat, int)
                self.assertIsInstance(city.lon, int)
                self.assertGreaterEqual(city.lat, -90)
                self.assertLessEqual(city.lat, 90)
                self.assertGreaterEqual(city.lon, -180)
                self.assertLessEqual(city.lon, 180)

    def test_known_cities(self) -> None:
        mapping = {city.name: (city.lat, city.lon) for city in CITIES}
        self.assertEqual(mapping["北京"], (40, 116))
        self.assertEqual(mapping["上海"], (31, 121))
        self.assertEqual(mapping["纽约"], (41, -74))
        self.assertEqual(mapping["悉尼"], (-34, 151))

    def test_invalid_city(self) -> None:
        with self.assertRaises(CoordError):
            CityPoint("", 10, 20)
        with self.assertRaises(CoordError):
            CityPoint("越界城", 91, 20)
        with self.assertRaises(CoordError):
            CityPoint("越界城", 10, -181)


class QuestionTests(unittest.TestCase):
    """Question 数据校验。"""

    def setUp(self) -> None:
        self.city = CityPoint("测试城", 10, 20)

    def test_valid_kinds(self) -> None:
        plot = Question(city=self.city, lat=10, lon=20, kind="plot")
        read = Question(city=self.city, lat=10, lon=20, kind="read")
        self.assertEqual(plot.kind, "plot")
        self.assertEqual(read.kind, "read")

    def test_invalid_kind(self) -> None:
        with self.assertRaises(CoordError):
            Question(city=self.city, lat=10, lon=20, kind="unknown")

    def test_invalid_city_type(self) -> None:
        with self.assertRaises(CoordError):
            Question(city="测试城", lat=10, lon=20, kind="plot")  # type: ignore[arg-type]

    def test_invalid_lat(self) -> None:
        with self.assertRaises(CoordError):
            Question(city=self.city, lat=95, lon=20, kind="plot")


class GenerateQuestionsTests(unittest.TestCase):
    """generate_questions 的筛选、确定性与异常。"""

    def test_count_and_bounds(self) -> None:
        questions = generate_questions(8, DEFAULT_BOUNDS, seed=1)
        self.assertEqual(len(questions), 8)
        for question in questions:
            with self.subTest(city=question.city.name):
                self.assertTrue(-60 <= question.city.lat <= 60)
                self.assertTrue(-180 <= question.city.lon <= 180)
                self.assertIn(question.city, CITIES)

    def test_deterministic_with_same_seed(self) -> None:
        first = generate_questions(6, DEFAULT_BOUNDS, seed=42)
        second = generate_questions(6, DEFAULT_BOUNDS, seed=42)
        self.assertEqual(
            [(q.city.name, q.kind, q.lat, q.lon) for q in first],
            [(q.city.name, q.kind, q.lat, q.lon) for q in second],
        )

    def test_kinds_include_both(self) -> None:
        questions = generate_questions(4, DEFAULT_BOUNDS, seed=5)
        kinds = [question.kind for question in questions]
        self.assertIn("plot", kinds)
        self.assertIn("read", kinds)

    def test_coordinates_match_city(self) -> None:
        questions = generate_questions(5, DEFAULT_BOUNDS, seed=9)
        for question in questions:
            with self.subTest(city=question.city.name):
                self.assertEqual(question.lat, question.city.lat)
                self.assertEqual(question.lon, question.city.lon)

    def test_seed_none_allowed(self) -> None:
        self.assertEqual(len(generate_questions(3, DEFAULT_BOUNDS)), 3)

    def test_count_zero(self) -> None:
        with self.assertRaises(CoordError):
            generate_questions(0, DEFAULT_BOUNDS)

    def test_count_too_large(self) -> None:
        with self.assertRaises(CoordError):
            generate_questions(21, DEFAULT_BOUNDS)

    def test_count_non_integer(self) -> None:
        with self.assertRaises(CoordError):
            generate_questions(3.5, DEFAULT_BOUNDS)  # type: ignore[arg-type]

    def test_no_city_in_range(self) -> None:
        with self.assertRaises(CoordError) as context:
            generate_questions(1, (80, 85, 10, 20))
        self.assertIn("放宽", str(context.exception))

    def test_not_enough_cities(self) -> None:
        with self.assertRaises(CoordError) as context:
            generate_questions(5, (20, 25, 110, 115))
        self.assertIn("不足以", str(context.exception))

    def test_exact_city_count(self) -> None:
        questions = generate_questions(2, (20, 25, 110, 115), seed=1)
        self.assertEqual(len(questions), 2)
        self.assertEqual({question.city.name for question in questions}, {"广州", "香港"})

    def test_invalid_seed(self) -> None:
        with self.assertRaises(CoordError):
            generate_questions(2, DEFAULT_BOUNDS, seed=1.5)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
