# Workscope-Dev Integration Guide

**Version:** 1.0.0
**Audience:** Developers integrating WSD into their projects

## Introduction

This guide shows you how to install Workscope-Dev (WSD) into your project and customize it for your needs. WSD provides a structured workflow system for AI-assisted development with Claude Code.

## Prerequisites

- **Git**: Strongly recommended for rollback safety
- **Python 3.10+**: Required for WSD scripts
- **Claude Code**: AI assistant that WSD is designed for

**For TypeScript projects:**
- **Node.js 18+**: Required for TypeScript-specific health checks

**For codeless projects** (documentation, research, etc.):
- No additional prerequisites beyond the basics above
- See `Codeless-Project-Guide.md` for minimal setup

## Installation Command

### Command Syntax

```bash
wsd.py install [OPTIONS] <target-path>
```

**Required Parameter:**
- `<target-path>`: Directory where WSD will be installed
  - Use `.` to install in the current directory
  - If the directory doesn't exist, it will be created
  - If the directory exists, collision detection runs before installation

**Options:**
- `--dry-run`: Preview what would be installed without making changes (updates only)
- `--force`: Force fresh installation even if WSD is already installed
- `--verbose`, `-v`: Show detailed progress during installation

### Basic Usage

**Install into current directory:**
```bash
python /path/to/wsd-source/wsd.py install .
```

**Install into a specific path:**
```bash
python /path/to/wsd-source/wsd.py install /path/to/my-project
```

**Install with verbose output:**
```bash
python /path/to/wsd-source/wsd.py install --verbose .
```

### New Project Installation

```bash
# Create project directory and install WSD
mkdir my-project && cd my-project
python /path/to/wsd-source/wsd.py install .

# Initialize git and commit
git init
git add .
git commit -m "Add Workscope-Dev framework"
```

### Existing Project Installation

```bash
# 1. Commit current work (safety checkpoint)
cd my-existing-project
git add -A && git commit -m "Checkpoint before WSD installation"

# 2. Install WSD
python /path/to/wsd-source/wsd.py install .

# 3. Commit WSD files
git add -A && git commit -m "Add Workscope-Dev framework"
```

## Collision Detection and Resolution

When installing into an existing project, WSD checks for files that would be overwritten. If conflicts are found, installation stops before any files are modified.

### How Collision Detection Works

WSD scans all files it would install and compares them against existing files in your target directory. If any file already exists, installation is aborted with a detailed report.

**Important:** Collision detection happens BEFORE any files are copied. Your existing files are never modified or deleted during this check.

### Collision Error Format

```
Error: Installation aborted due to file collisions.

The following files already exist in the target directory:
  - .gitignore
  - README.md
  - scripts/health_check.py

Resolution Options:
  1. Rename/backup conflicting files and retry installation
  2. Use --force to overwrite existing WSD installation (WARNING: destructive)
  3. Manually merge content after resolving conflicts

No files have been modified. Your existing files are unchanged.
```

### Resolution Strategies

**Strategy 1: Rename and Merge (Recommended)**

This approach preserves your existing content while allowing WSD installation:

```bash
# Rename conflicting files
mv .gitignore .gitignore.original
mv README.md README.md.original

# Install WSD
python /path/to/wsd-source/wsd.py install .

# Merge your original content into WSD files as needed
# For example, add your custom .gitignore rules to WSD's .gitignore
cat .gitignore.original >> .gitignore

# Clean up and commit
rm .gitignore.original README.md.original
git add -A && git commit -m "Add Workscope-Dev framework"
```

**Strategy 2: Delete Conflicting Files**

If your existing files can be replaced entirely:

```bash
# Remove conflicting files (only if you don't need them)
rm .gitignore README.md

# Install WSD
python /path/to/wsd-source/wsd.py install .

git add -A && git commit -m "Add Workscope-Dev framework"
```

**Strategy 3: Force Reinstallation**

Use `--force` only when reinstalling WSD over an existing WSD installation:

```bash
# WARNING: This overwrites existing WSD files
python /path/to/wsd-source/wsd.py install --force .
```

**Caution:** The `--force` flag is designed for reinstalling WSD, not for overwriting unrelated project files. It bypasses collision detection entirely.

### Files That Never Cause Collisions

- **`.wsdkeep` files**: Placeholder files for empty directories are always safe to overwrite
- **Empty directories**: Existing empty directories don't conflict with WSD's directory structure

### Common Collision Scenarios

| Conflicting File | Typical Resolution                                          |
| ---------------- | ----------------------------------------------------------- |
| `.gitignore`     | Merge: append your rules to WSD's gitignore                 |
| `README.md`      | Rename: keep as `README.project.md`, customize WSD's README |
| `LICENSE`        | Choose: keep your license or use WSD's template             |
| `scripts/*.py`   | Rename: move your scripts to avoid conflicts                |

## Integration Scenarios

### Scenario 1: Brand New Project

Starting from scratch with WSD as the foundation.

```bash
# Create and enter project directory
mkdir my-new-app && cd my-new-app

# Install WSD
python /path/to/wsd-source/wsd.py install .

# Initialize version control
git init
git add .
git commit -m "Initialize project with Workscope-Dev"

# Customize WSD for your project
# Edit .claude/commands/wsd/init.md to add project description
# Edit docs/core/Action-Plan.md to define your phases and tasks
```

**Result:** A fully structured project ready for AI-assisted development.

### Scenario 2: Existing Codebase

Adding WSD to a project that already has source code.

```bash
cd my-existing-codebase

# Safety checkpoint
git add -A && git commit -m "Checkpoint before WSD"

# Attempt installation
python /path/to/wsd-source/wsd.py install .

# If collisions occur, resolve them (see Collision Resolution above)
# Then retry installation

# Commit WSD addition
git add -A && git commit -m "Add Workscope-Dev framework"
```

**Result:** WSD directories (`.claude/`, `dev/`, `docs/`, `scripts/`) added alongside your existing code. Your source files remain untouched.

### Scenario 3: Project with Existing Documentation

Adding WSD when you already have a `docs/` folder.

```bash
cd my-documented-project

# Check what's in your docs folder
ls docs/

# Backup your documentation
cp -r docs/ docs-backup/

# Install WSD (may report collisions in docs/)
python /path/to/wsd-source/wsd.py install .

# If collisions in docs/, rename your files first
# WSD creates docs/core/, docs/read-only/, docs/workbench/, etc.
# Your existing docs can coexist or be moved into WSD structure
```

**Result:** WSD's documentation structure integrates with or replaces your existing docs as needed.

### Scenario 4: Monorepo or Multi-Package Project

Installing WSD at the repository root of a monorepo.

```bash
cd my-monorepo
# Contains: packages/frontend/, packages/backend/, packages/shared/

# Install WSD at root
python /path/to/wsd-source/wsd.py install .

# WSD adds its structure at root level:
# .claude/, dev/, docs/, scripts/, wsd.py

# Your packages remain in packages/
# Configure WSD's Action-Plan.md to reference work across packages
```

**Result:** WSD manages the repository-level workflow while your packages remain independent.

### Scenario 5: Reinstalling or Repairing WSD

When you need to reset WSD to a clean state.

```bash
cd my-wsd-project

# Option A: Force reinstall (preserves customizations in tags)
python /path/to/wsd-source/wsd.py install --force .

# Option B: Complete reset (loses all customizations)
rm -rf .claude/ dev/ docs/ scripts/ .wsd wsd.py
python /path/to/wsd-source/wsd.py install .
```

**Result:** Fresh WSD installation. Option A preserves WORKSCOPE-DEV tag content; Option B starts completely fresh.

### Scenario 6: Codeless Project

Setting up WSD for a non-code project (documentation, research, planning).

```bash
# Create project and install WSD
mkdir my-research-project && cd my-research-project
python /path/to/wsd-source/wsd.py install .

# Create minimal pyproject.toml for codeless project
cat > pyproject.toml << 'EOF'
[tool.wsd]
check_dirs = []

[tool.uv]
dev-dependencies = []
EOF

# Initialize and verify
uv sync
./wsd.py health  # Should show all checks as SKIPPED
git init && git add . && git commit -m "Initialize codeless project with WSD"
```

**Result:** WSD's workflow features work normally; Python-specific health checks are skipped.

See `Codeless-Project-Guide.md` for detailed setup instructions and use cases.

## Installation Best Practices

### Before Installation

1. **Commit your work**: Always create a git checkpoint before installing WSD
   ```bash
   git add -A && git commit -m "Checkpoint before WSD installation"
   ```

2. **Review your project structure**: Know which files might conflict with WSD
   ```bash
   ls -la  # Check for .gitignore, README.md, docs/, scripts/
   ```

3. **Use verbose mode for first installation**: See exactly what's being installed
   ```bash
   python /path/to/wsd-source/wsd.py install --verbose .
   ```

### During Installation

1. **Read collision messages carefully**: They tell you exactly which files conflict

2. **Choose the right resolution strategy**: Merge when you have custom content, delete when you don't need the original

3. **Don't use --force casually**: It's for reinstalling WSD, not for bypassing legitimate conflicts

### After Installation

1. **Verify the installation**: Check that key directories exist
   ```bash
   ls -la .claude/ docs/ scripts/
   cat .wsd  # View the manifest
   ```

2. **Run the health check**: Confirm everything is working
   ```bash
   ./wsd.py health
   ```

3. **Customize immediately**: Fill in WORKSCOPE-DEV tags while context is fresh
   ```bash
   # Find all customizable tags
   grep -r "WORKSCOPE-DEV" .claude/ docs/
   ```

4. **Commit the installation**: Create a clean commit point
   ```bash
   git add -A && git commit -m "Add Workscope-Dev framework"
   ```

### Working with Teams

1. **Install once, share via git**: WSD files should be committed and shared with your team

2. **Customize before sharing**: Fill in project-specific tags before team members clone

3. **Document your customizations**: Note any significant changes to WSD defaults in your project README

## Command Flags Reference

### --dry-run

Preview changes without modifying any files. Available for update operations.

```bash
# Preview what an update would change
python /path/to/wsd-source/wsd.py install --dry-run .
```

**Output includes:**
- Files that would be added
- Files that would be updated
- Files that would be deleted
- Files that would be skipped (protected)

**Note:** `--dry-run` is not available for fresh installations because WSD's collision detection already prevents unwanted changes.

### --force

Force a fresh installation even when WSD is already installed.

```bash
# Reinstall WSD (overwrites existing WSD files)
python /path/to/wsd-source/wsd.py install --force .
```

**When to use:**
- Repairing a corrupted WSD installation
- Resetting WSD to default state
- Downgrading to an earlier WSD version

**Warning:** Using `--force` on a non-WSD project will overwrite files without collision detection. Only use this flag when you understand what will be overwritten.

### --verbose, -v

Enable detailed logging during installation.

```bash
# Full verbose output
python /path/to/wsd-source/wsd.py install --verbose .

# Short form
python /path/to/wsd-source/wsd.py install -v .
```

**Output includes:**
- Each file being copied
- Directory creation events
- Permission changes
- Manifest creation details

**Sample verbose output:**
```
[VERBOSE] Verbose mode enabled for installation
[VERBOSE] Starting installation from /source to /target
[VERBOSE] Source directory validated
[VERBOSE] Found 87 files to install
[VERBOSE] Copying: wsd.py
[VERBOSE] Copying: .claude/agents/task-master.md
[VERBOSE] Copying: docs/core/Action-Plan.md
...
[VERBOSE] Setting execute permission: scripts/health_check.py
[VERBOSE] Creating manifest: .wsd
```

### Combining Flags

Flags can be combined for specific use cases:

```bash
# Verbose reinstallation
python /path/to/wsd-source/wsd.py install --force --verbose .

# Verbose update preview
python /path/to/wsd-source/wsd.py install --dry-run -v .
```

## Task Runner Setup

WSD includes a unified task runner (`wsd.py`) that provides consistent commands across Python and TypeScript projects. For convenience, create a shell alias to use the shorter `wsd` command:

**Bash/Zsh** (add to `~/.bashrc` or `~/.zshrc`):
```bash
alias wsd='./wsd.py'
```

**Fish** (add to `~/.config/fish/config.fish`):
```fish
alias wsd './wsd.py'
```

After setting up the alias, you can use commands like `wsd test`, `wsd lint`, and `wsd format` that automatically run the appropriate tools for your project's detected languages. The task runner supports polyglot projects (e.g., a React frontend with a Python backend) and runs the appropriate tools for each detected language.

**Language Detection:**
- **Python**: Detected when `pyproject.toml` exists
- **TypeScript**: Detected when `package.json` exists AND `.ts` files are found in check directories
- **JavaScript**: Detected when `package.json` exists but no `.ts` files are found
- **Codeless**: No language indicators found (workflow features work, quality checks skipped)

Note: TypeScript and JavaScript detection are mutually exclusive for Node.js projects, but a project can contain both Python and TypeScript/JavaScript.

For comprehensive command reference and usage examples, see the Task-Runner-Guide.md in your installation.

**Configuration Note**: Some commands (like `lint`, `format`, `type`, and `security` for Python) require a `[tool.wsd]` section in your `pyproject.toml` to specify which directories to check:

```toml
[tool.wsd]
check_dirs = ["src", "tests"]
```

Other commands (like `test`, `build`, `sync`) work immediately without configuration.

## Customization

After installation, customize WSD by editing content inside `<WORKSCOPE‑DEV>` tags.

### Finding Tags

```bash
# Find all customizable tags
grep -r "WORKSCOPE-DEV" .claude/ docs/
```

### Example Tags to Customize

**Project Introduction** (`.claude/commands/wsd/init.md`):
```markdown
<WORKSCOPE‑DEV wsd-init-project-introduction>
Replace this with your project description, tech stack, and approach
</WORKSCOPE‑DEV>
```

**Project-Specific Rules** (`docs/read-only/Agent-Rules.md`):
```markdown
<WORKSCOPE‑DEV agent-rules-project-specific>
Add your coding standards and conventions
</WORKSCOPE‑DEV>
```

**Execution Workflow** (`.claude/commands/wsd/execute.md`) - optional:
```markdown
<WORKSCOPE‑DEV wsd-execute-workflow>
Add custom workflow steps if needed
</WORKSCOPE‑DEV>
```

### How Tag Customization Works

When you modify content within WORKSCOPE-DEV tags, you're creating project-specific customizations that WSD will preserve automatically during future updates. The tag system works as follows:

The opening tag `<WORKSCOPE‑DEV tag-id>` and closing tag `</WORKSCOPE‑DEV>` act as boundaries around customizable content. Everything between these markers belongs to you. When WSD updates bring new template improvements, the system extracts your content from within each tag, applies the template updates around it, and then restores your content back into place.

For example, if you customize the project introduction tag:

```markdown
<WORKSCOPE‑DEV wsd-init-project-introduction>
We are building a real-time analytics dashboard using React and Python.
Our API follows REST conventions and uses PostgreSQL for persistence.
</WORKSCOPE‑DEV>
```

When you update WSD, even if the surrounding template text changes, your project description remains exactly as you wrote it. The update might change instructions before or after the tag, but your content inside stays untouched.

This means you can confidently customize tagged sections knowing that your work will survive updates. The surrounding template context may improve over time, but your project-specific content persists.

### Tag Syntax Rules

**Tag IDs** follow a specific format:
- Use lowercase letters, numbers, and hyphens only
- Length must be between 3 and 50 characters
- Use kebab-case style (words separated by hyphens)
- Must start and end with a letter or number (not a hyphen)

**Valid tag IDs:** `project-intro`, `custom-rules`, `workflow-steps`
**Invalid tag IDs:** `ProjectIntro` (uppercase), `ab` (too short), `my_rules` (underscore), `-bad-start` (starts with hyphen)

### Customization Guidelines

**DO:**
- Replace content between tags with your project-specific information
- Keep both the opening and closing tag markers intact
- Maintain proper tag syntax (opening tag, content, closing tag on separate lines or inline)

**DON'T:**
- Remove or modify the tag markers themselves
- Change the tag ID (the identifier after `WORKSCOPE-DEV`)
- Nest tags inside other tags (nesting is not supported)
- Leave malformed tags (missing closing tag will break preservation)

**Why this matters:** Malformed tags (missing closing marker, nested tags, or invalid IDs) will cause the preservation system to skip that tag during updates, potentially losing your customizations. Always verify your tags are properly formed after editing.

### Best Practices for Working with Tags

**Customize early, customize once.** The best time to fill in your WORKSCOPE-DEV tags is right after installation, while your project context is fresh. Taking a few minutes to write good project descriptions and rules pays dividends across all future AI sessions.

**Keep content focused and relevant.** Each tag has a specific purpose. The project introduction tag should describe what you're building and how. The project-specific rules tag should contain coding standards and conventions. Resist the urge to add unrelated information.

**Use clear, descriptive language.** AI assistants will read your tag content to understand your project. Write as if explaining to a new team member. Avoid jargon without explanation and be specific about your preferences.

**Test your tags before committing.** After editing a tag, run a quick search to verify syntax:
```bash
grep -B 1 -A 1 "WORKSCOPE-DEV" path/to/edited/file
```
This shows the tag markers and confirms they're properly formed.

**Review tags during updates.** When updating WSD, use `--dry-run` first and then check that your customizations survived. A quick grep after updating confirms everything is in place.

**Don't over-customize.** The default WSD workflow is designed to work well out of the box. Only customize what genuinely needs project-specific content. Adding unnecessary customizations creates more to maintain and more potential for errors.

**Document significant customizations.** If you make substantial changes to workflow tags or add complex project-specific rules, consider noting them in your project's README or documentation so team members understand the customizations.

## Action Plan Setup

Replace the template Action Plan with your project's tasks organized by functional area:

**Edit `docs/core/Action-Plan.md`:**
```markdown
# My Project Action Plan

## Phase 1: Foundation
- [ ] **1.1** - Setup database
  - [ ] **1.1.1** - Design schema
  - [ ] **1.1.2** - Create migrations
- [ ] **1.2** - Implement authentication
  - [ ] **1.2.1** - OAuth integration
  - [ ] **1.2.2** - Session management

## Phase 2: Core Features
- [ ] **2.1** - Build API endpoints
- [ ] **2.2** - Add frontend components
```

This checkboxlist serves as your project's master task list. WSD uses it to organize and track work, and tasks can link to other documentation files for detailed specifications.

**Note:** Certain files are protected by the `no_overwrite` policy in `wsd.json` and are only copied on initial installation. These files (including PRD.md, Action-Plan.md, Design-Decisions.md, LICENSE, README.md, and others) will not be overwritten during WSD updates. Inspect `wsd.json` in your installation for the complete list.

## Git Workflow

**Before installation:**
```bash
git add -A && git commit -m "Checkpoint before WSD"
```

**After installation:**
```bash
git add -A && git commit -m "Add Workscope-Dev framework"
```

**What to track in git:**
- All WSD files (`.claude/`, `docs/`, `scripts/`, etc.)
- The `.wsd` manifest
- Your customizations

**What you can ignore:**
- `dev/diagnostics/` - Temporary analysis files (already in WSD's `.gitignore`)
- Optionally `dev/journal/` - Work session logs (team preference)

The WSD installation includes a `.gitignore` file with sensible defaults.

## Next Steps

After integration:

1. **Run platform setup:** Execute `/wsd:setup` in Claude Code to configure platform-specific tooling. This command detects your project's languages and ensures all necessary configuration is in place.
2. **Customize tags:** Edit the 2-3 primary WORKSCOPE-DEV tags (find them with `grep -r "WORKSCOPE-DEV" .claude/ docs/`).
3. **Update Action Plan:** Add your project's actual phases and tasks to `docs/core/Action-Plan.md` (or run `/wsd:init --custom` and request that your agent build it for you!).
4. **Add design decisions:** Document your project's architectural philosophies in `docs/core/Design-Decisions.md` using the `/add-dd` command as you encounter them.
5. **Start first session:** Run `/wsd:init` in Claude Code to begin your first workscope.
6. **Read the docs:** Explore `docs/read-only/` to understand the workflow system.

For day-to-day usage including the workscope lifecycle, available commands, and agent reference, see `User-Guide.md`.

For updating WSD to newer versions, see `Update-Guide.md`.

---

*This guide covers WSD installation and initial customization. For daily usage, see User-Guide.md. For updates, see Update-Guide.md. For technical details, see the specification documents.*
