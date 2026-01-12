# Testing Configuration and Environment Variables: Standards (TypeScript)

## Overview

This document establishes mandatory standards for testing **both configuration variables and environment variables** in TypeScript projects. These standards prevent the critical failure mode where options are defined, documented, and "tested" without actually verifying they work.

**The Core Failure Mode**: Configuration options can be declared ✓, implementation mechanisms can exist ✓, tests can pass ✓, **but the config values are never actually read and used** ✗. This creates a silent failure where documented features don't work, eroding user trust.

### Scope: Two Types of Variables

This standard applies to:

1. **Configuration Variables** (JSON/YAML/TOML config files)
   - Defined in: `docs/core/Config-Spec.md`
   - Examples: `cache.maxSize`, `defaults.provider`, `security.trustRemoteCode`
   - Location: `~/.config/myapp/config.json` (or platform-specific)
   - Format: JSON, YAML, or TOML structures

2. **Environment Variables** (`.env` files or shell)
   - Defined in: `docs/core/Environment-Variables-Spec.md`
   - Examples: `ANTHROPIC_API_KEY`, `CONFIG_HOME`, `NODE_ENV`
   - Location: `.env` files, shell environment, or system environment
   - Format: `KEY=value` pairs

**When adding or modifying either type**, you must follow the testing standards in this document.

### Core Principle

**Testing the mechanism ≠ Testing the feature**

When the feature is "configuration controls behavior X," you must test that configuration actually controls behavior X, not just that behavior X works when manually configured.

## Why Configuration Testing Matters

### The Failure Mode

A test that verifies a mechanism works is not the same as a test that verifies configuration controls that mechanism.

**Example scenario**:
- `cache.maxSize` configuration option exists in config schema
- `TokenizerCache` class has `maxSizeBytes` parameter
- Test exists: `new TokenizerCache({ maxSizeBytes: 1024 }); verifyEviction()`
- Test passes ✓
- **But**: Config value is never read, hardcoded 100 MB always used
- **Result**: Users setting `maxSize: 50` silently get 100 MB

**The problem**: Test verified LRU eviction mechanism works (by directly passing size), but never verified that configuration controls the size.

### Problems Caused by Inadequate Config Testing

1. **Silent failures**: Config options silently ignored, no errors or warnings
2. **False confidence**: "All tests pass" doesn't mean features work
3. **User confusion**: Documented features don't work as described
4. **Maintenance burden**: Unused config options clutter codebase
5. **Trust erosion**: Can't trust that documented config actually does anything

### Benefits of Proper Config Testing

1. **Verification**: Config options proven to work, not assumed
2. **Early detection**: Disconnections caught before reaching users
3. **Documentation accuracy**: Config docs match actual behavior
4. **Maintainability**: Unused config detected automatically
5. **Confidence**: Green tests mean features actually work

## Alignment with Specification Documents

### The Three-Way Contract

Every configurable feature involves a three-way contract:

1. **Specification** (`docs/core/Config-Spec.md` or `docs/core/Environment-Variables-Spec.md`)
   - Documents what options exist
   - Describes expected behavior
   - Defines default values
   - User-facing documentation

2. **Implementation** (`ConfigManager.ts`, component code)
   - Config schema (e.g., Zod schema) defines structure
   - Components read and use config values
   - Factories create components with config

3. **Tests** (this document's focus)
   - Verify spec ↔ implementation alignment
   - Prove config actually controls behavior
   - Document through executable contracts

**All three must stay synchronized**. When you add/modify/remove a variable:

- ✅ Update specification document (`docs/core/Config-Spec.md` or `docs/core/Environment-Variables-Spec.md`)
- ✅ Update implementation (`ConfigManager.ts`, component, Zod schema)
- ✅ Update tests (integration test proving connection)
- ✅ Update examples (`config.example.json` or `.env.example`)

**This document focuses on #3 (tests)**, ensuring they properly verify the contract between specs and implementation.

## Standard 1: Two Types of Tests Required

### Mandatory Practice

**Every configurable feature requires BOTH mechanism tests AND integration tests.**

### Type 1: Mechanism Tests (Unit Tests)

**Purpose**: Verify the underlying component works correctly

**Example** (cache size limiting):
```typescript
describe('TokenizerCache eviction mechanism', () => {
    it('should evict oldest entries when size limit reached', () => {
        const cache = new TokenizerCache({ maxSizeBytes: 1024 });

        // Fill cache beyond limit
        for (let i = 0; i < 10; i++) {
            cache.save(`file_${i}`, largeData);
        }

        // Assert oldest entries evicted
        expect(cache.contains('file_0')).toBe(false);  // Evicted
        expect(cache.contains('file_9')).toBe(true);   // Retained
    });
});
```

**Characteristics**:
- Direct instantiation with specific parameters
- Isolated from configuration system
- Fast, focused, repeatable
- Tests "does the mechanism work?"

**✅ Necessary but NOT sufficient**

### Type 2: Integration Tests (Config Contract Tests)

**Purpose**: Verify configuration/environment variables actually control behavior

**Example** (cache size limiting):
```typescript
describe('Config contract: cache.maxSize', () => {
    it('should respect cache.maxSize from config file', async () => {
        // CONTRACT: cache.maxSize from config.json must control cache size
        const tempDir = mkdtempSync(join(tmpdir(), 'config-test-'));
        const configPath = join(tempDir, 'config.json');

        // Create config file with specific value
        await fs.writeFile(configPath, JSON.stringify({
            cache: {
                maxSize: 50  // MB
            }
        }));

        // Load through normal configuration path
        process.env = { CONFIG_PATH: configPath };
        const cache = await createCache();  // Factory function, not direct instantiation

        // Verify config value is actually used
        expect(cache.maxSizeBytes).toBe(50 * 1024 * 1024);

        rmSync(tempDir, { recursive: true, force: true });
    });
});
```

**Characteristics**:
- Loads real configuration files
- Uses factory functions, not direct instantiation
- Tests "does the config option work?"
- Should test multiple config values

**✅ Required for all configuration features**

### The Critical Distinction

**Mechanism test**: "Does component X work when I pass parameter Y?"
**Config test**: "Does config option control parameter Y in component X?"

You need both. Mechanism test alone creates false confidence.

## Standard 2: Mandatory Requirements for Configuration Variables

### Applies To

All configuration options in config files as defined in `docs/core/Config-Spec.md`.

**Common TypeScript config patterns:**
- JSON: `config.json`, `package.json` (config section)
- YAML: `config.yml`, `.config.yaml`
- TOML: `.config.toml`, `config.toml`
- TypeScript: `config.ts` (exported objects)

### When Adding a Configuration Option

Every configuration option added to config schema (e.g., Zod schema) and documented in `docs/core/Config-Spec.md` MUST have:

1. **At least one integration test** that:
   - Creates a config file (or sets environment variable)
   - Loads config through ConfigManager
   - Creates component through factory/normal path
   - Asserts config value affects behavior
   - Tests minimum 2-3 different values

2. **Test description**: Use clear "Contract:" prefix for discoverability

3. **Factory usage**: Test must use `createComponent()` / factory, NOT `new Component()`

4. **No mocking ConfigManager**: Integration tests must load real config

5. **Clear contract statement**: Test description must state what contract is verified

### Template for Config Contract Tests

```typescript
describe('Config contract: feature.option', () => {
    let tempDir: string;
    let configPath: string;

    beforeEach(() => {
        tempDir = mkdtempSync(join(tmpdir(), 'config-test-'));
        configPath = join(tempDir, 'config.json');
    });

    afterEach(() => {
        rmSync(tempDir, { recursive: true, force: true });
    });

    it('should respect feature.option from config file', async () => {
        // CONTRACT: config.feature.option must control feature behavior
        // Verifies that setting feature.option=value in config file results
        // in component using that value correctly

        // 1. Create config file
        await fs.writeFile(configPath, JSON.stringify({
            feature: {
                option: 'value1'
            }
        }));

        // 2. Load config through normal path (no mocking)
        process.env = { CONFIG_PATH: configPath };
        const component = await createComponent();  // Use factory, not new Component()

        // 3. Verify config value controls behavior
        expect(component.setting).toBe('expectedValue1');

        // 4. Test with different value
        await fs.writeFile(configPath, JSON.stringify({
            feature: {
                option: 'value2'
            }
        }));

        process.env = { CONFIG_PATH: configPath };
        const component2 = await createComponent();
        expect(component2.setting).toBe('expectedValue2');
    });
});
```

### Using Zod for Config Validation

When using Zod for config schema validation:

```typescript
import { z } from 'zod';

// Schema definition
const ConfigSchema = z.object({
    cache: z.object({
        maxSize: z.number().default(100),
        expirationDays: z.number().default(30)
    }),
    network: z.object({
        timeout: z.number().default(30000),
        retries: z.number().default(3)
    })
});

type Config = z.infer<typeof ConfigSchema>;

// Integration test
describe('Config contract: cache.maxSize', () => {
    it('should parse and use cache.maxSize from config', async () => {
        const configData = {
            cache: {
                maxSize: 50
            }
        };

        // Parse through Zod schema
        const config = ConfigSchema.parse(configData);

        // Create component with parsed config
        const cache = createCacheFromConfig(config);

        expect(cache.maxSizeBytes).toBe(50 * 1024 * 1024);
    });

    it('should use default when cache.maxSize not provided', () => {
        const configData = {};
        const config = ConfigSchema.parse(configData);
        const cache = createCacheFromConfig(config);

        expect(cache.maxSizeBytes).toBe(100 * 1024 * 1024); // Default
    });
});
```

## Standard 3: Mandatory Requirements for Environment Variables

### Applies To

All environment variables as defined in `docs/core/Environment-Variables-Spec.md`:

**Common categories:**
- **API Keys**: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.
- **Directory Overrides**: `CONFIG_HOME`, `DATA_HOME`, `CACHE_HOME`
- **Configuration**: `CONFIG_PATH`, `NODE_ENV`
- **Feature Flags**: `ENABLE_FEATURE_X`, `DEBUG_MODE`
- **External Tool Integration**: `HF_HOME`, `TRANSFORMERS_CACHE`

### When Adding an Environment Variable

Every environment variable added to the codebase and documented in `docs/core/Environment-Variables-Spec.md` MUST have:

1. **Test with variable set**:
```typescript
describe('FEATURE_FLAG environment variable', () => {
    const originalEnv = process.env;

    afterEach(() => {
        process.env = originalEnv;
    });

    it('should enable feature when FEATURE_FLAG is true', () => {
        process.env = { FEATURE_FLAG: 'true' };
        const result = getFeatureStatus();
        expect(result).toBe(true);
    });
});
```

2. **Test with variable unset** (default behavior):
```typescript
it('should default to disabled when FEATURE_FLAG not set', () => {
    process.env = {}; // Clear environment
    const result = getFeatureStatus();
    expect(result).toBe(false);  // Default behavior
});
```

3. **Test precedence** (if multiple sources):
```typescript
it('should respect env var over config file', async () => {
    // Create config file
    const configPath = join(tempDir, 'config.json');
    await fs.writeFile(configPath, JSON.stringify({
        feature: { value: 'from_config' }
    }));

    // Set environment variable
    process.env = {
        CONFIG_PATH: configPath,
        FEATURE_VALUE: 'from_env'
    };

    const result = await getFeatureValue();
    expect(result).toBe('from_env');  // Env wins
});
```

### Environment Variable Test Requirements

- **Always control** `process.env` explicitly in tests
- **Always test** both set and unset states
- **Document precedence**: CLI args > Env vars > Config file > Defaults
- **Test multiple values**: Not just "works", but "uses correct value"
- **Test type conversion**: Verify strings parse to expected types

### Type Conversion Testing

```typescript
describe('Environment variable type conversion', () => {
    it('should parse numeric env var correctly', () => {
        process.env = { TIMEOUT_MS: '5000' };
        const timeout = getTimeout();
        expect(timeout).toBe(5000);
        expect(typeof timeout).toBe('number');
    });

    it('should parse boolean env var correctly', () => {
        process.env = { ENABLE_CACHE: 'true' };
        expect(isCacheEnabled()).toBe(true);

        process.env = { ENABLE_CACHE: 'false' };
        expect(isCacheEnabled()).toBe(false);

        process.env = { ENABLE_CACHE: '1' };
        expect(isCacheEnabled()).toBe(true);

        process.env = { ENABLE_CACHE: '0' };
        expect(isCacheEnabled()).toBe(false);
    });

    it('should parse JSON env var correctly', () => {
        process.env = { CONFIG_JSON: '{"key":"value"}' };
        const config = getConfigFromEnv();
        expect(config).toEqual({ key: 'value' });
    });
});
```

## Standard 4: Anti-Patterns to Avoid

### ❌ Anti-Pattern 1: Testing Only the Mechanism

**Wrong**:
```typescript
describe('Cache size limiting', () => {
    it('should evict when full', () => {
        const cache = new TokenizerCache({ maxSizeBytes: 1024 });
        // Test eviction works...
    });
});
```

**Why wrong**: Never verifies config controls `maxSizeBytes`

**Right**: Have both mechanism test AND config integration test

---

### ❌ Anti-Pattern 2: Mocking Config in Integration Tests

**Wrong**:
```typescript
describe('Config integration', () => {
    it('should use config max size', async () => {
        vi.spyOn(ConfigManager, 'load').mockResolvedValue({
            cache: { maxSize: 50 }
        });
        // ... test ...
    });
});
```

**Why wrong**: Mocking the thing you're trying to test

**Right**: Create actual config file, load through real ConfigManager

---

### ❌ Anti-Pattern 3: Testing Default Only

**Wrong**:
```typescript
describe('Network timeout', () => {
    it('should use default timeout', () => {
        const timeout = getTimeout();
        expect(timeout).toBe(30000);
    });
});
```

**Why wrong**: Only tests default, doesn't verify config override works

**Right**: Test both default AND config override

```typescript
describe('Network timeout configuration', () => {
    it('should use default timeout when not configured', () => {
        process.env = {};
        const timeout = getTimeout();
        expect(timeout).toBe(30000);
    });

    it('should respect TIMEOUT_MS environment variable', () => {
        process.env = { TIMEOUT_MS: '5000' };
        const timeout = getTimeout();
        expect(timeout).toBe(5000);
    });

    it('should respect timeout from config file', async () => {
        const config = { network: { timeout: 10000 } };
        const timeout = getTimeoutFromConfig(config);
        expect(timeout).toBe(10000);
    });
});
```

---

### ❌ Anti-Pattern 4: Direct Instantiation in Config Tests

**Wrong**:
```typescript
describe('Config integration', () => {
    it('should use config value', async () => {
        const config = await loadConfig();
        const cache = new TokenizerCache({
            maxSizeBytes: config.cache.maxSize * 1024 * 1024
        });
        // ...
    });
});
```

**Why wrong**: Manually wiring config to component - doesn't test factory

**Right**: Use factory function that does the wiring

```typescript
describe('Config integration', () => {
    it('should use config value', async () => {
        const cache = await createCache();  // Factory handles config
        expect(cache.maxSizeBytes).toBe(expectedFromConfig);
    });
});
```

---

### ❌ Anti-Pattern 5: Not Cleaning Up Environment

**Wrong**:
```typescript
describe('Feature tests', () => {
    it('test 1', () => {
        process.env.FEATURE_X = 'enabled';
        // ... test ...
        // No cleanup!
    });

    it('test 2', () => {
        // This test inherits FEATURE_X from test 1!
        // Non-deterministic behavior
    });
});
```

**Why wrong**: Tests affect each other, order-dependent failures

**Right**: Always clean up in `afterEach`

```typescript
describe('Feature tests', () => {
    const originalEnv = process.env;

    afterEach(() => {
        process.env = originalEnv;
    });

    it('test 1', () => {
        process.env = { ...originalEnv, FEATURE_X: 'enabled' };
        // ... test ...
    });

    it('test 2', () => {
        process.env = { ...originalEnv };
        // Clean slate for this test
    });
});
```

## Standard 5: Configuration Precedence Testing

### The Precedence Hierarchy

Most applications follow this precedence (highest to lowest):

1. **Command-line arguments** (explicit user intent)
2. **Environment variables** (session-specific)
3. **Config file** (persistent user preferences)
4. **Defaults** (fallback values)

### Testing Precedence

You must test that higher-priority sources override lower-priority ones:

```typescript
describe('Configuration precedence', () => {
    let tempDir: string;
    let configPath: string;

    beforeEach(() => {
        tempDir = mkdtempSync(join(tmpdir(), 'precedence-test-'));
        configPath = join(tempDir, 'config.json');
    });

    afterEach(() => {
        rmSync(tempDir, { recursive: true, force: true });
    });

    it('should use default when nothing specified', async () => {
        process.env = {};
        const value = await getValue();
        expect(value).toBe(DEFAULT_VALUE);
    });

    it('should use config file over default', async () => {
        await fs.writeFile(configPath, JSON.stringify({
            option: 'from_config'
        }));

        process.env = { CONFIG_PATH: configPath };
        const value = await getValue();
        expect(value).toBe('from_config');
    });

    it('should use env var over config file', async () => {
        await fs.writeFile(configPath, JSON.stringify({
            option: 'from_config'
        }));

        process.env = {
            CONFIG_PATH: configPath,
            OPTION: 'from_env'
        };

        const value = await getValue();
        expect(value).toBe('from_env');
    });

    it('should use CLI arg over env var', async () => {
        process.env = { OPTION: 'from_env' };

        const value = await getValue({ cliArgs: { option: 'from_cli' } });
        expect(value).toBe('from_cli');
    });
});
```

### Multi-Source Integration Test

```typescript
describe('Configuration source integration', () => {
    it('should correctly merge all sources with precedence', async () => {
        // Set up all sources
        await fs.writeFile(configPath, JSON.stringify({
            feature: {
                option1: 'from_config',
                option2: 'from_config',
                option3: 'from_config'
            }
        }));

        process.env = {
            CONFIG_PATH: configPath,
            OPTION2: 'from_env',
            OPTION3: 'from_env'
        };

        const cliArgs = { option3: 'from_cli' };

        // Load config through normal path
        const config = await loadFullConfig(cliArgs);

        // Verify precedence
        expect(config.feature.option1).toBe('from_config');  // Only in config
        expect(config.feature.option2).toBe('from_env');     // Env overrides config
        expect(config.feature.option3).toBe('from_cli');     // CLI overrides all
    });
});
```

## Standard 6: Test Organization and Markers

### Organizing Config Tests

**Recommended structure:**

```
tests/
├── unit/                          # Mechanism tests
│   ├── cache.test.ts              # Cache mechanism works
│   ├── network.test.ts            # Network mechanism works
│   └── ...
├── integration/                   # Config contract tests
│   ├── config/
│   │   ├── cache-config.test.ts   # cache.* config options
│   │   ├── network-config.test.ts # network.* config options
│   │   └── ...
│   └── env/
│       ├── api-keys.test.ts       # API key env vars
│       ├── paths.test.ts          # Path override env vars
│       └── ...
└── e2e/                           # End-to-end tests
    └── ...
```

### Test Markers/Tags

Use descriptive test names with clear prefixes:

```typescript
// Config contract tests - clearly labeled
describe('Config contract: cache.maxSize', () => {
    it('should respect cache.maxSize from config file', async () => {
        // CONTRACT: cache.maxSize must control actual cache size
        // ...
    });
});

// Environment variable tests - clearly labeled
describe('Environment: CACHE_HOME', () => {
    it('should use CACHE_HOME for cache directory', () => {
        // CONTRACT: CACHE_HOME env var must control cache location
        // ...
    });
});

// Mechanism tests - no "contract" prefix
describe('TokenizerCache', () => {
    it('should evict oldest entries when full', () => {
        // Tests mechanism, not configuration
        // ...
    });
});
```

### Using Vitest/Jest Test Filters

```typescript
// Tag tests with describe.each or custom naming
describe('Config contract: cache', () => {
    // These tests verify config contracts
});

describe('Mechanism: cache', () => {
    // These tests verify mechanisms
});
```

Run specific test categories:
```bash
# Run only config contract tests
npm test -- --grep "Config contract"

# Run only environment variable tests
npm test -- --grep "Environment:"

# Run only mechanism tests
npm test -- --grep "Mechanism:"
```

## Standard 7: Test Naming Conventions

### Contract Tests

**Pattern**: `should respect <config.path> from <source>`

**Examples**:
```typescript
it('should respect cache.maxSize from config file', ...)
it('should respect TIMEOUT_MS from environment', ...)
it('should respect --port CLI argument', ...)
```

### Mechanism Tests

**Pattern**: `should <behavior> when <condition>`

**Examples**:
```typescript
it('should evict oldest entries when cache full', ...)
it('should retry request when network error occurs', ...)
it('should validate schema when loading config', ...)
```

### Precedence Tests

**Pattern**: `should use <higher> over <lower>`

**Examples**:
```typescript
it('should use env var over config file', ...)
it('should use CLI arg over env var', ...)
it('should use config file over default', ...)
```

### Default Behavior Tests

**Pattern**: `should <default-behavior> when <config> not set`

**Examples**:
```typescript
it('should use default timeout when TIMEOUT_MS not set', ...)
it('should disable feature when ENABLE_X not set', ...)
it('should use ~/.cache when CACHE_HOME not set', ...)
```

## Standard 8: Common Pitfalls and Solutions

### Pitfall 1: Async Config Loading Not Awaited

**Problem**:
```typescript
it('should use config value', () => {
    loadConfig();  // Async but not awaited!
    const result = getValue();
    expect(result).toBe(expectedFromConfig);  // Fails - config not loaded yet
});
```

**Solution**:
```typescript
it('should use config value', async () => {
    await loadConfig();
    const result = getValue();
    expect(result).toBe(expectedFromConfig);
});
```

### Pitfall 2: Singleton Config Manager

**Problem**: Config manager is singleton, tests interfere with each other

**Solution**: Reset singleton or use dependency injection

```typescript
// Option 1: Reset singleton between tests
describe('Config tests', () => {
    afterEach(() => {
        ConfigManager.reset();  // Clear singleton
    });
});

// Option 2: Use dependency injection
class MyService {
    constructor(private config: ConfigManager) {}
}

describe('MyService', () => {
    it('should use injected config', () => {
        const mockConfig = { /* ... */ };
        const service = new MyService(mockConfig);
        // Test with specific config
    });
});
```

### Pitfall 3: Cached Config Values

**Problem**: Config loaded once, cached, subsequent tests get stale values

**Solution**: Clear cache or reload config per test

```typescript
describe('Config tests', () => {
    beforeEach(async () => {
        await ConfigManager.clearCache();
        // or
        await ConfigManager.reload();
    });
});
```

### Pitfall 4: Global State Pollution

**Problem**: Tests modify global config state, affecting other tests

**Solution**: Isolate config per test

```typescript
describe('Config tests', () => {
    let originalConfig: Config;

    beforeEach(() => {
        originalConfig = getGlobalConfig();
    });

    afterEach(() => {
        setGlobalConfig(originalConfig);
    });

    it('test with custom config', () => {
        setGlobalConfig({ /* custom */ });
        // Test...
    });
});
```

### Pitfall 5: File System Race Conditions

**Problem**: Async file writes not completed before config load

**Solution**: Always await file operations

```typescript
it('should load config from file', async () => {
    await fs.writeFile(configPath, JSON.stringify(config));  // Await!
    await fs.sync();  // If available, ensure flush
    const loaded = await loadConfig(configPath);
    expect(loaded).toEqual(config);
});
```

## Standard 9: Red Flags in Test Review

During code review, flag these issues:

### 🚩 Red Flag 1: No Config Integration Test

```typescript
// New config option added to schema
const ConfigSchema = z.object({
    newFeature: z.object({
        enabled: z.boolean().default(false)  // NEW OPTION
    })
});

// ❌ Only mechanism test exists
describe('NewFeature', () => {
    it('should work when enabled', () => {
        const feature = new NewFeature({ enabled: true });
        expect(feature.isEnabled()).toBe(true);
    });
});

// ✅ Config integration test required
describe('Config contract: newFeature.enabled', () => {
    it('should respect newFeature.enabled from config', async () => {
        const config = { newFeature: { enabled: true } };
        const feature = await createNewFeature(config);
        expect(feature.isEnabled()).toBe(true);
    });
});
```

### 🚩 Red Flag 2: Mocked Config in "Integration" Test

```typescript
// ❌ This is not an integration test
it('should use config value', async () => {
    vi.spyOn(ConfigManager, 'load').mockResolvedValue({
        option: 'value'
    });
    // ... test ...
});
```

### 🚩 Red Flag 3: Missing Environment Reset

```typescript
// ❌ No cleanup
describe('Tests', () => {
    it('test 1', () => {
        process.env.OPTION = 'value';
        // No afterEach cleanup
    });
});
```

### 🚩 Red Flag 4: Testing Only Happy Path

```typescript
// ❌ Only tests when config is valid
it('should use config value', async () => {
    const config = { option: 'valid' };
    // ... test ...
});

// ✅ Should also test: missing config, invalid config, defaults
```

### 🚩 Red Flag 5: No Precedence Testing

```typescript
// ❌ Config and env both set, but precedence not tested
it('should work with config', async () => {
    // Has both config file AND env var, but doesn't verify which wins
});
```

## Standard 10: Integration with Existing Standards

### Connection to Test Environment Isolation Standards

Config contract tests must follow isolation standards:

- ✅ Use temporary directories for config files
- ✅ Control `process.env` explicitly
- ✅ Clean up after tests
- ✅ No reading from actual user config files

See: `TypeScript-Test-Environment-Isolation-Standards.md`

### Connection to Data Structure Documentation Standards

Config schemas should be documented:

```typescript
/**
 * Application configuration schema.
 */
export const ConfigSchema = z.object({
    /** Cache configuration */
    cache: z.object({
        /** Maximum cache size in MB */
        maxSize: z.number().default(100),

        /** Cache expiration in days */
        expirationDays: z.number().default(30)
    }),

    /** Network configuration */
    network: z.object({
        /** Request timeout in milliseconds */
        timeout: z.number().default(30000),

        /** Number of retry attempts */
        retries: z.number().default(3)
    })
});
```

See: `Data-Structure-Documentation-Standards.md`

## Standard 11: Enforcement and Compliance

### Required for PR Approval

Pull requests adding or modifying configuration options must include:

1. ✅ Updated config schema (Zod or similar)
2. ✅ Updated `docs/core/Config-Spec.md` or `docs/core/Environment-Variables-Spec.md`
3. ✅ Config contract integration test
4. ✅ Updated example files (`.env.example`, `config.example.json`)
5. ✅ Mechanism tests for new functionality

### Health Check Integration

Consider adding automated checks:

```typescript
// scripts/validate-config-tests.ts
/**
 * Validates that all config schema options have integration tests.
 */
async function validateConfigTests() {
    const schema = ConfigSchema.shape;
    const configKeys = extractAllKeys(schema);

    const testFiles = await glob('tests/integration/config/**/*.test.ts');
    const testedKeys = await extractTestedConfigKeys(testFiles);

    const untested = configKeys.filter(key => !testedKeys.includes(key));

    if (untested.length > 0) {
        console.error('Config options without integration tests:', untested);
        process.exit(1);
    }
}
```

### Documentation Review

During review, verify:

- Config option documented in `Config-Spec.md` or `Environment-Variables-Spec.md`
- Test clearly states what contract it verifies
- Both mechanism and config integration tests exist
- Example files updated

## Summary: The Golden Rules

### 1. Two Test Types Required
- ✅ **DO** write mechanism tests for functionality
- ✅ **DO** write config integration tests for configuration
- ✅ **DO** test that config actually controls behavior
- ❌ **DON'T** assume mechanism tests verify configuration

### 2. Integration Test Requirements
- ✅ **DO** create real config files in temporary directories
- ✅ **DO** load config through normal ConfigManager path
- ✅ **DO** use factory functions, not direct instantiation
- ❌ **DON'T** mock ConfigManager in integration tests

### 3. Environment Variable Testing
- ✅ **DO** test with variable set and unset
- ✅ **DO** control `process.env` explicitly
- ✅ **DO** clean up environment in `afterEach`
- ❌ **DON'T** inherit developer's environment

### 4. Configuration Precedence
- ✅ **DO** test all precedence levels
- ✅ **DO** verify higher priority overrides lower
- ✅ **DO** document precedence order
- ❌ **DON'T** assume precedence works without testing

### 5. Test Organization
- ✅ **DO** separate mechanism tests from config tests
- ✅ **DO** use clear naming conventions
- ✅ **DO** include "Contract:" in integration test descriptions
- ❌ **DON'T** mix unit and integration concerns

### 6. Cleanup and Isolation
- ✅ **DO** use temporary directories for config files
- ✅ **DO** reset environment after each test
- ✅ **DO** clear config cache between tests
- ❌ **DON'T** pollute global state

### 7. Schema Validation
- ✅ **DO** use Zod or similar for config schemas
- ✅ **DO** test schema validation
- ✅ **DO** test defaults from schema
- ❌ **DON'T** skip validation testing

## See Also

- `TypeScript-Test-Environment-Isolation-Standards.md` - Test isolation requirements
- `Data-Structure-Documentation-Standards.md` - Config schema documentation
- `docs/core/Config-Spec.md` - Configuration specification
- `docs/core/Environment-Variables-Spec.md` - Environment variables specification

---

**Remember**: Configuration is a feature. If a feature is worth implementing, it's worth testing. Config contract tests prove that documented features actually work.
