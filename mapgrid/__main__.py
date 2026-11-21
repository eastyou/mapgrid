from __future__ import annotations

"""允许通过 `python -m mapgrid` 运行命令行。"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
