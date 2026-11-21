from __future__ import annotations

"""cli 模块的单元测试。"""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from mapgrid.cli import main


class CliTestCase(unittest.TestCase):
    """提供临时目录与命令行输出捕获。"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)

    def run_cli(self, argv: list[str]) -> tuple[int, str, str]:
        """执行 main 并返回 (退出码, stdout, stderr)。"""
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def output_path(self, name: str = "worksheet.html") -> Path:
        """返回临时目录中的输出路径。"""
        return self.root / name


class CliSuccessTests(CliTestCase):
    """成功路径。"""

    def test_success_writes_file(self) -> None:
        path = self.output_path()
        code, stdout, stderr = self.run_cli(
            ["-o", str(path), "--questions", "4", "--seed", "3"]
        )
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(path.exists())
        content = path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("<!DOCTYPE html>"))
        self.assertIn("已生成", stdout)
        self.assertIn("4 道题", stdout)
        self.assertIn(str(path), stdout)

    def test_default_answers_included(self) -> None:
        path = self.output_path("answers.html")
        code, _, _ = self.run_cli(["-o", str(path), "--seed", "1"])
        self.assertEqual(code, 0)
        self.assertIn("参考答案", path.read_text(encoding="utf-8"))

    def test_no_answers_flag(self) -> None:
        path = self.output_path("plain.html")
        code, _, _ = self.run_cli(["-o", str(path), "--no-answers", "--seed", "1"])
        self.assertEqual(code, 0)
        self.assertNotIn("参考答案", path.read_text(encoding="utf-8"))

    def test_same_seed_same_output(self) -> None:
        first = self.output_path("first.html")
        second = self.output_path("second.html")
        code1, _, _ = self.run_cli(["-o", str(first), "--seed", "9"])
        code2, _, _ = self.run_cli(["-o", str(second), "--seed", "9"])
        self.assertEqual((code1, code2), (0, 0))
        self.assertEqual(
            first.read_text(encoding="utf-8"),
            second.read_text(encoding="utf-8"),
        )

    def test_custom_title(self) -> None:
        path = self.output_path("title.html")
        code, _, _ = self.run_cli(
            ["-o", str(path), "--title", "地理小测", "--seed", "1"]
        )
        self.assertEqual(code, 0)
        self.assertIn("地理小测", path.read_text(encoding="utf-8"))

    def test_default_question_count(self) -> None:
        path = self.output_path("default.html")
        code, stdout, _ = self.run_cli(["-o", str(path)])
        self.assertEqual(code, 0)
        self.assertIn("8 道题", stdout)

    def test_help_returns_zero(self) -> None:
        code, stdout, _ = self.run_cli(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("usage", stdout)
        self.assertIn("mapgrid", stdout)


class CliValidationTests(CliTestCase):
    """参数校验失败时返回 2。"""

    def assert_invalid(self, argv: list[str]) -> str:
        """断言退出码为 2 且 stderr 含中文错误，返回 stderr。"""
        code, _, stderr = self.run_cli(argv)
        self.assertEqual(code, 2)
        self.assertIn("错误", stderr)
        return stderr

    def test_lat_out_of_range(self) -> None:
        stderr = self.assert_invalid(["--lat-min", "-91"])
        self.assertIn("纬度", stderr)

    def test_lat_max_out_of_range(self) -> None:
        self.assert_invalid(["--lat-max", "91"])

    def test_lon_out_of_range(self) -> None:
        self.assert_invalid(["--lon-min", "-181"])

    def test_lon_max_out_of_range(self) -> None:
        self.assert_invalid(["--lon-max", "181"])

    def test_reversed_latitude_bounds(self) -> None:
        stderr = self.assert_invalid(["--lat-min", "50", "--lat-max", "10"])
        self.assertIn("小于", stderr)

    def test_reversed_longitude_bounds(self) -> None:
        self.assert_invalid(["--lon-min", "120", "--lon-max", "20"])

    def test_step_zero(self) -> None:
        stderr = self.assert_invalid(["--step", "0"])
        self.assertIn("步长", stderr)

    def test_step_too_large(self) -> None:
        self.assert_invalid(["--step", "91"])

    def test_questions_zero(self) -> None:
        stderr = self.assert_invalid(["--questions", "0"])
        self.assertIn("题目数量", stderr)

    def test_questions_too_many(self) -> None:
        self.assert_invalid(["--questions", "21"])

    def test_non_integer_argument(self) -> None:
        stderr = self.assert_invalid(["--lat-min", "abc"])
        self.assertIn("整数", stderr)

    def test_unknown_option(self) -> None:
        stderr = self.assert_invalid(["--unknown"])
        self.assertIn("无法识别", stderr)

    def test_missing_option_value(self) -> None:
        stderr = self.assert_invalid(["--lat-min"])
        self.assertIn("需要一个取值", stderr)

    def test_empty_title(self) -> None:
        self.assert_invalid(["--title", "   "])

    def test_no_city_in_range(self) -> None:
        stderr = self.assert_invalid(
            ["--lat-min", "80", "--lat-max", "85", "--lon-min", "10", "--lon-max", "20"]
        )
        self.assertIn("没有可选城市", stderr)

    def test_not_enough_cities(self) -> None:
        stderr = self.assert_invalid(
            [
                "--lat-min",
                "20",
                "--lat-max",
                "25",
                "--lon-min",
                "110",
                "--lon-max",
                "115",
                "--questions",
                "5",
            ]
        )
        self.assertIn("不足以", stderr)

    def test_invalid_input_creates_no_file(self) -> None:
        path = self.output_path("bad.html")
        self.assert_invalid(["-o", str(path), "--step", "0"])
        self.assertFalse(path.exists())


class CliWriteFailureTests(CliTestCase):
    """写文件失败时返回 1。"""

    def test_missing_parent_directory(self) -> None:
        path = self.root / "missing" / "out.html"
        code, stdout, stderr = self.run_cli(["-o", str(path), "--seed", "1"])
        self.assertEqual(code, 1)
        self.assertIn("写入文件失败", stderr)
        self.assertEqual(stdout, "")

    def test_output_is_directory(self) -> None:
        code, _, stderr = self.run_cli(["-o", str(self.root), "--seed", "1"])
        self.assertEqual(code, 1)
        self.assertIn("写入文件失败", stderr)


if __name__ == "__main__":
    unittest.main()
