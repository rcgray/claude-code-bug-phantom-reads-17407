---
description: Execute a command repeatedly, fixing issues until it succeeds
argument-hint: <command>
---

# Run a Fix Loop

This command asks the Agent to enter a task loop in which the Agent executes a terminal command, looks at the output, and addresses the issues that arise repeatedly until the command runs as expected.

**Command to execute:** $ARGUMENTS

## Usage

```
/fix-loop <command>
```

Where:
- `<command>` is the operation (sometimes a literal terminal command) to execute in the fix loop.

## Examples

```
/fix-loop uv run pytest
```

```
/fix-loop our automated tests
```

## Description

This command will:

1. Consider the recent conversation with the User that is related to the `<command>` text. The `<command>` could be a literal terminal command (e.g., Python: "uv run ruff check src/ tests/", TypeScript: "npm run lint"), or this could be a general description (e.g., "fix linting errors"). If there is any uncertainty regarding the command, the Agent will query the User for clarification.
2. Run the command and observe the output. If there are questions or decision points, you can halt to ask them.
3. Otherwise, address issues and repeat until the command runs as expected.

## Implementation

The command should:

1. Parse the argument to understand what operation needs to be run in the fix loop.
2. Run the command and observe its output.
3. Address any issues that result (errors, warnings, unexpected output, etc.).
4. Repeat at Step 2 until no issues remain.
