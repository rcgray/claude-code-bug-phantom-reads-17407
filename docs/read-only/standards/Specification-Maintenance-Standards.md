# Specification Maintenance Standards

**Purpose**: Maintain synchronization between specification documents and code implementation throughout the development lifecycle.

## Fundamental Principle

Specification documents are authoritative sources of truth describing how the application works. When code changes but specifications don't, "specification drift" occurs—documentation misleads developers and users about actual behavior. Agent Rule 3.11 requires specification updates in the same workscope as code changes.

## Specification Drift

Drift manifests in three forms:

**Missing Documentation**: Code implements features not documented in specifications. An agent adds a configuration option but doesn't document it. Users and future developers cannot discover the option exists.

**Dead Documentation**: Specifications describe features not present in code. An agent removes a CLI flag but leaves it documented. Users attempt to use non-existent features.

**Inconsistent Documentation**: Code and specifications both exist but describe different behavior. An agent changes a default value in code but doesn't update the documented default. Users expect incorrect behavior.

All three forms undermine specification trustworthiness and must be prevented through systematic maintenance.

## When Specifications Require Updates

### Configuration Changes

Configuration specifications document available configuration options, their types, defaults, and behavior. Update these specifications when:

- Adding a configuration option with its schema and default value
- Removing a configuration option
- Changing an option's name, type, or default value
- Modifying how an option affects application behavior
- Adding or removing validation rules

**Recognition Patterns:**

In Python projects, watch for changes to default configuration dictionaries, dataclass definitions, or schema validators:
```python
# Changes requiring specification updates
def get_default_config():
    return {
        "cache": {
            "max_size": 1000,  # New option or changed default
            "ttl_seconds": 3600  # New option
        }
    }
```

In TypeScript projects, watch for changes to configuration interfaces, default objects, or validation schemas:
```typescript
// Changes requiring specification updates
interface Config {
  cache: {
    maxSize: number;  // New property or type change
    ttlSeconds: number;  // New property
  }
}

const defaultConfig: Config = {
  cache: {
    maxSize: 1000,  // Changed default
    ttlSeconds: 3600  // New default
  }
};
```

### Environment Variable Changes

Environment variable specifications document variables affecting application behavior, their purposes, and precedence. Update these specifications when:

- Adding code that reads a new environment variable
- Removing code that reads an environment variable
- Changing how an environment variable is interpreted
- Modifying environment variable precedence or fallback logic

**Recognition Patterns:**

In Python projects, watch for `os.environ`, `os.getenv`, or environment management utilities:
```python
# Changes requiring specification updates
cache_dir = os.getenv("APP_CACHE_DIR", "/tmp/cache")  # New variable
api_key = os.environ["API_KEY"]  # New required variable
```

In TypeScript projects, watch for `process.env` accesses or environment parsers:
```typescript
// Changes requiring specification updates
const cacheDir = process.env.APP_CACHE_DIR ?? "/tmp/cache";  // New variable
const apiKey = process.env.API_KEY!;  // New required variable
```

### Command Interface Changes

Command interface specifications document CLI commands, flags, options, or API endpoints. Update these specifications when:

- Adding a command-line flag, API endpoint, or interactive command
- Removing a command-line flag or endpoint
- Changing a flag's name, aliases, type, or behavior
- Modifying command behavior or output format
- Changing API request/response schemas

**Recognition Patterns:**

In CLI applications (Python with argparse/click/typer, Node with commander/yargs):
```python
# Python CLI - changes requiring specification updates
@click.option("--format", type=click.Choice(["json", "yaml"]))  # New flag
@click.option("--cache-dir", help="Cache directory")  # New flag
```

```typescript
// TypeScript CLI - changes requiring specification updates
program
  .option("--format <type>", "output format", "json")  // New flag
  .option("--cache-dir <path>", "cache directory");  // New flag
```

In API applications, watch for new routes, changed endpoints, or modified schemas:
```python
# Flask/FastAPI - changes requiring specification updates
@app.post("/api/users")  # New endpoint
def create_user(user: UserCreate):  # New schema
```

```typescript
// Express/Fastify - changes requiring specification updates
app.post("/api/users", handler);  // New endpoint
interface UserCreate { ... }  // New schema
```

## Common Specification Documents

Recognize these specification patterns across projects:

**Configuration Specifications** document config file options. Common files: `Config-Spec.md`, `Configuration.md`, `Settings-Reference.md`. Updated when configuration schemas, defaults, or loading logic changes.

**Environment Variable Specifications** document environment variables affecting behavior. Common files: `Environment-Variables-Spec.md`, `Environment.md`, `Env-Vars.md`. Updated when code reads new environment variables or changes variable interpretation.

**CLI Command Specifications** document command-line interfaces. Common files: `CLI-Commands-Spec.md`, `CLI-Reference.md`, `Command-Line-Interface.md`. Updated when CLI parsers define new flags or modify command behavior.

**API Specifications** document HTTP endpoints. Common files: `API-Spec.md`, `API-Reference.md`, `Endpoints.md`. Updated when routes change or request/response schemas modify.

Projects may maintain additional specifications for database schemas, event formats, plugin interfaces, or data structures. Apply the same synchronization principles.

## Specification Update Process

### 1. Identify Affected Specifications

Before implementing code changes, determine which specifications will require updates. Ask:

- Am I modifying configuration schema or defaults? → Configuration specification
- Am I adding environment variable reads? → Environment variable specification
- Am I adding or changing CLI flags? → CLI specification
- Am I adding or modifying API endpoints? → API specification

Multiple specifications may require updates for a single feature. A configuration option often has a corresponding CLI flag and environment variable override—all three specifications need updates.

### 2. Implement Code Changes

Complete the workscope tasks. Track:
- New configuration options and their defaults
- New environment variables and their purposes
- New CLI flags or API endpoints and their behaviors
- Removed or renamed options

### 3. Update Specifications

For each affected specification:

**Read the specification** to understand its structure and formatting. Match existing patterns.

**Locate the appropriate section** for your change. Configuration options are typically grouped by category. Environment variables by purpose. CLI flags by command.

**Add, modify, or remove documentation** matching your code changes. Use consistent formatting with existing entries.

**Include concrete examples** showing actual usage. Examples should be executable code snippets or command-line invocations that users can copy.

**Update cross-references** if option names changed. Configuration options referenced from environment variable sections need consistency.



### 4. Verify Synchronization

After updating code and specifications, verify accuracy:

**Manual verification**:
- Review each documented feature against implementation
- Test that examples actually work
- Confirm all new features are documented
- Verify removed features are removed from specifications

**Automated verification** (if project implements drift detection):
- Run the project's specification drift audit tool
- Address any reported missing documentation (code exists, spec doesn't)
- Address any reported dead documentation (spec exists, code doesn't)
- Re-run until verification passes

Some projects implement automated drift detection scripts that parse specifications and code to identify discrepancies. These tools report missing documentation and dead documentation systematically. If available, use them. If not, rely on careful manual review.

## Language-Specific Documentation Patterns

### Python Projects

Configuration options typically use snake_case and are often nested dictionaries:

```markdown
### cache.max_size

**Type**: `int`
**Default**: `1000`

Maximum entries in cache. Oldest entries evicted when limit reached.

**Example**:
```python
config = {
    "cache": {
        "max_size": 500
    }
}
```
```

Environment variables follow uppercase snake_case conventions:
```markdown
### APP_CACHE_DIR

**Type**: String (filesystem path)
**Default**: `/tmp/cache`

Directory for cache files. Must have write permissions.

**Example**:
```bash
export APP_CACHE_DIR=/var/app/cache
```
```

### TypeScript Projects

Configuration options typically use camelCase and are interface-typed:

```markdown
### cache.maxSize

**Type**: `number`
**Default**: `1000`

Maximum entries in cache. Oldest entries evicted when limit reached.

**Example**:
```typescript
const config = {
  cache: {
    maxSize: 500
  }
};
```
```

Environment variables follow the same uppercase patterns as Python:
```markdown
### APP_CACHE_DIR

**Type**: String (filesystem path)
**Default**: `/tmp/cache`

Directory for cache files. Must have write permissions.

**Example**:
```bash
export APP_CACHE_DIR=/var/app/cache
```
```

Use language-appropriate naming conventions in examples while maintaining universal documentation structure.

## Integration with Development Workflow

### During Planning

When assigned a workscope, identify specification update requirements:
- Review tasks for configuration, environment, or interface changes
- Note which specifications need updates
- Include specification updates in execution plan

### During Execution

Implement code first to understand exact behavior, then update specifications immediately. Maintain synchronization as you work rather than batch updates at the end.

### Before Completion

Verify all specifications are synchronized:
- Check that every code change has corresponding documentation
- Run drift detection if available
- Document specification updates in Work Journal

Workscopes involving code changes are incomplete until specifications are updated. Documentation-Steward agents may review specification synchronization during quality assurance.

## Definition of Done

A workscope with code changes is complete only when:

1. Code changes are implemented and tested
2. All affected specifications are updated
3. Specifications accurately describe implementation
4. Drift verification passes (manual or automated)
5. Work Journal documents specification changes

Attempting to complete a workscope without specification updates violates Agent Rule 3.11 and will result in workscope rejection.

## Common Pitfalls

### Forgetting Specifications Exist

Agents implement features but forget specification documents need updates.

**Solution**: Review specification requirements during workscope planning. Include specification tasks in execution plan before beginning implementation.

### Partial Updates

Agents update one specification but miss related specifications. Adding a configuration option controlled by a CLI flag requires updating both configuration and CLI specifications.

**Solution**: Map features to all affected specifications. Configuration options often have CLI flag overrides and environment variable overrides. Update all three.

### Migration Notes in Specifications

**Solution**: Write specifications as if features always worked the current way. No migration notes, no old behavior references. For pre-release projects, the new design is the only design.

### Drift After Updates

Specifications updated but drift detection still reports issues.

**Solution**: Verify exact names match between spec and code. Check for typos. Ensure code actually uses documented features. Confirm specification formatting matches project patterns.

### Mismatched Structure

Specifications organized differently from code makes alignment difficult.

**Solution**: Mirror code organization in specifications where practical. Group related configuration options as they appear in code. Cross-reference between specifications when features span multiple specs.

## Examples

### Example: Adding Configuration Option

**Task**: Add automatic cache cleanup option.

**Code (Python)**:
```python
def get_default_config():
    return {
        "cache": {
            "max_size": 1000,
            "auto_clean": True  # NEW
        }
    }

# In cache implementation
if config["cache"]["auto_clean"]:
    self._clean_expired()
```

**Code (TypeScript)**:
```typescript
const defaultConfig = {
  cache: {
    maxSize: 1000,
    autoClean: true  // NEW
  }
};

// In cache implementation
if (config.cache.autoClean) {
  this.cleanExpired();
}
```

**Specification Update**:
```markdown
### cache.auto_clean / cache.autoClean

**Type**: Boolean
**Default**: `true`

Enable automatic cleanup of expired cache entries. When enabled, cache removes expired entries during read operations. When disabled, expired entries remain until manual cleanup.

**Example**:
```python
config = {"cache": {"auto_clean": False}}
```

```typescript
const config = {cache: {autoClean: false}};
```
```

### Example: Adding Environment Variable

**Task**: Allow cache directory override via environment.

**Code (Python)**:
```python
cache_dir = os.getenv("APP_CACHE_DIR", "/tmp/cache")
```

**Code (TypeScript)**:
```typescript
const cacheDir = process.env.APP_CACHE_DIR ?? "/tmp/cache";
```

**Specification Update**:
```markdown
### APP_CACHE_DIR

**Type**: String (filesystem path)
**Default**: `/tmp/cache`

Override cache directory location. Must be writable directory. Application creates directory if it doesn't exist.

**Example**:
```bash
export APP_CACHE_DIR=/var/app/cache
```

**Precedence**: Overrides cache directory from configuration files.
```

### Example: Removing Feature

**Task**: Remove deprecated legacy mode flag.

**Code Changes**: Delete flag from parser, remove checks from code.

**Specification Update**: Remove entire section documenting the flag.

**Verification**: Confirm no code references remain. Confirm specification no longer mentions removed feature. Run drift detection to verify no dead documentation.

## Related Standards

- Agent Rule 3.11 mandates specification updates with code changes
- Coding Standards require documentation for all public interfaces
- Test standards require specification accuracy verification

---

**Key Insight**: Specifications are sources of truth. Code implements what specifications describe. When code changes, specifications must change. Drift undermines trust in documentation and leads to user confusion, developer errors, and wasted time debugging discrepancies. Maintain synchronization systematically with every workscope.
