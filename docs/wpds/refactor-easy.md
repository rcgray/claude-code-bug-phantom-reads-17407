# Rename DEFAULT_BATCH_SIZE to INITIAL_BATCH_SIZE

## Overview

This refactor standardizes the naming convention for the batch size constant in Module Alpha. The current constant `DEFAULT_BATCH_SIZE` should be renamed to `INITIAL_BATCH_SIZE` to better reflect its semantic purpose as the starting batch size before any dynamic adjustments occur during processing.

The term "default" implies a fallback value that can be overridden, while "initial" more accurately describes this value's role as the starting point for batch processing before adaptive sizing takes effect. This naming change improves code clarity and aligns with the naming patterns used elsewhere in the codebase.

## Required Context

To complete this refactor, review the following file:

- `docs/specs/module-alpha.md` - Contains the constant definition and all usage locations

## Tasks

### Phase 1: Implementation

- [ ] **1.1** - Update the constant name from `DEFAULT_BATCH_SIZE` to `INITIAL_BATCH_SIZE` in the Configuration section
- [ ] **1.2** - Update all references to this constant in the Connection Configuration subsection
- [ ] **1.3** - Verify the constant is referenced consistently in the Module Beta Handoff section
- [ ] **1.4** - Update any documentation strings that reference the old constant name
