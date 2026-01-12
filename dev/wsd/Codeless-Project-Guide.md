# Codeless Project Setup Guide

**Version:** 1.0.0
**Audience:** Users integrating WSD into non-code projects

## Introduction

WSD supports "codeless projects" - projects that benefit from AI-assisted workflows but contain no programming source code. These projects use WSD's workscope management, agent coordination, and documentation systems without needing code quality tools like linters or type checkers.

Examples of codeless projects:
- Academic research papers
- Business strategy documents
- Technical writing projects
- Documentation-only repositories
- Planning and design projects

This guide covers how to set up WSD for codeless projects with minimal configuration.

## What Makes a Project "Codeless"

WSD classifies your project based on what it finds in your repository:

| Project Type | Detection Criteria |
|--------------|-------------------|
| TypeScript | Has `tsconfig.json` |
| JavaScript | Has `package.json` (without TypeScript) |
| Python | Has `[project]` section in `pyproject.toml` OR has `.py` files in `check_dirs` |
| Codeless | None of the above |

A codeless project has `pyproject.toml` (required for WSD's Python scripts to run) but lacks the indicators of an actual programming project.

## Quick Start

Setting up WSD for a codeless project requires just three steps:

```bash
# 1. Install WSD into your project
python /path/to/wsd-source/wsd.py install .

# 2. Create minimal pyproject.toml
cat > pyproject.toml << 'EOF'
[tool.wsd]
check_dirs = []

[tool.uv]
dev-dependencies = []
EOF

# 3. Install dependencies and verify
uv sync
./wsd.py health
```

The health check should show all Python-specific checks as "SKIPPED" with the reason "not a Python project (codeless)".

## Configuration

### Minimal pyproject.toml

Codeless projects need only the `[tool.wsd]` and `[tool.uv]` sections:

```toml
# pyproject.toml for a codeless project
[tool.wsd]
check_dirs = []  # No source directories to check

[tool.uv]
dev-dependencies = []  # No dev tools needed
```

### Why No [project] Section?

The `[project]` section is PEP 621 metadata for Python packages - it defines package name, version, dependencies, and distribution information. Codeless projects aren't Python packages, so they don't need this section.

WSD uses the absence of `[project]` (combined with no `.py` files in `check_dirs`) to identify your project as codeless and automatically skip Python-specific quality checks.

### Optional: Adding Python Dependencies

If your workflow uses Python scripts (even if they're not "your project's code"), you can add them:

```toml
[tool.wsd]
check_dirs = []  # Still no source directories to lint/check

[tool.uv]
dev-dependencies = [
    "requests",  # For custom scripts
    "pyyaml",    # For configuration parsing
]
```

These dependencies are available for WSD's scripts and any utilities you create, but WSD won't run linting or type checking on them since `check_dirs` is empty.

## WSD Features for Codeless Projects

### Features That Work Normally

| Feature | Description |
|---------|-------------|
| Workscope Management | Task assignment, tracking, and documentation |
| Agent Coordination | All Special Agents function normally |
| Documentation System | `docs/` hierarchy, workbench, archival |
| Checkboxlist System | Action plans, tickets, feature specs |
| Work Journals | Session documentation and handoffs |
| Custom Commands | All `/wsd:*` slash commands |

These features are the core value of WSD and work identically for codeless projects.

### Features That Are Skipped

| Feature | Reason |
|---------|--------|
| Linting (`./wsd.py lint`) | No source code to lint |
| Type Checking (`./wsd.py type`) | No source code to type check |
| Security Scanning (`./wsd.py security`) | No source code to scan |
| Test Running (`./wsd.py test`) | No tests to run |
| Build Validation | No package to build |
| Code Formatting | No source code to format |

When you run `./wsd.py health`, these checks appear as "SKIPPED" rather than failures:

```
============================================================
HEALTH CHECK SUMMARY
============================================================
Check                Status          Details
------------------------------------------------------------
Build Validation     ⏭️  SKIPPED     not a Python project (codeless)
Type Checking        ⏭️  SKIPPED     not a Python project (codeless)
Security Scan        ⏭️  SKIPPED     not a Python project (codeless)
Dependency Audit     ⏭️  SKIPPED     not a Python project (codeless)
Doc Completeness     ⏭️  SKIPPED     not a Python project (codeless)
Documentation        ⏭️  SKIPPED     not a Python project (codeless)
Linting              ⏭️  SKIPPED     not a Python project (codeless)
Code Formatting      ⏭️  SKIPPED     not a Python project (codeless)
============================================================

✅ Project Health Check completed successfully!
============================================================
```

This is expected behavior, not an error.

## Example Use Cases

### Academic Research Paper

A research paper project using WSD for structured writing assistance:

```
my-research-paper/
├── .claude/              # WSD agent definitions and commands
├── dev/
│   └── journal/          # Work session logs
├── docs/
│   ├── core/
│   │   └── Action-Plan.md   # Paper sections as phases
│   └── workbench/        # Draft sections, notes
├── paper/
│   ├── abstract.md
│   ├── introduction.md
│   ├── methodology.md
│   └── references.bib
├── pyproject.toml        # Minimal WSD config
└── wsd.py
```

The Action Plan might organize work by paper section:
```markdown
## Phase 1: Literature Review
- [ ] **1.1** - Survey existing approaches
- [ ] **1.2** - Identify research gaps

## Phase 2: Methodology
- [ ] **2.1** - Define experimental design
- [ ] **2.2** - Document data collection process
```

### Business Strategy Document

A strategic planning project:

```
strategy-2025/
├── .claude/
├── dev/journal/
├── docs/
│   ├── core/
│   │   ├── Action-Plan.md
│   │   └── PRD.md            # Strategy overview
│   ├── features/
│   │   ├── market-analysis/
│   │   └── competitive-positioning/
│   └── workbench/
├── deliverables/
│   ├── executive-summary.md
│   └── full-report.md
├── pyproject.toml
└── wsd.py
```

### Technical Documentation Project

A documentation-only repository:

```
product-docs/
├── .claude/
├── dev/journal/
├── docs/
│   ├── core/Action-Plan.md
│   ├── features/
│   │   ├── api-reference/
│   │   ├── getting-started/
│   │   └── tutorials/
│   └── workbench/
├── content/
│   ├── api/
│   ├── guides/
│   └── examples/
├── pyproject.toml
└── wsd.py
```

## Transitioning to a Code Project

If your project evolves to include Python code, transition by:

1. Adding a `[project]` section to `pyproject.toml`:
   ```toml
   [project]
   name = "my-project"
   version = "0.1.0"
   requires-python = ">=3.10"
   ```

2. Updating `check_dirs` to include your source directories:
   ```toml
   [tool.wsd]
   check_dirs = ["src", "tests"]
   ```

3. Installing development dependencies:
   ```bash
   uv add --dev ruff mypy pytest pytest-cov
   ```

WSD automatically detects the change and enables Python-specific quality checks on your next health check run.

See `Python-Project-Guide.md` for complete Python project setup.

## Troubleshooting

### Health Check Shows Python Checks Running

**Symptom:** Python-specific checks run instead of being skipped.

**Cause:** WSD detected your project as a Python project. This happens if:
- `pyproject.toml` has a `[project]` section
- There are `.py` files in directories listed in `check_dirs`

**Solution:** Remove the `[project]` section if you don't need it, or set `check_dirs = []` to prevent scanning.

### "uv not found" Error

**Symptom:** WSD commands fail with "uv not found".

**Solution:** Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Missing pyproject.toml

**Symptom:** WSD commands fail with configuration errors.

**Solution:** Create the minimal configuration:
```toml
[tool.wsd]
check_dirs = []

[tool.uv]
dev-dependencies = []
```

Then run `uv sync` to initialize the environment.

## Next Steps

After setting up WSD for your codeless project:

1. **Customize WORKSCOPE-DEV tags**: Fill in project-specific content in `.claude/commands/`
2. **Set up your Action Plan**: Add phases and tasks to `docs/core/Action-Plan.md`
3. **Start your first session**: Run `/wsd:init` in Claude Code
4. **Explore the workflow**: Review `docs/read-only/` for system documentation

---

*This guide covers codeless project setup. For Python projects, see `Python-Project-Guide.md`. For general installation, see `Integration-Guide.md`.*
