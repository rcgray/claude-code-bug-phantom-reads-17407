---
description: Configure WSD platform for detected project languages (Python, TypeScript, JavaScript)
---

# WSD Platform Setup

This command ensures the WSD platform is properly configured within a project after installation or update. It detects project platforms, reads the authoritative setup guides, and follows their instructions to ensure WSD tools can function.

## Usage

```
/wsd:setup
```

No flags are required. The command detects platforms automatically and presents a plan for User confirmation before making any changes.

## Examples

```
/wsd:setup
```
(Detects platforms, reads guides, proposes changes, and executes after User approval)

---

## WSD Platform Setup

This command ensures the WSD platform is properly integrated with your project's development tooling. It is idempotent - safe to run multiple times, only making changes where needed.

**Purpose:** After running `wsd.py install` or `wsd.py update`, this command ensures your project has all necessary configuration for WSD tools to function.

**Scope Clarification:** This command ensures WSD platform readiness within EXISTING project tooling. It does NOT set up your project's development infrastructure from scratch. The one exception is Python: since WSD requires Python to function, this command will bootstrap minimal Python tooling if none exists.

**Ownership Principle:** This command is an orchestrator. The setup guides in `dev/wsd/` are the authoritative source of truth for what each platform requires. This command reads those guides and follows their instructions - it does not duplicate or summarize them.

## Phase 1: Platform Detection

Detect what platforms have tooling established in this project by checking for platform-specific configuration files.

### Supported Platforms

Check for the following platforms (this list will expand as WSD adds support for more languages):

| Platform   | Detection Files  | Additional Detection                                               | Notes                                                 |
| ---------- | ---------------- | ------------------------------------------------------------------ | ----------------------------------------------------- |
| Python     | `pyproject.toml` | `[project]` section in pyproject.toml OR `.py` files in check dirs | Special case: Always included (WSD requires Python)   |
| TypeScript | `package.json`   | `.ts` files present in configured directories                      | Detected when package.json exists AND .ts files found |
| JavaScript | `package.json`   | No `.ts` files in configured directories                           | Detected when package.json exists but no .ts files    |

**Language Detection for Node.js Projects:**
WSD distinguishes between TypeScript and JavaScript projects by scanning for `.ts` files in the project's configured check directories. The detection uses `wsd.checkDirs` from `package.json` if configured, falling back to conventional directories (`src`, `lib`, `source`, `tests`, `test`).

Future platforms (not yet supported):
- PHP: `composer.json`
- Rust: `Cargo.toml`
- Ruby: `Gemfile`

### Detection Process

1. Check for each platform's detection files in the project root
2. Record which platforms have existing tooling
3. Always include Python in the list (even if not detected, since WSD requires it)

### Report Detection Results

Present the detection results to the User:

```
## Platform Detection Results

The following platforms were detected based on existing tooling:

| Platform   | Status    | Detection       |
| ---------- | --------- | --------------- |
| Python     | [DETECTED | WILL BOOTSTRAP] | [pyproject.toml found                   | No pyproject.toml - will create minimal setup] |
| TypeScript | [DETECTED | NOT DETECTED]   | [package.json found + .ts files present | No package.json OR no .ts files]               |
| JavaScript | [DETECTED | NOT DETECTED]   | [package.json found + no .ts files      | No package.json OR .ts files present]          |

**Note:** TypeScript and JavaScript are mutually exclusive - a Node.js project will be detected as one or the other based on the presence of .ts files.

**Python is always included because WSD requires Python to function.**

**Platforms to configure:** [List of platforms that will be set up]

Please confirm this list, or specify any adjustments (e.g., "Skip JavaScript"):
```

**HALT HERE** and wait for User confirmation or adjustments before proceeding.

## Phase 2: Read Setup Guides

After User confirms the platform list, read the authoritative setup guides for each confirmed platform.

### Guide Location

All setup guides are located in `dev/wsd/` and follow a consistent naming pattern:
- `[Language]-Project-Guide.md` - Main setup guide with instructions
- Supporting config documentation files as referenced by the guide

### Python Guides

Read:
- `dev/wsd/Python-Project-Guide.md` ( @dev/wsd/Python-Project-Guide.md )
- `dev/wsd/pyproject.toml.md` ( @dev/wsd/pyproject.toml.md )

### TypeScript Guides (if TypeScript detected)

Read:
- `dev/wsd/Node-Project-Guide.md` ( @dev/wsd/Node-Project-Guide.md )
- `dev/wsd/package.json.md` ( @dev/wsd/package.json.md )
- `dev/wsd/tsconfig.json.md` ( @dev/wsd/tsconfig.json.md )
- `dev/wsd/typedoc.json.md` ( @dev/wsd/typedoc.json.md )

### JavaScript Guides (if JavaScript detected)

Read:
- `dev/wsd/Node-Project-Guide.md` ( @dev/wsd/Node-Project-Guide.md ) - Note: This guide covers both TypeScript and JavaScript Node.js projects
- `dev/wsd/package.json.md` ( @dev/wsd/package.json.md )

**Note for JavaScript Projects:** JavaScript projects use the same base configuration as TypeScript projects but skip TypeScript-specific tooling (tsc, TypeDoc). The Node-Project-Guide.md contains sections applicable to both languages.

### Future Platforms

As WSD adds support for more languages, their guides will be added to `dev/wsd/` following the same pattern. This command will read them when those platforms are detected.

**IMPORTANT:** The guides you just read are the SOURCE OF TRUTH for what each platform requires. Do not rely on memorized or hardcoded requirements - use only what the guides specify.

## Phase 3: Analyze Current State

For each confirmed platform, examine the project's current configuration and compare against what the guides specify as required.

### Analysis Process

For each platform:
1. Read the project's configuration files (e.g., `pyproject.toml`, `package.json`)
2. Compare against the requirements documented in the guides you read
3. **Check for documentation generation configuration:**
   - **Python projects**: Verify `pyproject.toml` includes pdoc configuration (see `pyproject.toml.md` guide)
   - **TypeScript projects**: Verify `typedoc.json` exists at project root (see `typedoc.json.md` guide)
   - **JavaScript projects**: Verify JSDoc configuration if applicable (see `package.json.md` guide)
4. Identify what is missing or needs to be added
5. Note what is already correctly configured

**Critical: Documentation Config as Project Protection**

Documentation generation configuration is not optional and is not merely for generating docs. Without these config files, documentation tools use default output directories (typically `docs/`) that **directly conflict with WSD's documentation structure**. If an agent runs these tools without proper configuration, they will delete the entire `docs/` directory, destroying all Action Plans, specifications, tickets, and workbench artifacts. This configuration is a defensive requirement for agent-based workflows, protecting critical project infrastructure from accidental destruction.

### Special Cases

**Python Bootstrap Case:**
If Python is confirmed but `pyproject.toml` does NOT exist, this is a bootstrap scenario. The guide describes how to create a minimal `pyproject.toml` for WSD to function.

**Node.js Check Directories Configuration:**
For TypeScript or JavaScript projects, check if `wsd.checkDirs` is configured in `package.json`. If not configured:

1. Check if the project's `package.json` contains a `wsd` field with `checkDirs`
2. If missing, recommend adding configuration for accurate language detection:

```json
{
  "wsd": {
    "checkDirs": ["src", "tests"]
  }
}
```

3. Adjust the directories list based on the actual project structure (e.g., if the project uses `lib/` instead of `src/`)

**Why this matters:** WSD uses these directories to scan for `.ts` files when distinguishing TypeScript from JavaScript projects. Without this configuration, WSD falls back to conventional directories which may not match the project's actual structure, potentially causing incorrect language detection.

**Tool Config Files:** Though Python project tooling can be controleld via the `[tool.wsd] check_dirs` variable, Node.js projects distribute their tools across config files (e.g., `.eslint.config.js`, `.prettierrc`, `.prettierignore`, `typedoc.json`). In addition to (and in the same spirit of) the `typedoc.json` defensive case mentioned above, you will need to ensure that the tools are limited to the appropriate directories. It is devastating for a rogue agent to run `bunx eslint` and completely mangle all the files in the project because it was not properly constraint. Each tool has its own methods of inclusion and exclusion, but this step is crucially important that you analyze these files (or add them if they don't exist) with proper settings that will protect our files.

**CLAUDE.md:** A properly configured project will have a CLAUDE.md file (created by the `/init` command in Claude Code), which will pick up on the WSD Task Runner commands and add these when executed after the WSD integration. However, you should add a note to CLAUDE.md to prefer using the WSD Task Runner commands (e.g., `wsd lint`, `wsd format`, etc.) where possible, and also include the note that `wsd` is aliased on the user's system to use the `wsd.py` in the CWD of wherever it is launched from.

## Phase 4: Propose Changes

Based on your analysis (comparing current state against guide requirements), create a clear proposal of what changes need to be made.

### Proposal Format

```
## WSD Setup Proposal

**IMPORTANT:** Please commit any uncommitted changes to your version control system before proceeding. This allows easy rollback if any issues are encountered.

### [Platform Name]

**Current State:** [Brief description of what exists]

**Changes Required:**
- [Specific change 1, as specified by the guide]
- [Specific change 2, as specified by the guide]
- ...

**Commands to Execute:**
- [Command 1]
- [Command 2]
- ...

[Repeat for each platform]

---

**Do you approve this setup plan?** You may:
- Approve as-is
- Request modifications to the plan
- Cancel the setup
```

**HALT HERE** and wait for User approval before proceeding to Phase 5.

## Phase 5: Execute Setup

After User approval, execute the proposed changes for each platform.

### Execution Principles

1. **Follow the guides:** Execute only what the guides specify and what the User approved
2. **Be idempotent:** Skip changes that are already in place
3. **Report progress:** Inform the User as each step completes
4. **Handle errors gracefully:** If a step fails, report the error and ask how to proceed

### Python Bootstrap (Special Case)

If bootstrapping Python (no `pyproject.toml` exists):
1. Create a minimal `pyproject.toml` as described in the Python guide
2. Install dependencies using the commands specified in the guide
3. Continue with normal Python setup

### Standard Execution

For each platform:
1. Make configuration file changes as proposed
2. Run dependency installation commands as proposed
3. Verify the changes were applied correctly

## Phase 6: Completion

### Summary Report

Provide a summary of what was done:

```
## WSD Setup Complete

### Changes Made

**[Platform Name]:**
- [Change 1 completed]
- [Change 2 completed]
- Commands run: [list]

[Repeat for each platform]

### Platform Status

| Platform   | Status                  |
| ---------- | ----------------------- |
| Python     | [READY - X changes made | READY - no changes needed]      |
| TypeScript | [READY - X changes made | SKIPPED - not in platform list] |
| JavaScript | [READY - X changes made | SKIPPED - not in platform list] |

**Note:** Only one of TypeScript or JavaScript will be detected per project.

### Suggested Next Steps

Your project is now configured for WSD. Depending on your project's current state:

- If you have source code to check: `./wsd.py lint` or `./wsd.py type`
- If you have tests: `./wsd.py test`
- To see all available commands: `./wsd.py --help`

```

### Completion Message

MANDATORY: Put the following text at the END of your reply, verbatim:
**"WSD PLATFORM SETUP (/wsd:setup) COMPLETE. Your project is now configured for WSD."**

## Error Handling

The command should handle these error conditions:

1. **Missing guide files**: If `dev/wsd/*.md` files are not found, inform User that WSD may not be fully installed
2. **Permission errors**: If unable to modify config files, inform User and suggest manual changes
3. **Dependency installation failures**: Report the specific failure and ask User how to proceed
4. **Platform without tooling (non-Python)**: Report that the platform cannot be set up without existing configuration files
