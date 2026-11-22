"""Tool-Input-Policy. Angriffseingaben stammen aus dem Dev-Datensatz (bench/data/dev.jsonl)."""

from __future__ import annotations

from pathlib import Path

import pytest

from gradweight_guardrails import Decision, Guard, GuardConfig, ToolPolicy, scan, scan_tool_input
from gradweight_guardrails.evaluation import Case, load_cases
from gradweight_guardrails.tool_policy import TOOL_RULES, Tool, analyze_tool_input

DEV = Path(__file__).resolve().parent.parent / "bench" / "data" / "dev.jsonl"
TOOL_CASES = [c for c in load_cases(DEV) if c.context == "tool"]


def _ids(value: str, tool: str, policy: ToolPolicy | None = None) -> set[str]:
    return {f.rule_id for f in analyze_tool_input(value, Tool(tool), policy)}


@pytest.mark.parametrize("case", TOOL_CASES, ids=[c.id for c in TOOL_CASES])
def test_dev_tool_cases(case: Case) -> None:
    result = scan_tool_input(case.text, case.tool or "shell")
    if case.is_attack:
        assert result.decision is Decision.BLOCK, result.findings
    else:
        assert result.decision is Decision.ALLOW, result.findings


def test_chat_context_does_not_apply_tool_policy() -> None:
    """Dieselbe Zeichenkette ist als Frage harmlos und erst als Tool-Eingabe relevant."""
    for case in TOOL_CASES:
        if case.is_attack:
            assert scan(f"Was macht der Befehl `{case.text}` genau?").decision is not Decision.BLOCK


def test_sql_read_only_policy() -> None:
    statement = "INSERT INTO notes (text) VALUES ('Rückruf vereinbart')"
    assert scan_tool_input(statement, "sql").decision is Decision.ALLOW
    strict = scan_tool_input(statement, "sql", policy=ToolPolicy(sql_read_only=True))
    assert "SQL-007" in strict.rule_ids
    assert strict.decision is Decision.BLOCK
    assert scan_tool_input("SELECT id FROM notes", "sql", policy=ToolPolicy(sql_read_only=True)).allowed


def test_sql_multiple_statements_without_write_are_review() -> None:
    result = scan_tool_input("SELECT 1; SELECT 2", "sql")
    assert result.decision is Decision.REVIEW
    assert result.rule_ids == ("SQL-003",)


def test_sql_where_inside_literal_does_not_count() -> None:
    assert "SQL-002" in _ids("UPDATE notes SET text = 'where'", "sql")
    assert "SQL-002" not in _ids("UPDATE notes SET text = 'x' WHERE id = 3", "sql")


def test_url_allowlist() -> None:
    policy = ToolPolicy(allowed_hosts=("api.example.com", ".admin.ch"))
    assert _ids("https://api.example.com/v1", "url", policy) == set()
    assert _ids("https://www.admin.ch/gov", "url", policy) == set()
    assert _ids("https://admin.ch", "url", policy) == set()
    assert "NET-004" in _ids("https://other.example.org/", "url", policy)


@pytest.mark.parametrize(
    "value",
    [
        "http://localhost:8000/",
        "http://127.1/",
        "http://2130706433/",
        "http://10.0.0.5/",
        "http://[::1]/",
        "http://[::ffff:127.0.0.1]/",
        "http://printer.local/",
        "http://intranet/",
    ],
)
def test_url_private_targets(value: str) -> None:
    assert "NET-002" in _ids(value, "url")
    assert "NET-002" not in _ids(value, "url", ToolPolicy(allow_private_network=True))


def test_url_metadata_endpoint_is_critical_even_if_private_allowed() -> None:
    result = Guard(GuardConfig(tool_policy=ToolPolicy(allow_private_network=True))).scan_tool_input(
        "http://169.254.169.254/latest/", "url"
    )
    assert result.decision is Decision.BLOCK


def test_url_scheme_credentials_and_ports() -> None:
    assert "NET-001" in _ids("ftp://files.example.com/a", "url")
    assert "NET-003" in _ids("https://user:pw@api.example.com/", "url")
    assert "NET-005" in _ids("https://db.example.com:5432/", "url")
    assert _ids("https://api.example.com/health", "url") == set()
    assert _ids("api.example.com/health", "url") == set()
    assert "NET-001" in _ids("http://[::1", "url")


def test_path_rules() -> None:
    assert _ids("reports/2026/q3.csv", "path") == set()
    assert "PTH-003" in _ids("/var/data/report.csv", "path")
    assert "PTH-001" in _ids("reports/%2e%2e/%2e%2e/x", "path")
    assert "PTH-004" in _ids("report\x00.csv", "path")


def test_path_allowed_roots() -> None:
    policy = ToolPolicy(allowed_path_roots=("/srv/data",))
    assert _ids("/srv/data/2026/a.csv", "path", policy) == set()
    assert "PTH-005" in _ids("/srv/other/a.csv", "path", policy)
    assert "PTH-005" in _ids("../a.csv", "path", policy)
    assert _ids("2026/a.csv", "path", policy) == set()


def test_shell_harmless_commands_allowed() -> None:
    for command in ("git status && git diff --stat", "python -m pytest -q", "ls -la reports"):
        assert scan_tool_input(command, "shell").allowed


def test_shell_recursive_delete_of_project_path_is_only_a_hint() -> None:
    result = scan_tool_input("rm -rf ./dist", "shell")
    assert result.allowed
    assert result.rule_ids == ("SH-012",)


def test_sudo_policy() -> None:
    assert "SH-008" in _ids("sudo apt-get update", "shell")
    assert "SH-008" not in _ids("sudo apt-get update", "shell", ToolPolicy(allow_sudo=True))


def test_invisible_characters_in_tool_input_are_flagged() -> None:
    assert "OBF-001" in _ids("l​s -la", "shell")


def test_unknown_tool_raises() -> None:
    with pytest.raises(ValueError, match="nope"):
        scan_tool_input("ls", "nope")


def test_tool_rule_ids_unique() -> None:
    ids = [r.id for r in TOOL_RULES]
    assert len(ids) == len(set(ids))
