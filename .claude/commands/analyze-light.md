---
description: Analyze Work Plan Document (Light Context)
argument-hint: <path-to-wpd>
---

# Analyze Work Plan Document (Light Context)

This command initiates adversarial review of a Work Plan Document with light context preloading.

@docs/specs/operations-manual-standard.md
@docs/specs/operations-manual-exceptions.md

## Usage

```
/analyze-light <path-to-wpd>
```

Where:
- `<path-to-wpd>` is the path to the Work Plan Document (ticket, feature spec, or workbench file) to review. This argument is required.

The target Work Plan Document to review:

$ARGUMENTS

## Examples

```
/analyze-light docs/wpds/pipeline-refactor.md
```

```
/analyze-light docs/tickets/open/fix-cache-invalidation.md
```

---

## Your Mission

You are about to review a Work Plan Document with the goal of hardening it into a rock-solid plan before implementation begins.

Read the target WPD (specified above) thoroughly. Then investigate deeply - read related specifications, examine existing code, cross-reference with design decisions and other documentation. Search for inconsistencies, gaps, edge cases, and anything that conflicts with other parts of our system.

### Suggested Documentation

For WPDs targeting the Data Pipeline System, these specifications provide essential context:

- `docs/specs/data-pipeline-overview.md` - System architecture and module relationships
- `docs/specs/module-alpha.md` - Ingestion module specifications
- `docs/specs/module-beta.md` - Transformation module specifications
- `docs/specs/module-gamma.md` - Output module specifications
- `docs/specs/integration-layer.md` - Cross-module protocols and handoffs
- `docs/specs/compliance-requirements.md` - Regulatory and audit requirements

Cross-reference the proposal against these specifications where relevant. Verify that proposed changes are feasible given the existing architecture and constraints.

### Your Task

Your job is to find what's wrong, what's missing, and what could cause implementation to fail. You own this investigation. Be thorough. Be skeptical. Verify your concerns against actual documents and code before reporting them.

When you're ready, share your assessment as a numbered list of findings. We'll discuss them together. Along the way, we might declare numbered "Investigations" that need to be performed to guide our decisions. Some issues we may decide should be broken out into separate tickets, and you may be asked to open them (use the `/open-ticket` command).

When we agree on all the needed changes for the WPD, you'll update the WPD directly.

After updates are complete, remind the user they can run `/analyze-light` again in a fresh session for another pass, repeating until the WPD is solid.
