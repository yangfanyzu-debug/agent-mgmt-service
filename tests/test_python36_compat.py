import ast
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class Python36CompatTests(unittest.TestCase):
    def test_app_sources_parse_as_python36(self):
        for path in (ROOT / "app").rglob("*.py"):
            source = path.read_text(encoding="utf-8")
            if sys.version_info >= (3, 8):
                ast.parse(source, filename=str(path), feature_version=(3, 6))
            else:
                ast.parse(source, filename=str(path))


if __name__ == "__main__":
    unittest.main()
