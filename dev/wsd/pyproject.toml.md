# Sample pyproject.toml for WSD Projects

This file documents the pyproject.toml configuration required for WSD integration. The configuration you need depends on whether your project contains Python code or is a codeless project (documentation, research, etc.).

For complete setup instructions, see `Python-Project-Guide.md`. For codeless projects, see `Codeless-Project-Guide.md`.

---

## Understanding Configuration Levels

WSD supports two types of projects, each requiring different `pyproject.toml` configurations:

### Minimal Configuration (Codeless Projects)

If your project uses WSD for AI-assisted workflows but contains no Python source code (e.g., research papers, business documents, technical writing), you only need minimal configuration:

```toml
# Minimal pyproject.toml for codeless projects
[tool.wsd]
check_dirs = []  # No source directories to check

[tool.uv]
dev-dependencies = []  # Minimal deps for WSD operation
```

With this configuration:
- WSD's workscope management, agent coordination, and documentation systems work normally
- Python-specific health checks (linting, type checking, security scanning) are automatically skipped
- The health check reports these as "SKIPPED" with the reason "not a Python project (codeless)"

**Key point:** The `[project]` section is NOT required for codeless projects. That section is PEP 621 metadata for Python packages, which codeless projects don't need.

### Full Configuration (Python Projects)

If your project contains Python source code, you need the full configuration including:
- `[project]` section with package metadata
- `[tool.wsd]` with `check_dirs` pointing to your source directories
- Development dependencies for quality tools

WSD determines your project is a Python project if either:
1. Your `pyproject.toml` has a `[project]` section, OR
2. There are `.py` files in your configured `check_dirs`

See the sections below for complete Python project configuration.

---

## Required: WSD Configuration

WSD requires this section to know which directories to check for linting, type checking, and other quality tools:

```toml
# <WORKSCOPE‑DEV pyproject-toml-settings>: Users should update these paths
[tool.wsd]
# Directories for ruff/mypy coverage. First should be project source (for bandit, etc.)
check_dirs = ["src", "tests"]
# </WORKSCOPE‑DEV>
```

**Important Notes:**
- The first directory in `check_dirs` is used for bandit security scanning
- All directories are used for ruff linting, mypy type checking, and formatting
- Update these paths to match your project structure

**Note on confusable characters:** The tag example above uses a non-breaking hyphen `‑` (U+2011) instead of the regular hyphen `-` (U+002D) in "WORKSCOPE‑DEV". This is intentional—documentation examples use this visually identical character to prevent the tag scanner from detecting them as real tags. When creating actual tags in your project, use the regular hyphen. See `Tag-Registry.md § Writing Tag Examples in Documentation` for details.

---

## Required: Development Dependencies

These dependencies are required for WSD tools to function:

### Option A: Using [project.optional-dependencies]

```toml
[project.optional-dependencies]
dev = [
    # Linting and formatting (REQUIRED)
    "ruff>=0.1.0",

    # Type checking (REQUIRED)
    "mypy>=1.8.0",

    # Testing (REQUIRED)
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",

    # Security scanning (optional - health check skips if missing)
    "bandit>=1.7.6",

    # Dependency auditing (optional - health check skips if missing)
    "pip-audit>=2.6.0",

    # Additional testing tools (optional)
    "pytest-watch>=4.2.0",
    "coverage>=7.0.0",

    # API documentation (optional - for codedocs_pdoc.py)
    "pdoc>=14.0.0",
]
```

Install with: `uv sync --extra dev`

### Option B: Using [tool.uv] (uv-native)

```toml
[tool.uv]
dev-dependencies = [
    # Linting and formatting (REQUIRED)
    "ruff>=0.1.0",

    # Type checking (REQUIRED)
    "mypy>=1.8.0",

    # Testing (REQUIRED)
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",

    # Security scanning (optional - health check skips if missing)
    "bandit>=1.7.6",

    # Dependency auditing (optional - health check skips if missing)
    "pip-audit>=2.6.0",

    # Additional testing tools (optional)
    "pytest-watch>=4.2.0",
    "coverage>=7.0.0",

    # API documentation (optional - for codedocs_pdoc.py)
    "pdoc>=14.0.0",
]
```

Install with: `uv sync`

### Python 3.10 Compatibility

If using Python 3.10 (not 3.11+), also add:

```toml
    # TOML parsing fallback for Python 3.10
    "tomli>=2.0.0",
```

Python 3.11+ includes `tomllib` in the standard library.

---

## Recommended: Tool Configuration

### Ruff Configuration

```toml
[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "PL",     # Pylint
    "D",      # pydocstyle - docstring conventions (recommended)
]
ignore = [
    "E501",   # Line too long (handled by formatter)
]

[tool.ruff.lint.pydocstyle]
# Google convention automatically excludes opinionated rules like D413
# (blank line after last section), D203, D213, etc.
convention = "google"
```

**Note on pydocstyle (D rules):** We recommend enabling D rules with the Google convention, which automatically excludes overly opinionated rules (like D413 requiring blank lines before closing `"""`). Alternative conventions are `"numpy"` and `"pep257"`. If you prefer not to enforce docstring conventions, you can move `"D"` from `select` to `ignore`, but this is not recommended for projects that value documentation quality.

### Mypy Configuration

```toml
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

### Pytest Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "**/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

### Bandit Configuration

```toml
[tool.bandit]
exclude_dirs = ["tests", "venv", ".venv"]
skips = []
```

---

## Complete Example

Here's a complete pyproject.toml example for a WSD Python project:

```toml
[project]
name = "example-project"
version = "0.1.0"
description = "Example project using WSD Task Runner"
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
dev = [
    # Testing
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-watch>=4.2.0",
    "coverage>=7.0.0",

    # Linting and formatting
    "ruff>=0.1.0",

    # Type checking
    "mypy>=1.8.0",

    # Security
    "bandit>=1.7.6",
    "pip-audit>=2.6.0",

    # Documentation
    "pdoc>=14.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/example_project"]

# WSD Configuration (REQUIRED)
[tool.wsd]
check_dirs = ["src", "tests"]

# Ruff Configuration
[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "C4", "UP", "PL", "D"]
ignore = ["E501"]

[tool.ruff.lint.pydocstyle]
convention = "google"

# Mypy Configuration
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_ignores = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

# Pytest Configuration
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["src"]

[tool.coverage.report]
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:"]

# Bandit Configuration
[tool.bandit]
exclude_dirs = ["tests", ".venv"]
```

---

## Dependency Summary

| Package        | Purpose                   | Required        | WSD Feature                                      |
| -------------- | ------------------------- | --------------- | ------------------------------------------------ |
| `ruff`         | Linting & formatting      | Yes             | `./wsd.py lint`, `./wsd.py format`, health check |
| `mypy`         | Type checking             | Yes             | `./wsd.py type`, health check                    |
| `pytest`       | Testing                   | Yes             | `./wsd.py test`                                  |
| `pytest-cov`   | Coverage reporting        | Yes             | `./wsd.py test:coverage`                         |
| `bandit`       | Security scanning         | Optional        | Health check (skips if missing)                  |
| `pip-audit`    | Dependency audit          | Optional        | Health check (skips if missing)                  |
| `pytest-watch` | Watch mode testing        | Optional        | `./wsd.py test:watch`                            |
| `coverage`     | Markdown coverage reports | Optional        | `update_docs.py`                                 |
| `pdoc`         | API documentation         | Optional        | `codedocs_pdoc.py`                               |
| `tomli`        | TOML parsing (3.10 only)  | For Python 3.10 | Core WSD functionality                           |

---

*See `Python-Project-Guide.md` for complete setup instructions and troubleshooting.*
