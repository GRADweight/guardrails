"""Alle Python-Codeblöcke der README werden ausgeführt, CLI-Zeilen ebenfalls."""

from __future__ import annotations

import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text("utf-8")
PYTHON_BLOCKS = re.findall(r"```python\n(.*?)```", README, flags=re.DOTALL)
CLI_LINES = [
    line.strip()
    for block in re.findall(r"```bash\n(.*?)```", README, flags=re.DOTALL)
    for line in block.splitlines()
    if line.strip().startswith("python -m gradweight_guardrails")
]


def test_readme_has_examples() -> None:
    assert len(PYTHON_BLOCKS) >= 6
    assert len(CLI_LINES) >= 3


@pytest.mark.parametrize("code", PYTHON_BLOCKS, ids=[f"block{i}" for i in range(len(PYTHON_BLOCKS))])
def test_python_block_runs(code: str, capsys: pytest.CaptureFixture[str]) -> None:
    exec(compile(code, "README.md", "exec"), {"__name__": "readme_example"})  # noqa: S102


@pytest.mark.parametrize("line", CLI_LINES)
def test_cli_line_runs(line: str) -> None:
    args = shlex.split(line)
    result = subprocess.run([sys.executable, *args[1:]], capture_output=True, text=True, check=False, cwd=ROOT)
    assert result.returncode in (0, 3, 4), result.stderr
    assert result.stdout
