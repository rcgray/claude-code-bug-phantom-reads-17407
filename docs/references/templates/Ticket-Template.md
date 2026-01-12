# New Ticket: Refactor ProjectManager to Follow Manager Pattern

**Date Reported:** 2025-01-27
**Status**: Open
**Prerequisites**: This ticket should be addressed AFTER `remove-concat-md-from-typedoc-script.md` is completed, since that ticket will eliminate the `npx concat-md` invocation entirely.

## Problem Description

Our current `projectManager.ts` implementation violates industry best practices for the Manager pattern as documented in `docs/core/Technical-Spec.md`. The current implementation exhibits characteristics of a service doing repository work rather than a proper manager that maintains entity state and lifecycle.

## User Journey & Integration
**Entry Point:** How does the user trigger this feature?
<!-- e.g., "User runs 'toki --init' command" -->

**Trigger Conditions:** What causes this code to execute?
<!-- e.g., "When .tokirc file is missing from all search paths" -->

**Integration Points:** Where in existing code should this connect?
<!-- e.g., "In ConfigManager.load_config_file() when no config found" -->

**Success Indicators:** How does the user know it worked?
<!-- e.g., "New .tokirc file appears with message 'Created default configuration'" -->

**Current Issues:**

1. **Stateless Design**: The projectManager doesn't maintain any in-memory tracking of current project state, requiring repeated file system access and re-derivation of project information.

2. **Mixed Responsibilities**: The module handles both system-wide projects.json management AND individual project.json files, blurring the lines between system-level and project-level concerns.

3. **Missing Entity Management**: There's no concept of "current project" or project lifecycle management - each operation is isolated and stateless.

4. **Repository Pattern Misuse**: The module directly handles file I/O operations instead of focusing on entity management and delegating persistence to internal repository methods.

5. **Event System Gap**: No event emission when project state changes, requiring manual event handling in consuming code.

6. **Testing Complexity**: State transitions can't be easily tested because there's no state to transition.

## Suspected Cause

This implementation emerged from iterative development where the initial focus was on getting basic project file operations working. The module was created as a collection of utility functions rather than being designed as a proper Manager class following established software engineering patterns.

The current approach treats projects as data to be manipulated rather than entities to be managed, which doesn't align with the intended architecture where Scout maintains awareness of the current project context and provides event-driven updates to the UI and external adapters.

## Investigation & Analysis

**Current State Analysis:**

The existing `projectManager.ts` exports functions like:
- `addProject()`: Manages system projects.json entries
- `updateProjectLastOpened()`: Updates timestamps in projects.json
- `getRecentProjects()`: Reads and filters projects.json data
- `loadProjectState()`: Loads individual project.json files
- `extractProjectInfo()`: Converts ProjectJson to ProjectInfo

These functions work in isolation and don't maintain any shared state or context. Each caller must manage their own understanding of what the "current project" is, leading to potential inconsistencies.

**Industry Standards Reference:**

According to `docs/core/Technical-Spec.md` section "Code Architecture Patterns":

**Manager Pattern should be used when:**
- Managing the current state of entities (e.g., active project, open sessions)
- Tracking entity lifecycle and relationships
- Acting as a single source of truth for entity state
- Providing factory methods for entity creation

**Manager Characteristics:**
- **Stateful**: Maintains current state and entity references in memory
- **Entity-Focused**: Manages the lifecycle of a specific type of domain object
- **Registry/Factory**: Often acts as both a factory and registry for managed entities
- **Single Domain**: Responsible for one primary entity type or collection

## Proposed Solution

Transform `projectManager.ts` into a true **Manager** class that follows industry standards while maintaining all existing functionality and improving the overall architecture.

### Implementation Plan

#### Phase 1: Add State Management (High Priority)

Convert to singleton class with state management:

```typescript
class ProjectManager extends EventEmitter {
  private static instance: ProjectManager;
  private currentProject: ProjectInfo | null = null;
  private currentProjectState: ProjectJson | null = null;
  private loadedProjects: Map<string, ProjectInfo> = new Map();

  public static getInstance(): ProjectManager {
    if (!ProjectManager.instance) {
      ProjectManager.instance = new ProjectManager();
    }
    return ProjectManager.instance;
  }

  // State management methods
  getCurrentProject(): ProjectInfo | null
  getCurrentProjectState(): ProjectJson | null
  isProjectLoaded(projectPath: string): boolean
}
```

#### Phase 2: Event System Integration

Add comprehensive event emission:
```typescript
private emitProjectStateChanged(project: ProjectInfo | null): void {
  this.emit('projectStateChanged', project);

  // Also emit CRI event for external adapters
  emitCRIEvent('project.stateChanged', { project });
}

// Events that ProjectManager will emit:
// - 'projectStateChanged': (project: ProjectInfo | null) => void
// - 'projectAdded': (project: ProjectInfo) => void
// - 'projectRemoved': (projectPath: string) => void
```

#### Phase 3: Update Dependencies

**Update `electron/main.ts`:**
```typescript
const projectManager = ProjectManager.getInstance();

async function openProject(projectPath: string) {
  try {
    const projectInfo = await projectManager.openProject(projectPath);
    // Event emission is handled internally by ProjectManager
    log.info(`[MainProcess] Successfully opened project: ${projectPath}`);
  } catch (error) {
    log.error(`[MainProcess] Failed to open project ${projectPath}:`, error);
  }
}
```

**Update CRI Handlers in `electron/src/cri/project-handlers.ts`:**
```typescript
// Level 2: CRI endpoint handler for project.open
case 'project.open': {
  const projectManager = ProjectManager.getInstance();
  const projectInfo = await projectManager.openProject(projectPathToOpen);

  return successResponse<ProjectOperationResult>(requestId, {
    project: projectInfo,
    initialState: { status: 'ready', details: 'Project opened successfully.' }
  });
}

// Level 2: CRI endpoint handler for project.getCurrent
case 'project.getCurrent': {
  const projectManager = ProjectManager.getInstance();
  const currentProject = projectManager.getCurrentProject();

  return successResponse<{ project: ProjectInfo | null }>(requestId, {
    project: currentProject
  });
}
```

## Testing Requirements

### Unit Tests
- Test the core functionality in isolation
- Test edge cases and error conditions

### Integration Tests
- Test that the feature is reachable through normal user flow
- Test interaction with existing features

## Definition of Done
- Core functionality implemented
- Unit tests passing
- **Integration point connected** (feature is reachable)
- Documentation updated (if needed)
- No regressions in existing functionality

## Related Files

**Primary Implementation:**
- `electron/src/data-management/projectManager.ts` - Main refactoring target
- `electron/main.ts` - openProject function updates
- `electron/src/cri/project-handlers.ts` - CRI handler updates

**Testing:**
- `tests/unit/main/data-management/projectManager.spec.ts` - Test updates required

**Documentation:**
- `docs/core/Technical-Spec.md` - Architecture patterns reference
- `docs/core/Data-Management.md` - Data management context

**Related Tickets:**
- `docs/tickets/open/consolidate-projectinfo-instantiation-and-loading.md` - Originating ticket that identified need for refactoring

## Developer Notes

This refactoring emerged from the completion of the ProjectInfo consolidation work in the above-mentioned ticket. While implementing centralized project loading functions, it became clear that the current projectManager implementation doesn't follow industry best practices for the Manager pattern.

The refactoring maintains all existing functionality while providing a foundation for future enhancements like multi-project support, project caching, and more sophisticated project lifecycle management.

## Revision History

**2025-12-09**: Updated ticket with current state
- Warning count increased from 640 to 968
- Updated line numbers (code has shifted): linting check now at lines 715-742
- **GOOD NEWS**: Security scan check (lines 580-610) has already been fixed and can serve as reference implementation
- Phase 1.2 marked complete (security scan already fixed)
- Scope reduced: only linting check in JS needs fixing, plus Python audit

## In-Flight Failures (IFF)


## Implementation Plan

<!--
  The ticket always ends with a checkboxlist containing an implementation plan

  WARNING: NEVER START WITH PHASE 0
  ❌ WRONG - Phase 0: Core Implementation
  ✅ RIGHT - Phase 1: Core Implementation

  Phase 0 is ONLY for emergencies discovered DURING work, not planned work!
  If you're creating a new ticket, you CANNOT know what emergencies will arise.

  Do not include tasks that would cause the agent to violate a Rule in Agent-Rules.md
  Do not EVER list git commands (e.g. `git commit`) as a work item (violates Rule 2.2)
  Do not include ticket management ("close this ticket") as a work item
  -->

### Phase 1: Core Functionality
- [ ] **1.1** - Convert to singleton class with state management
- [ ] **1.2** - Refactor openProject and closeProject operations
- [ ] **1.3** - Add private setCurrentProject method with state tracking

### Phase 2: Event System
- [ ] **2.1** - Add EventEmitter inheritance
- [ ] **2.2** - Implement event emission for state changes
  - [ ] **2.2.1** - Audit existing base class for edge cases
  - [ ] **2.2.2** - Implement core functionality
- [ ] **2.3** - Connect to existing CRI event system

### Phase 3: Integration
- [ ] **3.1** - Update electron/main.ts to use manager instance
- [ ] **3.2** - Update CRI handlers in project-handlers.ts
- [ ] **3.3** - Remove manual event emission from callers

### Phase 4: Cleanup and Testing
- [ ] **4.1** - Convert public methods to use internal repository methods
- [ ] **4.2** - Update test suite for singleton pattern
- [ ] **4.3** - Add tests for state management and event emission
- [ ] **4.4** - Verify backward compatibility wrappers work correctly

