# mapgrid 经纬网练习纸

[![CI](https://github.com/eastyou/mapgrid/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/mapgrid/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)


`mapgrid` 是一个零第三方依赖的 Python 小工具，用来生成可直接打印的 A4 经纬网练习纸：
主图是带四边刻度的 SVG 经纬网格，下方自动配「找坐标 / 写坐标」练习题，并可附加答案页。
适合地理课堂、教师备课与学生自测。

- 经纬范围、网格步长、题目数量均可配置
- 纬度刻度在左右两侧，经度刻度在上下两侧
- 赤道与本初子午线自动加粗并标注
- `plot` 题给坐标找位置，`read` 题标点位写坐标
- 答案为独立页面：点位图、坐标表与半球信息
- 纯标准库实现，支持 Python 3.9+

## 安装

```bash
python -m pip install -e .
```

也可以不安装，直接在仓库根目录运行：

```bash
python -m mapgrid --help
```

## 快速开始

生成默认练习纸（8 道题，含答案页）：

```bash
mapgrid -o worksheet.html --seed 7
```

生成不带答案页的版本：

```bash
mapgrid -o worksheet.html --seed 7 --no-answers
```

自定义范围、步长与题量：

```bash
mapgrid -o worksheet.html \
  --lat-min 0 --lat-max 60 --lon-min 60 --lon-max 150 \
  --step 10 --questions 6 --seed 42 --title "亚洲经纬网练习"
```

## 命令行参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `-o, --output` | `mapgrid.html` | 输出 HTML 文件路径 |
| `--lat-min` | `-60` | 纬度最小值，范围 -90 到 90 |
| `--lat-max` | `60` | 纬度最大值，范围 -90 到 90 |
| `--lon-min` | `-180` | 经度最小值，范围 -180 到 180 |
| `--lon-max` | `180` | 经度最大值，范围 -180 到 180 |
| `--step` | `15` | 经纬网格步长，范围 1 到 90 |
| `--questions` | `8` | 题目数量，范围 1 到 20 |
| `--seed` | 无 | 随机种子，指定后题目可复现 |
| `--no-answers` | 关闭 | 不生成答案页 |
| `--title` | `经纬网练习` | 练习纸标题，最长 80 个字符 |

负经度表示西经，负纬度表示南纬，例如纽约为 `41N, 74W`，即 `lat=41, lon=-74`。

## 半球判定约定

- 赤道（0° 纬线）按地理惯例归入**北半球**
- 本初子午线（0° 经线）按地理惯例归入**东半球**
- 其余情况：纬度大于 0 为北半球，小于 0 为南半球；经度大于 0 为东半球，小于 0 为西半球

答案页底部也会印有这条说明，方便学生对照。

## 退出码

| 退出码 | 含义 |
| --- | --- |
| `0` | 生成成功 |
| `1` | 写文件失败（如目录不存在、路径是目录） |
| `2` | 参数非法（范围、步长、题量、标题、可选城市不足等） |

参数错误会以中文提示输出到标准错误。

## Python API

```python
from mapgrid import generate_questions, render_worksheet

bounds = (-60, 60, -180, 180)  # (lat_min, lat_max, lon_min, lon_max)
questions = generate_questions(8, bounds, seed=7)
html = render_worksheet(bounds, 15, questions, title="经纬网练习")
with open("worksheet.html", "w", encoding="utf-8") as file:
    file.write(html)
```

`render_worksheet(..., show_answers=False)` 可关闭答案页；所有面向外部输入的非法参数都会抛出
`CoordError`（`ValueError` 的子类）。

## 示例文件

- [examples/mapgrid.html](examples/mapgrid.html)：练习页（不含答案）
- [examples/mapgrid-answers.html](examples/mapgrid-answers.html)：练习页 + 答案页

## 项目结构

```
mapgrid/
├── pyproject.toml
├── LICENSE
├── README.md
├── .github/workflows/ci.yml
├── mapgrid/
│   ├── __init__.py
│   ├── __main__.py
│   ├── model.py      # 校验、刻度、投影、城市与题目生成
│   ├── render.py     # A4 HTML / SVG 渲染
│   └── cli.py        # 命令行入口
├── tests/
│   ├── test_model.py
│   ├── test_render.py
│   └── test_cli.py
└── examples/
```

## 测试

```bash
python -m unittest discover -s tests -v
```

CI 会在 Ubuntu、macOS、Windows 以及 Python 3.9 / 3.10 / 3.13 上运行单元测试与命令行冒烟测试。

## 许可证

MIT，详见 [LICENSE](LICENSE)。Copyright (c) 2026 eastyou。
