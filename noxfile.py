"""Task runner for TokenHelm. Run ``nox -l`` to list sessions.

Common commands (so contributors don't memorize long invocations):

    nox -s install        # editable install with dev extras
    nox -s lint           # ruff check + format check
    nox -s format         # auto-format + autofix
    nox -s test           # full test suite (current interpreter)
    nox -s coverage       # tests with the 90% coverage gate
    nox -s benchmark      # performance/memory budget checks
    nox -s build          # build sdist + wheel, then twine check
    nox -s docs           # audit that docs/exports match the implementation
    nox -s release_test   # build + upload to TestPyPI (needs creds)
    nox -s release        # build + upload to PyPI (needs creds)

    nox                   # default: lint, test, coverage
"""

from __future__ import annotations

import nox

nox.options.sessions = ["lint", "test", "coverage"]
nox.options.reuse_existing_virtualenvs = True

PYTHONS = ["3.11", "3.12", "3.13"]
LINT_PATHS = ["src", "tests", "noxfile.py"]


@nox.session
def install(session: nox.Session) -> None:
    """Editable install with the dev toolchain."""
    session.install("-e", ".[dev]")


@nox.session
def lint(session: nox.Session) -> None:
    """Check formatting and lint rules (no changes)."""
    session.install("ruff==0.15.20")  # keep in sync with ci.yml and .pre-commit-config.yaml
    session.run("ruff", "check", *LINT_PATHS)
    session.run("ruff", "format", "--check", *LINT_PATHS)


@nox.session
def format(session: nox.Session) -> None:
    """Auto-format and apply safe lint fixes."""
    session.install("ruff==0.15.20")  # keep in sync with ci.yml and .pre-commit-config.yaml
    session.run("ruff", "format", *LINT_PATHS)
    session.run("ruff", "check", "--fix", *LINT_PATHS)


@nox.session(python=PYTHONS)
def test(session: nox.Session) -> None:
    """Run the test suite (parametrized across supported Pythons)."""
    session.install("-e", ".[dev]")
    session.run("pytest", "-q", *session.posargs)


@nox.session
def coverage(session: nox.Session) -> None:
    """Run tests with the coverage gate."""
    session.install("-e", ".[dev]")
    session.run(
        "pytest",
        "--cov=tokenhelm",
        "--cov-report=term-missing",
        "--cov-fail-under=90",
        *session.posargs,
    )


@nox.session
def benchmark(session: nox.Session) -> None:
    """Run the performance/memory budget checks."""
    session.install("-e", ".[dev]")
    session.run("pytest", "-m", "benchmark", "-q", *session.posargs)


@nox.session
def build(session: nox.Session) -> None:
    """Build sdist + wheel and validate metadata."""
    session.install("build", "twine")
    session.run("python", "-m", "build")
    session.run("twine", "check", "dist/*")


@nox.session
def docs(session: nox.Session) -> None:
    """Audit that the public exports and API docs match the implementation."""
    session.install("-e", ".")
    session.run("python", "scripts/check_public_api.py")


@nox.session
def release_test(session: nox.Session) -> None:
    """Build and upload to TestPyPI (requires TestPyPI credentials / token)."""
    session.install("build", "twine")
    session.run("python", "-m", "build")
    session.run("twine", "check", "dist/*")
    session.run("twine", "upload", "--repository", "testpypi", "dist/*")


@nox.session
def release(session: nox.Session) -> None:
    """Build and upload to PyPI (requires PyPI credentials / token).

    Prefer the automated Trusted Publishing flow (push a tag) over running this locally.
    """
    session.install("build", "twine")
    session.run("python", "-m", "build")
    session.run("twine", "check", "dist/*")
    session.run("twine", "upload", "dist/*")
