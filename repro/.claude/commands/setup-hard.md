---
description: Generate a Workscope ID without full WSD initialization
argument-hint:
---

# Get Workscope ID

This command generates a unique Workscope ID for trial coordination without the full WSD platform initialization overhead. Use this for Phantom Read Experiment trials where minimal context consumption is required.

@docs/specs/operations-manual-standard.md
@docs/specs/operations-manual-exceptions.md
@docs/specs/architecture-deep-dive.md
@docs/specs/troubleshooting-compendium.md

## Usage

```
/setup-hard
```

## Purpose

The Workscope ID serves as the coordination marker for trial artifacts:
- Chat export naming
- Session file organization via `collect_trials.py`
- Trial directory structure in `dev/misc/`

This command provides the ID generation without loading WSD system files, creating Work Journals, or consulting Special Agents.

---

## Workscope ID Generation

Generate a unique Workscope ID based on the current timestamp:

1. Run the `date` command to get the current timestamp
2. Derive the Workscope ID according to the pattern: `YYYYMMDD-HHMMSS`

Report the Workscope ID clearly so it can be recorded for artifact naming.

## Completion Behavior

After generating the ID, display it prominently:

```
Workscope ID: YYYYMMDD-HHMMSS
```
