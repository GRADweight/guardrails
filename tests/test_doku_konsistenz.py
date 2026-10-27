"""Doku und Code stimmen überein: generierte Dateien, Zahlen, Links, Lizenz, keine Interna."""

from __future__ import annotations

import importlib.metadata
import re
import subprocess
import sys
from pathlib import Path

import pytest

import gradweight_guardrails
from gradweight_guardrails.decode import DecodeBudget
from gradweight_guardrails.engine import EngineConfig
from gradweight_guardrails.evaluation import load_cases
from gradweight_guardrails.guard import GuardConfig
from gradweight_guardrails.models import Severity
from gradweight_guardrails.normalize import MAX_COMPACT_CHARS

ROOT = Path(__file__).resolve().parent.parent
MARKDOWN = sorted(p for p in ROOT.rglob("*.md") if ".venv" not in p.parts and "node_modules" not in p.parts)


def _read(relative: str) -> str:
    return (ROOT / relative).read_text("utf-8")


def _project_files() -> list[Path]:
    """Versionierte Dateien; ohne Git (z.B. im sdist) alle Dateien ausser Build- und Cache-Ordnern."""
    try:
        result = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
        files = [ROOT / line for line in result.stdout.splitlines() if line]
    except (OSError, subprocess.CalledProcessError):
        files = []
    if not files:
        skip = {".venv", ".git", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache", "dist", "build"}
        files = [p for p in ROOT.rglob("*") if p.is_file() and not skip & set(p.relative_to(ROOT).parts)]
    return [p for p in files if p.is_file()]


def test_generated_documents_are_current() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/generate_reports.py", "--check"], cwd=ROOT, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr


def test_readme_performance_block_matches_report() -> None:
    readme = _read("README.md")
    block = readme.split("<!-- PERF:START -->", 1)[1].split("<!-- PERF:END -->", 1)[0].strip()
    report = _read("bench/PERFORMANCE.md")
    assert block
    for line in block.splitlines():
        assert line in report, line
    assert "Gemessen am" in block
    assert "Systemlast" in block


def test_version_is_consistent() -> None:
    version = gradweight_guardrails.__version__
    assert importlib.metadata.version("gradweight-guardrails") == version
    first_entry = re.search(r"^## \[(\d+\.\d+\.\d+)\]", _read("CHANGELOG.md"), flags=re.MULTILINE)
    assert first_entry is not None
    assert first_entry.group(1) == version
    assert f"`{version}`" in _read("bench/ERGEBNISSE.md")


def test_license_is_plain_mit() -> None:
    text = _read("LICENSE")
    assert text.startswith("MIT License\n\nCopyright (c) 2026 GRADweight GmbH\n")
    assert text.rstrip().endswith("DEALINGS IN THE SOFTWARE.")
    meta = importlib.metadata.metadata("gradweight-guardrails")
    assert meta["License-Expression"] == "MIT"
    classifiers = meta.get_all("Classifier") or []
    assert "Development Status :: 4 - Beta" in classifiers
    assert not any("Production/Stable" in c or c.startswith("License ::") for c in classifiers)
    assert meta["Requires-Python"] == ">=3.11"


def test_numbers_in_docs_match_code() -> None:
    architecture = _read("docs/architektur.md")
    engine, guard = EngineConfig(), GuardConfig()
    expected = [
        f"Tiefe {engine.decode_depth}",
        f"höchstens {engine.max_decoded_segments} Segmente",
        f"{engine.max_decoded_chars:,}".replace(",", " ") + " dekodierte",
        f"{DecodeBudget().max_segment_chars} Zeichen je Segment",
        f"{engine.max_input_chars:,}".replace(",", " ") + ")",
        f"höchstens {MAX_COMPACT_CHARS} Zeichen",
        f"REVIEW ab {guard.review_threshold}",
        f"BLOCK ab\n{guard.block_threshold}",
    ]
    for severity in Severity:
        expected.append(f"{severity.value} {severity.weight}")
    for snippet in expected:
        assert snippet in architecture, snippet
    readme = _read("README.md")
    assert f"Konfidenz ≥ {guard.judge_min_confidence}" in readme
    assert f"über {engine.max_input_chars:,}".replace(",", " ") + " Zeichen" in readme
    assert f"low {Severity.LOW.weight}, medium {Severity.MEDIUM.weight}" in _read("docs/regeln.md")
    holdout = load_cases(ROOT / "bench" / "data" / "holdout.jsonl")
    assert f"{len(holdout)} Holdout-Fälle" in _read("bench/README.md")
    fail_under = re.search(r"fail_under = (\d+)", _read("pyproject.toml"))
    assert fail_under is not None
    assert f"mindestens {fail_under.group(1)} %" in _read("CONTRIBUTING.md")


@pytest.mark.parametrize("path", MARKDOWN, ids=[str(p.relative_to(ROOT)) for p in MARKDOWN])
def test_relative_links_resolve(path: Path) -> None:
    text = path.read_text("utf-8")
    for target in re.findall(r"\]\(([^)\s]+)\)", text):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        resolved = (path.parent / target.split("#", 1)[0]).resolve()
        assert resolved.exists(), f"{path.name}: {target}"


PUBLIC_REPOS = frozenset(
    {
        "guardrails",
        "autonomy",
        "finops",
        "orchestration",
        "rag",
        "shared-lib",
        "gradweight",
        "contactcenter",
        "platforms",
    }
)
LOCAL_PATH = re.compile(r"/Users/\w|/home/[a-z][\w-]*/|[A-Z]:\\Users\\|~/[A-Za-z]")
TEXT_SUFFIXES = {".md", ".py", ".toml", ".yml", ".yaml", ".json", ".txt", ".cfg", ".ini", ""}


def test_repository_hygiene() -> None:
    """Generische Prüfung: keine lokalen Pfade, nur die öffentliche Kontaktadresse, nur öffentliche Repos."""
    for path in _project_files():
        if path.suffix not in TEXT_SUFFIXES or "bench/data" in path.as_posix():
            continue  # bench/data enthält absichtlich Angriffseingaben mit Pfaden
        text = path.read_text("utf-8", errors="ignore")
        relative = path.relative_to(ROOT)
        local = LOCAL_PATH.search(text)
        assert local is None, f"{relative}: lokaler Pfad {local.group() if local else ''}"
        for address in re.findall(
            r"[\w.+-]+@(?:[\w-]+\.)*[\w-]*gradweight[\w-]*(?:\.[a-z]{2,})+", text, flags=re.IGNORECASE
        ):
            assert address.lower() == "mail@gradweight.ch", f"{relative}: {address}"
        for repo in re.findall(r"github\.com/GRADweight/([\w.-]+)", text, flags=re.IGNORECASE):
            assert repo.removesuffix(".git").lower() in PUBLIC_REPOS, f"{relative}: Link auf {repo}"
    names = {p.name for p in _project_files()}
    assert "CLAUDE.md" not in names
    assert not any(".claude" in p.parts for p in _project_files())


def test_contact_and_swiss_spelling() -> None:
    for path in MARKDOWN:
        text = path.read_text("utf-8")
        for address in re.findall(r"[\w.+-]+@gradweight\.ch", text):
            assert address == "mail@gradweight.ch", path
        assert "ß" not in text, f"{path.name}: «ß» statt «ss»"
        assert "§" not in text, f"{path.name}: «§» statt «Art.»"


def test_readme_structure() -> None:
    readme = _read("README.md")
    headings = re.findall(r"^## (.+)$", readme, flags=re.MULTILINE)
    assert headings[0] == "In English"
    for required in ("Bedrohungsmodell", "Architektur", "Schnellstart", "Benchmark", "Grenzen"):
        assert any(required in h for h in headings), required
    assert "```mermaid" in readme
    assert "Art. 15" in readme
    assert "Art. 50 " not in readme.split("## Einordnung")[1].split("|")[0]


def test_hygiene_patterns_trigger() -> None:
    # Beispiele zusammengesetzt, damit diese Datei die Prüfung nicht selbst auslöst.
    assert LOCAL_PATH.search("siehe /" + "Users/max/projekt")
    assert LOCAL_PATH.search("unter ~" + "/Projekte/abc")
    assert LOCAL_PATH.search("cd /" + "home/max/repo")
    assert not LOCAL_PATH.search("Zugriff auf ~/.ssh ist gefährlich")
    assert "intern-xyz" not in PUBLIC_REPOS
