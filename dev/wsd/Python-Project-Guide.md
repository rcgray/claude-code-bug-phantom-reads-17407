# Python Project Setup Guide

**Version:** 1.0.0
**Audience:** Developers integrating WSD into Python projects

## Introduction

This guide covers the specific setup requirements for using Workscope-Dev (WSD) with Python projects. WSD provides Python-specific tools for health checks, code documentation, and API generation that require additional configuration beyond the basic WSD installation.

For general WSD installation instructions, see the Integration-Guide.md first, then return here for Python-specific configuration.

**Related Documentation:**
- **`pyproject.toml.md`** - Authoritative reference for pyproject.toml configuration and dependencies. Use this file as your copy-paste source for configuration snippets.
- **Integration-Guide.md** - General WSD installation instructions
- **Node-Project-Guide.md** - Setup guide for JavaScript/TypeScript projects

## Prerequisites

Before configuring WSD for Python, ensure you have:

- **WSD installed**: Follow Integration-Guide.md to install WSD into your project
- **Python 3.10+**: Required for all WSD Python tooling (3.11+ recommended)
- **uv**: Astral's fast Python package manager (required for WSD operations)

### Installing uv

WSD uses `uv` for dependency management and running Python tools. Install it if not already present:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

See https://github.com/astral-sh/uv for more installation options.

## Quick Start

If you're integrating WSD into an **existing Python project** that already has pytest, ruff, and mypy configured, the minimum setup is:

```bash
# 1. Install WSD (if not already done)
python /path/to/wsd-source/wsd.py install .

# 2. Add [tool.wsd] to your pyproject.toml (see Configuration section)

# 3. Install dev dependencies
uv sync --extra dev

# 4. Test the health check
./wsd.py health
```

If starting from scratch or missing dependencies, follow the complete setup below.

## Project Detection

WSD automatically detects Python projects by looking for:

| File             | Detection Result |
| ---------------- | ---------------- |
| `pyproject.toml` | Python project   |

The `update_docs.py` script and task runner use this detection to run the appropriate tools.

## Required Configuration

### pyproject.toml [tool.wsd] Section

WSD requires a `[tool.wsd]` section in your `pyproject.toml` to specify which directories to check for linting, type checking, and other quality tools:

```toml
[tool.wsd]
check_dirs = ["src", "tests"]
```

**Important**: Without this configuration, WSD commands like `./wsd.py lint`, `./wsd.py type`, and `./wsd.py health` will fail with an error message.

The first directory in `check_dirs` is used for bandit security scanning; all directories are used for ruff and mypy. Adjust paths to match your project structure (e.g., `["mypackage", "tests"]` for single-package layouts).

See **`pyproject.toml.md`** for the complete configuration reference with examples.

## Required Dependencies

WSD's Python tools require specific packages to function. The table below summarizes what's needed:

| Package        | Purpose                   | Required         | WSD Feature                                      |
| -------------- | ------------------------- | ---------------- | ------------------------------------------------ |
| `ruff`         | Linting & formatting      | **Yes**          | `./wsd.py lint`, `./wsd.py format`, health check |
| `mypy`         | Type checking             | **Yes**          | `./wsd.py type`, health check                    |
| `pytest`       | Testing                   | **Yes**          | `./wsd.py test`                                  |
| `pytest-cov`   | Coverage reporting        | **Yes**          | `./wsd.py test:coverage`                         |
| `bandit`       | Security scanning         | Optional         | Health check (skips if missing)                  |
| `pip-audit`    | Dependency audit          | Optional         | Health check (skips if missing)                  |
| `pytest-watch` | Watch mode testing        | Optional         | `./wsd.py test:watch`                            |
| `coverage`     | Markdown coverage reports | Optional         | `update_docs.py`                                 |
| `pdoc`         | API documentation         | Optional         | `codedocs_pdoc.py`                               |
| `tomli`        | TOML parsing              | Python 3.10 only | Core WSD functionality                           |

### Quick Install

Install all required dependencies:

```bash
uv add --dev ruff mypy pytest pytest-cov
```

For a fully-featured installation with all optional packages:

```bash
uv add --dev ruff mypy pytest pytest-cov pytest-watch coverage bandit pip-audit pdoc
```

### Graceful Degradation

Optional packages enable additional WSD features. When missing, the health check **gracefully skips** these checks rather than failing - they appear with "SKIPPED" status in the summary. Install them when you want those specific quality checks enabled.

### Python 3.10 Compatibility

If using Python 3.10 (not 3.11+), also add `tomli` for TOML parsing:

```bash
uv add --dev tomli
```

Python 3.11+ includes `tomllib` in the standard library.

**See `pyproject.toml.md`** for complete dependency configuration examples using both `[project.optional-dependencies]` and `[tool.uv]` formats.

## Tool Configuration

WSD's Python tools (ruff, mypy, pytest, bandit) are configured via `pyproject.toml`. Each tool has sensible defaults, but you'll want to customize them for your project.

### Configuration Summary

| Tool   | Section                     | Purpose                                        |
| ------ | --------------------------- | ---------------------------------------------- |
| Ruff   | `[tool.ruff]`               | Linting rules, formatting options, line length |
| Mypy   | `[tool.mypy]`               | Type checking strictness, Python version       |
| Pytest | `[tool.pytest.ini_options]` | Test paths, coverage settings                  |
| Bandit | `[tool.bandit]`             | Security scan exclusions                       |

### Key Configuration Points

**Ruff**: WSD health check uses ruff for both linting (`ruff check`) and formatting (`ruff format`). Configure your preferred rules in `[tool.ruff.lint]` and set `convention = "google"` in `[tool.ruff.lint.pydocstyle]` for Google-style docstrings.

**Mypy**: Enable `strict = true` for comprehensive type checking. Use `[[tool.mypy.overrides]]` to relax rules for test files.

**Pytest**: Set `testpaths` to your test directory. Configure coverage in `[tool.coverage.run]` and `[tool.coverage.report]`.

**Bandit**: Exclude test directories and virtual environments from security scanning.

**See `pyproject.toml.md`** for complete, copy-paste-ready configuration examples for all tools.

## WSD Command Reference

### Task Runner Commands

WSD's task runner (`wsd.py`) provides these commands for Python projects:

| WSD Command                  | Underlying Tool                          | Description                     |
| ---------------------------- | ---------------------------------------- | ------------------------------- |
| `./wsd.py health`            | Multiple                                 | Runs comprehensive health check |
| `./wsd.py health:aggressive` | Multiple                                 | Health check with unsafe fixes  |
| `./wsd.py test`              | `uv run pytest`                          | Run test suite                  |
| `./wsd.py test:watch`        | `uv run pytest-watch`                    | Run tests in watch mode         |
| `./wsd.py test:coverage`     | `uv run pytest --cov`                    | Run tests with coverage         |
| `./wsd.py lint`              | `uv run ruff check`                      | Check for lint errors           |
| `./wsd.py lint:fix`          | `uv run ruff check --fix`                | Auto-fix lint errors            |
| `./wsd.py lint:aggressive`   | `uv run ruff check --fix --unsafe-fixes` | Aggressive lint fixes           |
| `./wsd.py lint:docs`         | `uv run ruff check --select D`           | Check docstrings only           |
| `./wsd.py lint:docs:fix`     | `uv run ruff check --select D --fix`     | Fix docstring issues            |
| `./wsd.py format`            | `uv run ruff format`                     | Format code                     |
| `./wsd.py format:check`      | `uv run ruff format --check`             | Check formatting                |
| `./wsd.py type`              | `uv run mypy`                            | Type check code                 |
| `./wsd.py security`          | `uv run bandit`                          | Run security scan               |
| `./wsd.py build`             | `uv build`                               | Build package                   |
| `./wsd.py sync`              | `uv sync`                                | Sync dependencies               |
| `./wsd.py audit`             | `uv run pip-audit`                       | Audit dependencies              |
| `./wsd.py audit:fix`         | `uv run pip-audit --fix`                 | Fix vulnerable deps             |

### Health Check (`./wsd.py health`)

The health check provides comprehensive code quality validation through eight sequential checks. It serves as the pre-commit quality gate, ensuring all code meets established standards before integration.

#### Check Execution Sequence

Checks run in a specific order designed to identify structural issues first, then progressively validate quality, security, and style:

1. **Build Validation**: Runs `uv build` to verify `pyproject.toml` configuration and package build process
2. **Type Checking (mypy)**: Validates type correctness with intelligent output analysis that filters known false positives and detects mypy crashes
3. **Security Scan (bandit)**: Static security analysis scanning for common vulnerabilities (skips if not installed)
4. **Dependency Audit (pip-audit)**: Checks installed packages against known CVE vulnerabilities (skips if not installed)
5. **Doc Completeness**: Custom AST-based validation ensuring dataclass fields and public method parameters are documented
6. **Documentation (ruff)**: Checks and auto-fixes docstring formatting issues
7. **Linting (ruff)**: Checks and auto-fixes code quality issues
8. **Code Formatting (ruff)**: Checks and auto-fixes code style

#### Auto-Fix Behavior

The health check automatically fixes issues where safe transformations exist:

- **Documentation**: Adds template docstrings, fixes formatting
- **Linting**: Applies safe fixes that don't change code behavior
- **Formatting**: Reformats code to consistent style (always safe)

Fixed issues show `✅ FIXED` status rather than failure, and the health check succeeds.

#### Command-Line Flags

| Flag           | Description                                                                 |
| -------------- | --------------------------------------------------------------------------- |
| `--aggressive` | Enable unsafe fixes during linting (transformations that may change behavior) |
| `--commands`   | Display all underlying commands used by each check without running them     |

#### Status Indicators

| Status       | Meaning                                          |
| ------------ | ------------------------------------------------ |
| `✅ PASSED`  | Check completed with no issues                   |
| `✅ FIXED`   | Issues detected and automatically fixed          |
| `❌ FAILED`  | Issues detected that could not be auto-fixed     |
| `⚠️ WARNING` | Non-blocking issues detected                     |
| `⏭️ SKIPPED` | Check not run (optional tool not installed)      |

#### Example Output

**Successful run with auto-fixes:**
```
============================================================
Starting Python Project Health Check...
Checking directories: src tests
Running in SAFE mode (use --aggressive for more fixes)
============================================================

...

============================================================
HEALTH CHECK SUMMARY
============================================================
Check                Status          Details
------------------------------------------------------------
Build Validation     ✅ PASSED
Type Checking        ✅ PASSED
Security Scan        ✅ PASSED
Dependency Audit     ✅ PASSED
Doc Completeness     ✅ PASSED
Documentation        ✅ FIXED        All issues auto-fixed
Linting              ✅ FIXED        All issues auto-fixed
Code Formatting      ✅ PASSED
============================================================

✅ Project Health Check completed successfully!
============================================================
```

**Run with failures:**
```
============================================================
HEALTH CHECK SUMMARY
============================================================
Check                Status          Details
------------------------------------------------------------
Build Validation     ✅ PASSED
Type Checking        ❌ FAILED        2 error(s)
Security Scan        ✅ PASSED
Dependency Audit     ✅ PASSED
Doc Completeness     ✅ PASSED
Documentation        ✅ PASSED
Linting              ❌ FAILED        5 unfixable issues (12 more fixable with --aggressive)
Code Formatting      ✅ PASSED
============================================================

❌ Project Health Check found issues that need attention.
============================================================
```

#### Viewing Available Commands

Use `--commands` to see all underlying tool commands without running them:

```bash
./wsd.py health --commands
```

This displays a reference table showing exact commands for each check, useful for manual execution or CI/CD integration.

### Documentation Scripts

**Code Summary (`codedocs_python.py`):**
Generates a markdown summary of Python code structure:

```bash
python scripts/codedocs_python.py src/
```

**API Documentation (`codedocs_pdoc.py`):**
Generates HTML API documentation using pdoc:

```bash
python scripts/codedocs_pdoc.py mypackage --source-dir src --output-dir dev/reports/api-docs
```

**Update Docs (`update_docs.py`):**
Unified documentation script that auto-detects Python projects:

```bash
python scripts/update_docs.py          # Full mode (tests, docs, health check)
python scripts/update_docs.py --quick  # Quick mode (structure, file lists, code summary)
```

## Integration Scenarios

### Scenario 1: New Python Project

Starting from scratch with WSD and Python:

```bash
# Create project
mkdir my-python-project && cd my-python-project
uv init

# Add dev dependencies
uv add --dev ruff mypy pytest pytest-cov

# Add [tool.wsd] to pyproject.toml
cat >> pyproject.toml << 'EOF'

[tool.wsd]
check_dirs = ["src", "tests"]
EOF

# Install WSD
python /path/to/wsd-source/wsd.py install .

# Create initial structure
mkdir -p src/mypackage tests
touch src/mypackage/__init__.py tests/__init__.py

# Initialize git and test
git init
./wsd.py health
git add . && git commit -m "Initialize project with WSD"
```

### Scenario 2: Existing Python Project

Adding WSD to a project with existing Python setup:

```bash
cd my-existing-python-project

# Checkpoint
git add -A && git commit -m "Checkpoint before WSD"

# Install WSD
python /path/to/wsd-source/wsd.py install .

# Add [tool.wsd] to pyproject.toml if not present
# Verify check_dirs matches your project structure

# Install dev dependencies if missing
uv add --dev ruff mypy pytest pytest-cov

# Test health check
./wsd.py health

# Commit WSD
git add -A && git commit -m "Add Workscope-Dev framework"
```

### Scenario 3: Mixed Python/TypeScript Project

For projects with both Python and TypeScript:

```bash
cd my-mixed-project

# Install WSD
python /path/to/wsd-source/wsd.py install .

# Add Python configuration to pyproject.toml
[tool.wsd]
check_dirs = ["src/python", "tests/python"]

# Add JavaScript/TypeScript configuration to package.json
# See Node-Project-Guide.md

# WSD commands will run for BOTH languages
./wsd.py health   # Runs Python health check
./wsd.py test     # Runs pytest AND jest
./wsd.py lint     # Runs ruff AND eslint
```

## Troubleshooting

### Health Check Fails Immediately

**Symptom:** `./wsd.py health` fails with "uv not found"

**Solution:** Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Missing [tool.wsd] Configuration

**Symptom:** Health check fails with "ERROR: [tool.wsd] configuration missing"

**Solution:** Add the configuration to pyproject.toml:
```toml
[tool.wsd]
check_dirs = ["src", "tests"]
```

### Type Checking Fails

**Symptom:** mypy reports many errors

**Solutions:**
1. Ensure all dependencies have type stubs:
   ```bash
   uv add --dev types-requests types-PyYAML  # etc.
   ```
2. Add `# type: ignore` comments for third-party libraries without stubs
3. Adjust strictness in `[tool.mypy]` configuration

### Security Scan Skipped

**Symptom:** Health check shows "Security Scan SKIPPED"

**Solution:** Install bandit:
```bash
uv add --dev bandit
```

### Dependency Audit Skipped

**Symptom:** Health check shows "Dependency Audit SKIPPED"

**Solution:** Install pip-audit:
```bash
uv add --dev pip-audit
```

### Build Validation Fails

**Symptom:** Health check fails on "Build validation"

**Solutions:**
1. Verify pyproject.toml has correct `[build-system]` section
2. Check that all package metadata is valid
3. Ensure source files are included via `[tool.hatch.build]` or similar

### Import Errors in Tests

**Symptom:** pytest can't find your package

**Solution:** Ensure your package is installed in editable mode:
```bash
uv pip install -e .
```

Or use `uv sync` which handles this automatically.

## CI/CD Integration

The health check is designed for easy integration into CI/CD pipelines. It uses standard exit codes (0 for success, 1 for failure) and produces clear, parseable output.

### GitHub Actions

Create `.github/workflows/quality.yml`:

```yaml
name: Code Quality

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.11

      - name: Install dependencies
        run: uv sync --extra dev

      - name: Run health check
        run: ./wsd.py health
```

### GitLab CI

Add to `.gitlab-ci.yml`:

```yaml
stages:
  - quality

health-check:
  stage: quality
  image: python:3.11
  before_script:
    - pip install uv
    - uv sync --extra dev
  script:
    - ./wsd.py health
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
```

### Pre-commit Hook

Run health check before each commit by creating `.git/hooks/pre-commit`:

```bash
#!/bin/bash
./wsd.py health
if [ $? -ne 0 ]; then
    echo "Health check failed. Please fix issues before committing."
    exit 1
fi
```

Make it executable: `chmod +x .git/hooks/pre-commit`

### Exit Codes

| Exit Code | Meaning                                          |
| --------- | ------------------------------------------------ |
| 0         | All checks passed or were auto-fixed (success)   |
| 1         | One or more checks failed or system error        |

**Note:** `⚠️ WARNING` status does not cause exit code 1 (non-blocking).

### Best Practices for CI/CD

**Run health check early**: Place health check at the start of your pipeline. Failing fast on code quality issues saves CI resources.

**Use caching**: Cache the `.venv/` or `uv` cache directory to speed up dependency installation:

```yaml
# GitHub Actions caching example
- uses: actions/cache@v4
  with:
    path: .venv
    key: venv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
```

**Separate test and quality jobs**: Run `./wsd.py health` and `./wsd.py test` as separate jobs so they can run in parallel:

```yaml
jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      # ... setup steps ...
      - run: ./wsd.py health

  tests:
    runs-on: ubuntu-latest
    steps:
      # ... setup steps ...
      - run: ./wsd.py test:coverage
```

**Pin Python version**: Specify an exact Python version to ensure consistent results across environments.

**Review auto-fixes**: The health check auto-fixes issues in safe mode. Review these changes before committing with `git diff`.

## Complete Example pyproject.toml

For a complete, copy-paste-ready pyproject.toml example with all WSD configuration, dependencies, and tool settings, see **`pyproject.toml.md`**.

That file contains:
- Required `[tool.wsd]` configuration
- Complete dependency lists (both `[project.optional-dependencies]` and `[tool.uv]` formats)
- Full tool configurations for ruff, mypy, pytest, and bandit
- Build system setup

## Next Steps

After completing Python setup:

1. **Run health check**: `./wsd.py health` to verify everything works
2. **Generate documentation**: `python scripts/update_docs.py --quick` to test doc generation
3. **Customize WORKSCOPE-DEV tags**: Fill in project-specific content in WSD files
4. **Set up Action Plan**: Add your project phases and tasks
5. **Start your first session**: Run `/wsd:init` in Claude Code

For updates and maintenance, see Update-Guide.md.

---

*This guide covers Python-specific WSD configuration. For general installation, see Integration-Guide.md. For the task runner, see Task-Runner-Guide.md.*
