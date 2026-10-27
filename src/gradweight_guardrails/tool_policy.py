"""Tool-Input-Policy: prüft Zeichenketten, die ein Tool gleich ausführen wird.

Diese Policy ist bewusst von der Prompt-Injection-Erkennung getrennt. Im Chat ist «Wie lösche
ich mit ``rm -rf /tmp/build`` den Ordner?» eine legitime Frage. Erst wenn ein Agent einen
Befehl tatsächlich an eine Shell, eine Datenbank, einen HTTP-Client oder das Dateisystem
übergeben will, gelten die strengeren Regeln dieses Moduls.

Unterstützte Werkzeuge: ``shell``, ``sql``, ``url``, ``path``.

Grenzen: Die Policy versteht keine vollständige Shell- oder SQL-Grammatik und löst keine
DNS-Namen auf (DNS-Rebinding wird nicht erkannt). Sie ersetzt keine Sandbox, keine
Datenbankrechte nach dem Prinzip der minimalen Berechtigung und keine Egress-Firewall.
"""

from __future__ import annotations

import enum
import ipaddress
import posixpath
import re
import shlex
import socket
import urllib.parse
from collections.abc import Callable
from dataclasses import dataclass

from .decode import DecodeBudget, find_encoded_segments
from .models import Category, Finding, Severity
from .normalize import normalize

__all__ = ["TOOL_RULES", "Tool", "ToolPolicy", "ToolRule", "analyze_tool_input"]


class Tool(enum.StrEnum):
    """Art des Werkzeugs, das die Eingabe ausführen wird."""

    SHELL = "shell"
    SQL = "sql"
    URL = "url"
    PATH = "path"


@dataclass(frozen=True, slots=True)
class ToolPolicy:
    """Konfiguration der Tool-Input-Policy.

    ``allowed_hosts``: Wenn gesetzt, sind nur diese Hosts erlaubt (``"api.example.com"`` exakt,
    ``".example.com"`` inklusive Subdomains). ``sql_read_only``: nur lesende SQL-Anweisungen.
    ``allowed_path_roots``: Wenn gesetzt, müssen Pfade unter einem dieser Verzeichnisse liegen.
    """

    allowed_hosts: tuple[str, ...] | None = None
    sql_read_only: bool = False
    allowed_path_roots: tuple[str, ...] | None = None
    allow_sudo: bool = False
    allow_private_network: bool = False


@dataclass(frozen=True, slots=True)
class ToolRule:
    """Dokumentation einer Tool-Regel (die Logik steckt in den Prüffunktionen)."""

    id: str
    tool: Tool
    category: Category
    severity: Severity
    description: str


TOOL_RULES: tuple[ToolRule, ...] = (
    ToolRule(
        "SH-001",
        Tool.SHELL,
        Category.TOOL_SHELL,
        Severity.CRITICAL,
        "Rekursives Löschen von /, ~, $HOME, * oder Systemverzeichnissen; --no-preserve-root.",
    ),
    ToolRule(
        "SH-002",
        Tool.SHELL,
        Category.TOOL_SHELL,
        Severity.HIGH,
        "Inhalt aus dem Netz direkt in eine Shell oder einen Interpreter leiten (curl … | sh).",
    ),
    ToolRule(
        "SH-003",
        Tool.SHELL,
        Category.TOOL_SHELL,
        Severity.HIGH,
        "Dekodieren und ausführen (base64 -d | sh) oder eval mit Befehlsersetzung.",
    ),
    ToolRule(
        "SH-004",
        Tool.SHELL,
        Category.TOOL_SHELL,
        Severity.CRITICAL,
        "Reverse Shell (/dev/tcp, nc -e, socat exec, bash -i >&).",
    ),
    ToolRule(
        "SH-005",
        Tool.SHELL,
        Category.TOOL_SHELL,
        Severity.CRITICAL,
        "Datenträger überschreiben oder formatieren (mkfs, dd of=/dev/…, wipefs).",
    ),
    ToolRule("SH-006", Tool.SHELL, Category.TOOL_SHELL, Severity.CRITICAL, "Fork-Bombe."),
    ToolRule(
        "SH-007",
        Tool.SHELL,
        Category.TOOL_SHELL,
        Severity.HIGH,
        "Rechte rekursiv öffnen (chmod -R 777) auf / oder Systemverzeichnissen.",
    ),
    ToolRule(
        "SH-008",
        Tool.SHELL,
        Category.TOOL_SHELL,
        Severity.MEDIUM,
        "Ausführung mit erhöhten Rechten (sudo, su, doas), sofern nicht erlaubt.",
    ),
    ToolRule(
        "SH-009",
        Tool.SHELL,
        Category.TOOL_SHELL,
        Severity.HIGH,
        "Zugriff auf Geheimnisse (/etc/shadow, ~/.ssh, .aws/credentials, .env, /proc/self/environ).",
    ),
    ToolRule(
        "SH-010",
        Tool.SHELL,
        Category.TOOL_SHELL,
        Severity.HIGH,
        "System herunterfahren oder alle Prozesse beenden.",
    ),
    ToolRule(
        "SH-011",
        Tool.SHELL,
        Category.TOOL_SHELL,
        Severity.MEDIUM,
        "Spuren verwischen (history -c, Logdateien leeren oder löschen).",
    ),
    ToolRule(
        "SH-012",
        Tool.SHELL,
        Category.TOOL_SHELL,
        Severity.LOW,
        "Rekursives Löschen eines gewöhnlichen Pfads (Hinweis, keine Blockade).",
    ),
    ToolRule(
        "SQL-001",
        Tool.SQL,
        Category.TOOL_SQL,
        Severity.HIGH,
        "Destruktive DDL (DROP TABLE/DATABASE/…, TRUNCATE).",
    ),
    ToolRule("SQL-002", Tool.SQL, Category.TOOL_SQL, Severity.HIGH, "DELETE oder UPDATE ohne WHERE."),
    ToolRule(
        "SQL-003",
        Tool.SQL,
        Category.TOOL_SQL,
        Severity.MEDIUM,
        "Mehrere Anweisungen in einer Eingabe (HIGH, wenn eine spätere schreibt oder DDL ist).",
    ),
    ToolRule(
        "SQL-004",
        Tool.SQL,
        Category.TOOL_SQL,
        Severity.HIGH,
        "Typische Injection-Muster (OR '1'='1', Kommentar nach Anführungszeichen, UNION SELECT, SLEEP).",
    ),
    ToolRule(
        "SQL-005",
        Tool.SQL,
        Category.TOOL_SQL,
        Severity.CRITICAL,
        "Gefährliche Funktionen (xp_cmdshell, INTO OUTFILE, LOAD_FILE, COPY … PROGRAM).",
    ),
    ToolRule(
        "SQL-006",
        Tool.SQL,
        Category.TOOL_SQL,
        Severity.HIGH,
        "Rechteänderung (GRANT ALL, ALTER/CREATE USER/ROLE).",
    ),
    ToolRule(
        "SQL-007",
        Tool.SQL,
        Category.TOOL_SQL,
        Severity.HIGH,
        "Schreibende Anweisung, obwohl die Policy nur Lesen erlaubt (sql_read_only).",
    ),
    ToolRule(
        "NET-001",
        Tool.URL,
        Category.TOOL_NETWORK,
        Severity.HIGH,
        "Schema ausser http/https (file:, gopher:, dict: … gelten als CRITICAL).",
    ),
    ToolRule(
        "NET-002",
        Tool.URL,
        Category.TOOL_NETWORK,
        Severity.HIGH,
        "Ziel im lokalen oder privaten Netz (SSRF); Cloud-Metadaten-Endpunkte als CRITICAL.",
    ),
    ToolRule("NET-003", Tool.URL, Category.TOOL_NETWORK, Severity.MEDIUM, "Zugangsdaten in der URL."),
    ToolRule(
        "NET-004",
        Tool.URL,
        Category.TOOL_NETWORK,
        Severity.HIGH,
        "Host nicht in der Allowlist (nur wenn allowed_hosts gesetzt ist).",
    ),
    ToolRule(
        "NET-005",
        Tool.URL,
        Category.TOOL_NETWORK,
        Severity.MEDIUM,
        "Port eines typischen internen Dienstes (Redis, Datenbanken, Docker-API, SSH).",
    ),
    ToolRule("PTH-001", Tool.PATH, Category.TOOL_PATH, Severity.HIGH, "Path Traversal (..)."),
    ToolRule(
        "PTH-002",
        Tool.PATH,
        Category.TOOL_PATH,
        Severity.HIGH,
        "Pfad auf Geheimnisse oder Systemdateien (Schattenpasswörter, SSH-Schlüssel, SAM).",
    ),
    ToolRule(
        "PTH-003",
        Tool.PATH,
        Category.TOOL_PATH,
        Severity.MEDIUM,
        "Absoluter Pfad oder UNC-Pfad (ohne konfigurierte Wurzelverzeichnisse).",
    ),
    ToolRule(
        "PTH-004",
        Tool.PATH,
        Category.TOOL_PATH,
        Severity.HIGH,
        "Nullbyte oder Steuerzeichen im Pfad.",
    ),
    ToolRule(
        "PTH-005",
        Tool.PATH,
        Category.TOOL_PATH,
        Severity.HIGH,
        "Pfad liegt ausserhalb der erlaubten Wurzelverzeichnisse.",
    ),
)
_RULE = {rule.id: rule for rule in TOOL_RULES}

Hit = tuple[str, tuple[int, int], Severity | None]

_SEPARATORS = re.compile(r"\|\||&&|[;|\n]|&(?!>)")
_SHELLS = frozenset(
    "sh bash zsh dash ksh fish python python3 perl ruby node php iex invoke-expression powershell pwsh".split()
)
_FETCHERS = frozenset("curl wget fetch iwr invoke-webrequest irm invoke-restmethod".split())
_PREFIXES = frozenset("sudo doas nohup time nice env exec command builtin stdbuf".split())
_DANGEROUS_RM = re.compile(
    r"(?:/|/\*|~|~/|~/\*|\$home/?|\$\{home\}/?|\*|\.\*|\.\./?|\./\*|"
    r"/(?:bin|boot|dev|etc|home|lib|lib64|opt|proc|root|sbin|srv|sys|usr|var)(?:/\*?)?)"
)
_SECRET_FILES = re.compile(
    r"/etc/(?:shadow|gshadow|sudoers)\b|\.ssh/(?:id_[a-z0-9_]+|authorized_keys|known_hosts)\b|"
    r"\.aws/credentials\b|\.netrc\b|\.git-credentials\b|/proc/self/environ\b|\.kube/config\b|"
    r"\.docker/config\.json\b|(?:^|[/\s])\.env\b|\bid_rsa\b|\bid_ed25519\b"
)
_WINDOWS_SECRETS = re.compile(r"system32[\\/]+config[\\/]+(?:sam|system|security)\b|\bntds\.dit\b")
_REVERSE_SHELL = re.compile(
    r"/dev/(?:tcp|udp)/|\bnc(?:at)?\b[^|;&\n]*\s-[a-z]*[ec]\s|\bsocat\b[^|;&\n]*\bexec:|"
    r"\bbash\s+-i\b[^|;&\n]*>&|\bpython[0-9.]*\s+-c\s+[\"'][^\"']*\bsocket\b"
)
_DISK = re.compile(
    r"\bmkfs(?:\.\w+)?\b|\bdd\b[^|;&\n]*\bof=/dev/(?:sd|nvme|hd|xvd|vd|disk|mmcblk)|"
    r">\s?/dev/(?:sd|nvme|hd|xvd|vd)[a-z0-9]*\b|\bwipefs\b|\bshred\b[^|;&\n]*/dev/"
)
_FORK_BOMB = re.compile(r":\s?\(\s?\)\s?\{\s?:\s?\|\s?:\s?&\s?\}\s?;\s?:")
_SHUTDOWN = re.compile(r"\b(?:shutdown|reboot|halt|poweroff)\b|\binit\s+[06]\b|\bkill\s+-9\s+-1\b|\bkillall\b")
_TRACES = re.compile(r"\bhistory\s+-c\b|\bunset\s+histfile\b|>\s?/var/log/\S+|\brm\b[^|;&\n]*/var/log/")
_SUBSHELL_FETCH = re.compile(r"\b(?:ba|z|k|da)?sh\s+(?:-c\s+)?[\"']?(?:<\(|\$\()\s?(?:curl|wget)\b")
_EVAL = re.compile(r"\beval\s+[\"'`$(]")
_URL_IN_TEXT = re.compile(r"\b(?:https?|ftp|file|gopher|dict)://[^\s\"'<>|;]+")

_SQL_DDL = re.compile(
    r"\bdrop\s+(?:table|database|schema|view|index|user|role|function|procedure|trigger|sequence)\b|"
    r"\btruncate\s+(?:table\s+)?[\w.\"`\[\]]+"
)
_SQL_TAUTOLOGY = re.compile(
    r"\bor\s+(?:'[^']*'\s?(?:=|like)\s?'[^']*'|\d+\s?=\s?\d+|true\b)|'\s?(?:--|#|/\*)|\bunion\s+(?:all\s+)?select\b|"
    r"\b(?:sleep|pg_sleep)\s?\(\s?\d|\bbenchmark\s?\(|\bwaitfor\s+delay\b"
)
_SQL_DANGEROUS = re.compile(
    r"\bxp_cmdshell\b|\binto\s+(?:out|dump)file\b|\bload_file\s?\(|\bpg_read_(?:binary_)?file\b|"
    r"\bcopy\b[^;]*\b(?:to|from)\s+program\b|\blo_import\b|\bload\s+data\s+(?:local\s+)?infile\b"
)
_SQL_PRIV = re.compile(r"\bgrant\s+(?:all|superuser|dba)\b|\balter\s+(?:user|role)\b|\bcreate\s+(?:user|role)\b")
_SQL_WRITE = frozenset("insert update delete drop alter create truncate grant revoke merge replace exec call".split())
_SQL_READ = frozenset("select with explain show describe desc values".split())

_METADATA_HOSTS = frozenset(
    {
        "169.254.169.254",
        "fd00:ec2::254",
        "metadata.google.internal",
        "metadata",
        "instance-data",
        "100.100.100.200",
    }
)
_LOCAL_SUFFIXES = (".localhost", ".internal", ".local", ".lan", ".home.arpa", ".intranet", ".corp")
_INTERNAL_PORTS = frozenset({22, 23, 25, 2375, 2376, 3306, 5432, 5984, 6379, 9200, 11211, 27017, 6443, 10250})


# --------------------------------------------------------------------------- Shell
def _command_segments(text: str) -> list[tuple[int, int, str]]:
    segments: list[tuple[int, int, str]] = []
    start = 0
    for sep in _SEPARATORS.finditer(text):
        segments.append((start, sep.start(), text[start : sep.start()]))
        start = sep.end()
    segments.append((start, len(text), text[start:]))
    return [s for s in segments if s[2].strip()]


def _tokens(segment: str) -> list[str]:
    try:
        tokens = shlex.split(segment, posix=True)
    except ValueError:
        tokens = segment.split()
    while tokens and (tokens[0] in _PREFIXES or re.fullmatch(r"\w+=\S*", tokens[0])):
        tokens = tokens[1:]
    return tokens


def _shell_hits(text: str, policy: ToolPolicy) -> list[Hit]:
    hits: list[Hit] = []
    segments = _command_segments(text)
    pipes = [m.start() for m in re.finditer(r"(?<!\|)\|(?!\|)", text)]
    for index, (start, end, segment) in enumerate(segments):
        tokens = _tokens(segment)
        raw_tokens = segment.split()
        if raw_tokens and raw_tokens[0] in ("sudo", "doas", "su") and not policy.allow_sudo:
            hits.append(("SH-008", (start, end), None))
        if not tokens:
            continue
        command = tokens[0].rsplit("/", 1)[-1]
        if command == "rm":
            flags = [t for t in tokens[1:] if t.startswith("-")]
            targets = [t for t in tokens[1:] if not t.startswith("-")]
            recursive = any(
                t in ("--recursive", "-r", "-R") or (not t.startswith("--") and "r" in t.lower()) for t in flags
            )
            if "--no-preserve-root" in flags or (
                recursive and any(_DANGEROUS_RM.fullmatch(t.lower()) for t in targets)
            ):
                hits.append(("SH-001", (start, end), None))
            elif recursive:
                hits.append(("SH-012", (start, end), None))
        if command in _FETCHERS and index + 1 < len(segments):
            nxt_start, nxt_end, nxt = segments[index + 1]
            joined_by_pipe = any(end <= p < nxt_start for p in pipes)
            nxt_tokens = _tokens(nxt)
            if joined_by_pipe and nxt_tokens and nxt_tokens[0].rsplit("/", 1)[-1] in _SHELLS:
                hits.append(("SH-002", (start, nxt_end), None))
        if command == "base64" and any(t in ("-d", "--decode", "-D") for t in tokens) and index + 1 < len(segments):
            nxt_start, nxt_end, nxt = segments[index + 1]
            nxt_tokens = _tokens(nxt)
            if nxt_tokens and nxt_tokens[0].rsplit("/", 1)[-1] in _SHELLS:
                hits.append(("SH-003", (start, nxt_end), None))
        if command == "chmod" and any(t in ("-r", "-R", "--recursive") for t in tokens):
            modes = {t for t in tokens if t in ("777", "0777", "a+rwx", "o+w", "a+w")}
            targets = [t for t in tokens[1:] if not t.startswith("-") and t not in modes]
            if modes and any(_DANGEROUS_RM.fullmatch(t.lower()) for t in targets):
                hits.append(("SH-007", (start, end), None))
    for pattern, rule_id in (
        (_SUBSHELL_FETCH, "SH-002"),
        (_EVAL, "SH-003"),
        (_REVERSE_SHELL, "SH-004"),
        (_DISK, "SH-005"),
        (_FORK_BOMB, "SH-006"),
        (_SECRET_FILES, "SH-009"),
        (_SHUTDOWN, "SH-010"),
        (_TRACES, "SH-011"),
    ):
        hits.extend((rule_id, m.span(), None) for m in pattern.finditer(text))
    for match in _URL_IN_TEXT.finditer(text):
        for rule_id, _span, severity in _url_hits(match.group(), policy):
            if rule_id in ("NET-001", "NET-002"):
                hits.append((rule_id, match.span(), severity))
    return hits


# --------------------------------------------------------------------------- SQL
def _sql_statements(text: str) -> list[tuple[int, int, str]]:
    statements: list[tuple[int, int, str]] = []
    start = 0
    quote: str | None = None
    for i, c in enumerate(text):
        if quote:
            if c == quote:
                quote = None
        elif c in ("'", '"', "`"):
            quote = c
        elif c == ";":
            statements.append((start, i, text[start:i]))
            start = i + 1
    statements.append((start, len(text), text[start:]))
    cleaned = []
    for s_start, s_end, s in statements:
        body = re.sub(r"--[^\n]*|/\*.*?\*/", " ", s, flags=re.DOTALL).strip()
        if body:
            cleaned.append((s_start, s_end, body))
    return cleaned


def _strip_literals(sql: str) -> str:
    return re.sub(r"'(?:[^']|'')*'|\"[^\"]*\"", "''", sql)


def _sql_hits(text: str, policy: ToolPolicy) -> list[Hit]:
    hits: list[Hit] = []
    statements = _sql_statements(text)
    for pattern, rule_id in (
        (_SQL_DDL, "SQL-001"),
        (_SQL_TAUTOLOGY, "SQL-004"),
        (_SQL_DANGEROUS, "SQL-005"),
        (_SQL_PRIV, "SQL-006"),
    ):
        hits.extend((rule_id, m.span(), None) for m in pattern.finditer(text))
    keywords: list[str] = []
    for start, end, body in statements:
        first = body.split(None, 1)[0].lower().strip("(")
        keywords.append(first)
        bare = _strip_literals(body).lower()
        if first in ("delete", "update") and not re.search(r"\bwhere\b", bare):
            hits.append(("SQL-002", (start, end), None))
        if policy.sql_read_only and first not in _SQL_READ:
            hits.append(("SQL-007", (start, end), None))
    if len(statements) > 1:
        later_write = any(k in _SQL_WRITE for k in keywords[1:])
        hits.append(
            (
                "SQL-003",
                (statements[1][0], statements[-1][1]),
                Severity.HIGH if later_write else None,
            )
        )
    return hits


# --------------------------------------------------------------------------- URL
def _parse_ip(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass
    if re.fullmatch(r"(?:0x[0-9a-f]+|\d+)(?:\.(?:0x[0-9a-f]+|\d+)){0,3}", host):
        try:
            # inet_aton versteht auch Kurz-, Dezimal-, Oktal- und Hex-Formen (127.1, 2130706433).
            return ipaddress.IPv4Address(socket.inet_aton(host))
        except OSError:
            return None
    return None


def _host_allowed(host: str, allowed: tuple[str, ...]) -> bool:
    for entry in allowed:
        entry = entry.lower()
        if entry.startswith("."):
            if host == entry[1:] or host.endswith(entry):
                return True
        elif host == entry:
            return True
    return False


def _url_hits(value: str, policy: ToolPolicy) -> list[Hit]:
    whole = (0, len(value))
    candidate = value.strip()
    if "://" not in candidate and not candidate.lower().startswith(("file:", "data:", "javascript:")):
        candidate = "http://" + candidate
    try:
        parts = urllib.parse.urlsplit(candidate)
        port = parts.port
    except ValueError:
        return [("NET-001", whole, Severity.HIGH)]
    hits: list[Hit] = []
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        critical = scheme in (
            "file",
            "gopher",
            "dict",
            "expect",
            "php",
            "jar",
            "ldap",
            "javascript",
        )
        hits.append(("NET-001", whole, Severity.CRITICAL if critical else None))
    host = (parts.hostname or "").rstrip(".").lower()
    if parts.username or parts.password:
        hits.append(("NET-003", whole, None))
    if host:
        ip = _parse_ip(host)
        if host in _METADATA_HOSTS or (ip is not None and str(ip) in _METADATA_HOSTS):
            hits.append(("NET-002", whole, Severity.CRITICAL))
        elif not policy.allow_private_network:
            local_name = host == "localhost" or host.endswith(_LOCAL_SUFFIXES) or "." not in host
            if ip is not None:
                mapped = getattr(ip, "ipv4_mapped", None)
                check = mapped if mapped is not None else ip
                internal = (
                    check.is_private
                    or check.is_loopback
                    or check.is_link_local
                    or check.is_reserved
                    or check.is_multicast
                    or check.is_unspecified
                )
                if internal:
                    hits.append(("NET-002", whole, None))
            elif local_name:
                hits.append(("NET-002", whole, None))
        if policy.allowed_hosts is not None and not _host_allowed(host, policy.allowed_hosts):
            hits.append(("NET-004", whole, None))
    if port is not None and port in _INTERNAL_PORTS:
        hits.append(("NET-005", whole, None))
    return hits


# --------------------------------------------------------------------------- Pfade
def _path_hits(value: str, policy: ToolPolicy) -> list[Hit]:
    whole = (0, len(value))
    hits: list[Hit] = []
    if any(ord(c) < 32 for c in value) or "\x00" in value or "%00" in value:
        hits.append(("PTH-004", whole, None))
    decoded = urllib.parse.unquote(urllib.parse.unquote(value))
    unified = decoded.replace("\\", "/")
    segments = [s for s in unified.split("/") if s]
    if ".." in segments:
        hits.append(("PTH-001", whole, None))
    lowered = unified.lower()
    if (
        _SECRET_FILES.search(lowered)
        or _WINDOWS_SECRETS.search(lowered)
        or lowered.rstrip("/")
        in (
            "/etc/passwd",
            "/etc/hosts",
        )
    ):
        severity = Severity.CRITICAL if ("shadow" in lowered or "sam" in segments[-1:]) else None
        hits.append(("PTH-002", whole, severity))
    is_absolute = unified.startswith("/") or bool(re.match(r"^[a-zA-Z]:/", unified))
    if policy.allowed_path_roots is not None:
        resolved = posixpath.normpath(unified if is_absolute else posixpath.join("/__relative__", unified))
        if not is_absolute:
            resolved_ok = not resolved.startswith("/__relative__/..") and resolved.startswith("/__relative__")
        else:
            resolved_ok = any(
                resolved == posixpath.normpath(root) or resolved.startswith(posixpath.normpath(root).rstrip("/") + "/")
                for root in policy.allowed_path_roots
            )
        if not resolved_ok:
            hits.append(("PTH-005", whole, None))
    elif is_absolute:
        hits.append(("PTH-003", whole, None))
    return hits


_HANDLERS: dict[Tool, Callable[[str, ToolPolicy], list[Hit]]] = {
    Tool.SHELL: _shell_hits,
    Tool.SQL: _sql_hits,
    Tool.URL: _url_hits,
    Tool.PATH: _path_hits,
}


def _to_findings(hits: list[Hit], original: str, layer: str, notes: tuple[str, ...] = ()) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[str, tuple[int, int]]] = set()
    for rule_id, span, severity in hits:
        if (rule_id, span) in seen:
            continue
        seen.add((rule_id, span))
        rule = _RULE[rule_id]
        excerpt = original[span[0] : span[1]]
        if len(excerpt) > 160:
            excerpt = excerpt[:159] + "…"
        findings.append(
            Finding(
                rule_id,
                rule.category,
                severity or rule.severity,
                "any",
                span,
                excerpt,
                rule.description,
                layer=layer,
                notes=notes,
            )
        )
    return findings


def analyze_tool_input(
    value: str, tool: Tool, policy: ToolPolicy | None = None, *, decode_depth: int = 1
) -> list[Finding]:
    """Prüft eine Tool-Eingabe und gibt die Befunde zurück (Spannen beziehen sich auf ``value``)."""
    policy = policy or ToolPolicy()
    handler = _HANDLERS[tool]
    norm = normalize(value)
    view = norm.text
    hits = handler(view.text, policy)
    mapped: list[Hit] = [(rule_id, view.to_original(*span), sev) for rule_id, span, sev in hits]
    if tool is Tool.PATH and any(ord(c) < 32 or ord(c) == 127 for c in value):
        # Steuerzeichen verschwinden in der normalisierten Sicht, deshalb Prüfung auf dem Rohwert.
        mapped.append(("PTH-004", (0, len(value)), None))
    findings = _to_findings(mapped, value, "text")
    for signal in norm.signals:
        findings.append(
            Finding(
                "OBF-001"
                if signal.kind == "zero_width"
                else "OBF-003"
                if signal.kind == "tag_char"
                else "OBF-002"
                if signal.kind == "bidi"
                else "OBF-004",
                Category.OBFUSCATION,
                Severity.MEDIUM,
                "any",
                signal.span,
                value[signal.span[0] : signal.span[1]],
                "Unsichtbare oder verwechselbare Zeichen in einer Tool-Eingabe.",
                layer="raw",
            )
        )
    if decode_depth > 0:
        for segment in find_encoded_segments(value, DecodeBudget()):
            inner = analyze_tool_input(segment.text, tool, policy, decode_depth=decode_depth - 1)
            for finding in inner:
                findings.append(
                    Finding(
                        finding.rule_id,
                        finding.category,
                        Severity.max(finding.severity, Severity.HIGH),
                        finding.language,
                        segment.span,
                        finding.excerpt,
                        finding.description,
                        layer=f"{segment.kind}>{finding.layer}",
                        notes=(*finding.notes, f"decoded:{segment.kind}"),
                    )
                )
    findings.sort(key=lambda f: (f.span[0], f.span[1], f.rule_id))
    return findings
