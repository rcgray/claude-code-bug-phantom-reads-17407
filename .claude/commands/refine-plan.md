---
description: Refine Work Plan Document
argument-hint: <path-to-wpd>
---

# Refine Work Plan Document

This command initiates adversarial review of a Work Plan Document (WPD) before it enters the execution pipeline.

## Usage

```
/refine-plan <path-to-wpd>
```

Where:
- `<path-to-wpd>` is the path to the Work Plan Document (ticket, feature spec, or workbench file) to review. This argument is required.

The target Work Plan Document to review:

$ARGUMENTS

## Examples

```
/refine-plan docs/tickets/open/fix-collision-detection.md
```

```
/refine-plan docs/features/content-hashing/Content-Hashing-Overview.md
```

---

## Your Mission

You are about to review a Work Plan Document with the goal of hardening it into a rock-solid plan before implementation begins.

Read the target WPD (specified above) thoroughly. Then investigate deeply - read related specifications, examine existing code, cross-reference with design decisions and other documentation. Search for inconsistencies, gaps, edge cases, and anything that conflicts with other parts of our system.

Your job is to find what's wrong, what's missing, and what could cause implementation to fail. You own this investigation. Be thorough. Be skeptical. Verify your concerns against actual documents and code before reporting them.

When you're ready, share your assessment as a numbered list of findings. We'll discuss them together. Along the way, we might declared numbered "Investigations" that need to be performed to guide our decisions. Some issues we may decide should be broken out into separate tickets, and you may be asked to open them (use the `/open-ticket` command).

When we agree on all the needed changes for the WPD, you'll update the WPD directly.

After updates are complete, remind the user they can run `/refine-plan` again in a fresh session for another pass, repeating until the WPD is solid.
