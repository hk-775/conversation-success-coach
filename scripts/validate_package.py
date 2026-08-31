"""Repository-level publication checks using only the Python standard library."""

from __future__ import annotations

import re
import shutil
import struct
import subprocess  # nosec B404
import sys
from pathlib import Path

from defusedxml import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "conversation_success_coach" / "web"
SITE = ROOT / "site"

REQUIRED_ARTIFACTS = (
    ".dockerignore",
    ".env.example",
    ".github/CODEOWNERS",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows/ci.yml",
    ".github/workflows/pages.yml",
    "CHANGELOG.md",
    "CITATION.cff",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "Dockerfile",
    "GOVERNANCE.md",
    "LICENSE",
    "NOTICE",
    "QUICKSTART.md",
    "README.md",
    "SECURITY.md",
    "STARTUP.md",
    "SUPPORT.md",
    "docker-compose.yml",
    "docs/API.md",
    "docs/ARCHITECTURE.md",
    "docs/DEMO.md",
    "docs/DEPLOYMENT.md",
    "docs/ETHICS.md",
    "docs/PRODUCTION_READINESS.md",
    "docs/PUBLICATION_ARTIFACTS.md",
    "docs/THREAT_MODEL.md",
    "launch-materials.md",
    "pyproject.toml",
    "scripts/test_public_site.mjs",
    "site/.nojekyll",
    "site/architecture.html",
    "site/assets/aws-reference-architecture.drawio",
    "site/assets/aws-reference-architecture.png",
    "site/assets/system-architecture.drawio",
    "site/assets/system-architecture.png",
    "site/dashboard.html",
    "site/index.html",
    "uv.lock",
)

IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
}

FORBIDDEN_TEXT = (
    "github.com/" + "example",
    "example" + ".com/",
    "example" + ".org/",
    "local" + "host:8080",
    "127.0.0.1:" + "8080",
    "Match" + "Mind",
    "dating" + "-specific",
)

TEXT_EXTENSIONS = {
    ".css",
    ".drawio",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".yaml",
    ".yml",
}


def fail(message: str) -> None:
    print(f"validation error: {message}", file=sys.stderr)
    raise SystemExit(1)


def relative_files(directory: Path) -> dict[Path, Path]:
    return {
        path.relative_to(directory): path
        for path in directory.rglob("*")
        if path.is_file() and not any(part in IGNORED_PARTS for part in path.parts)
    }


def validate_required_artifacts() -> None:
    for relative in REQUIRED_ARTIFACTS:
        if not (ROOT / relative).is_file():
            fail(f"missing publication artifact: {relative}")


def validate_mirror() -> None:
    served = relative_files(WEB)
    static = relative_files(SITE)
    if served.keys() != static.keys():
        missing = sorted(str(path) for path in served.keys() - static.keys())
        extra = sorted(str(path) for path in static.keys() - served.keys())
        fail(f"static mirror file set differs; missing={missing}, extra={extra}")
    for relative, served_path in served.items():
        if served_path.read_bytes() != static[relative].read_bytes():
            fail(f"static mirror differs: {relative}")


def validate_tracked_hygiene() -> None:
    git = shutil.which("git")
    if git is None:
        fail("git is required for repository hygiene validation")
    # Fixed, read-only repository query with no user-controlled command content.
    result = subprocess.run(  # nosec B603
        [git, "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = Path(raw.decode())
        if any(part in IGNORED_PARTS for part in relative.parts):
            fail(f"generated directory is tracked: {relative}")
        if relative.suffix in {".db", ".pyc", ".sqlite", ".sqlite3"}:
            fail(f"generated runtime file is tracked: {relative}")
        if relative.name.endswith(("-shm", "-wal")):
            fail(f"SQLite sidecar is tracked: {relative}")


def validate_text() -> None:
    for path in ROOT.rglob("*"):
        if (
            not path.is_file()
            or path.suffix not in TEXT_EXTENSIONS
            or any(part in IGNORED_PARTS for part in path.relative_to(ROOT).parts)
        ):
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        lowered = content.lower()
        for forbidden in FORBIDDEN_TEXT:
            if forbidden.lower() in lowered:
                fail(f"placeholder URL, stale port, or removed branding in {path.relative_to(ROOT)}")


def validate_standard_port() -> None:
    required = (
        ".env.example",
        "Dockerfile",
        "QUICKSTART.md",
        "README.md",
        "docker-compose.yml",
        "docs/DEMO.md",
        "docs/DEPLOYMENT.md",
        "scripts/demo.sh",
        "scripts/smoke.sh",
        "src/conversation_success_coach/cli.py",
    )
    for relative in required:
        path = ROOT / relative
        if "8103" not in path.read_text(encoding="utf-8"):
            fail(f"standard port 8103 missing from {relative}")


def validate_uv_deployment() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    required = (
        "FROM python:3.12-alpine3.24@sha256:",
        "COPY --from=ghcr.io/astral-sh/uv:0.10.7@sha256:",
        "RUN apk upgrade --no-cache",
        "COPY pyproject.toml uv.lock README.md LICENSE NOTICE ./",
        "uv sync --locked --no-dev --no-editable",
        "USER coach",
        '"uv", "run", "--locked", "--no-dev", "--no-sync"',
    )
    for snippet in required:
        if snippet not in dockerfile:
            fail(f"Docker deployment is missing required uv configuration: {snippet}")
    if "pip install" in dockerfile:
        fail("Docker deployment must install through uv, not pip")

    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    if "${CSC_BIND_ADDRESS:-127.0.0.1}:${CSC_PORT:-8103}:8103" not in compose:
        fail("Compose must bind the unauthenticated demo to loopback by default")

    for relative in ("scripts/demo.sh", "scripts/test.sh", "scripts/smoke.sh"):
        content = (ROOT / relative).read_text(encoding="utf-8")
        if "uv run --locked" not in content:
            fail(f"{relative} must use the locked uv environment")


def validate_workflows() -> None:
    workflow_files = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    unpinned = re.compile(r"^\s*uses:\s*(?!\./)([^@\s]+)@([^#\s]+)", re.MULTILINE)
    full_sha = re.compile(r"^[0-9a-f]{40}$")
    for workflow in workflow_files:
        content = workflow.read_text(encoding="utf-8")
        for match in unpinned.finditer(content):
            if not full_sha.fullmatch(match.group(2)):
                fail(
                    f"GitHub Action is not pinned to a full commit SHA in "
                    f"{workflow.relative_to(ROOT)}: {match.group(0).strip()}"
                )

    pages = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    for snippet in (
        'if: ${{ github.event.repository.private == false }}',
        'UV_PYTHON: "3.12"',
        'uv sync --python "3.12" --locked --extra dev',
        "uv run --locked --extra dev python scripts/validate_package.py",
        "node scripts/test_public_site.mjs",
    ):
        if snippet not in pages:
            fail(f"Pages workflow is missing required validation: {snippet}")

    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for snippet in (
        "UV_PYTHON: ${{ matrix.python-version }}",
        'UV_PYTHON: "3.12"',
        "pip-audit",
        "bandit",
        "node scripts/test_public_site.mjs",
        "uv build",
    ):
        if snippet not in ci:
            fail(f"CI is missing required coverage: {snippet}")


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"invalid PNG file: {path.relative_to(ROOT)}")
    return struct.unpack(">II", data[16:24])


def validate_diagrams() -> None:
    for stem in ("system-architecture", "aws-reference-architecture"):
        drawio = SITE / "assets" / f"{stem}.drawio"
        try:
            root = ET.parse(drawio).getroot()
        except ET.ParseError as error:
            fail(f"invalid draw.io XML in {drawio.relative_to(ROOT)}: {error}")
        if root.tag != "mxfile" or not root.findall("diagram"):
            fail(f"draw.io source has no diagram page: {drawio.relative_to(ROOT)}")

        width, height = png_dimensions(SITE / "assets" / f"{stem}.png")
        if width < 1000 or height < 500:
            fail(f"architecture PNG is too small for publication: {stem} ({width}x{height})")


def validate_public_mode() -> None:
    site_js = (WEB / "assets" / "site.js").read_text(encoding="utf-8")
    dashboard_js = (WEB / "assets" / "dashboard.js").read_text(encoding="utf-8")
    browser_test = (ROOT / "scripts" / "test_public_site.mjs").read_text(encoding="utf-8")

    for snippet in (
        'window.location.hostname.endsWith(".github.io")',
        'get("public-site") === "true"',
        'document.documentElement.dataset.publicSite',
    ):
        if snippet not in site_js or snippet not in dashboard_js:
            fail(f"published-mode detection is missing: {snippet}")

    for snippet in (
        'const publicBase = "/conversation-success-coach/";',
        'cdp.on("Network.webSocketCreated"',
        'document.documentElement.dataset.publicSite === "true"',
        'url.pathname.startsWith("/api/")',
    ):
        if snippet not in browser_test:
            fail(f"public-site browser test is missing required coverage: {snippet}")

    for path in relative_files(SITE).values():
        if path.suffix not in TEXT_EXTENSIONS:
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"https?://[^\"'\s]*execute-api|wss://|\.amazonaws\.com", content, re.I):
            fail(f"public site contains a private cloud endpoint marker: {path.relative_to(ROOT)}")


def main() -> None:
    validate_required_artifacts()
    validate_mirror()
    validate_tracked_hygiene()
    validate_text()
    validate_standard_port()
    validate_uv_deployment()
    validate_workflows()
    validate_diagrams()
    validate_public_mode()
    print(
        "Publication artifacts, static mirror, repository hygiene, locked uv deployment, "
        "diagrams, workflows, and Pages boundaries passed."
    )


if __name__ == "__main__":
    main()
