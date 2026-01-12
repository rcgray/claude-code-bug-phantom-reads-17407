# Test Environment Isolation Standards (TypeScript/Jest/Vitest)

## Overview

This document establishes mandatory standards for test environment isolation in TypeScript projects using Jest or Vitest. These standards ensure that tests are deterministic, reproducible, and independent of developer machine configuration.

### Core Principle

**Tests must pass identically on any machine, regardless of local environment configuration.**

A test suite that depends on a developer's specific setup is not truly automated—it's a source of false failures, CI/CD instability, and developer friction.

## Why Test Isolation Matters

### Problems Caused by Poor Isolation

1. **Non-deterministic failures**: Tests pass on one machine, fail on another
2. **CI/CD brittleness**: Build servers require special configuration to match developer environments
3. **Onboarding friction**: New developers encounter mysterious test failures
4. **Hidden bugs**: Tests may pass due to "lucky" local config, hiding real issues
5. **Debugging overhead**: Hours wasted investigating environment-dependent failures

### Benefits of Proper Isolation

1. **Confidence**: Green tests mean the code works, red tests mean it doesn't
2. **Portability**: Tests run anywhere—local machines, CI/CD, containers
3. **Maintainability**: Tests explicitly declare their dependencies
4. **Debugging**: Failures are reproducible and clearly caused by code changes

## Standard 1: Environment Variable Isolation

### Mandatory Practice

**Every test must explicitly control its environment variables.**

Tests fall into two categories:

#### 1A: Tests of Default Behavior (No Environment Variables Set)

These tests verify behavior when environment variables are NOT set. They must clear the environment:

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

describe('Default cache directory behavior', () => {
    const originalEnv = process.env;

    beforeEach(() => {
        // Reset to clean environment
        process.env = {};
    });

    afterEach(() => {
        // Restore original environment
        process.env = originalEnv;
    });

    it('should use default cache directory when HF_HOME is not set', () => {
        const tokenizer = new HuggingFaceTokenizer('meta-llama/Llama-2-7b-hf');
        const cacheDir = tokenizer.getCacheDir();

        // Now we KNOW HF_HOME was not set
        expect(cacheDir).toBe(path.join(os.homedir(), '.cache', 'huggingface', 'hub'));
    });
});
```

**Why**: Without clearing the environment, the test inherits the developer's shell environment, making it non-deterministic.

#### 1B: Tests of Environment-Dependent Behavior

These tests verify behavior when specific environment variables ARE set. They must explicitly set only what's needed:

```typescript
describe('Custom cache directory behavior', () => {
    const originalEnv = process.env;

    beforeEach(() => {
        // Set specific environment variable
        process.env = { HF_HOME: '/custom/path' };
    });

    afterEach(() => {
        process.env = originalEnv;
    });

    it('should use custom cache directory when HF_HOME is set', () => {
        const tokenizer = new HuggingFaceTokenizer('meta-llama/Llama-2-7b-hf');
        const cacheDir = tokenizer.getCacheDir();

        // Now we KNOW exactly what HF_HOME is
        expect(cacheDir).toBe(path.join('/custom/path', 'hub'));
    });
});
```

### Common Environment Variables in TypeScript Projects

When testing code that reads these variables, always control them explicitly:

- API keys (e.g., `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) - Must be mocked unless in opt-in integration test
- `HF_HOME` - Must be explicitly set or cleared
- `NODE_ENV` - Must be controlled for environment-specific behavior
- `CONFIG_PATH` or custom config paths - Must be controlled, typically with temporary directories
- Cache directory variables - Must be controlled, typically with `tmp()` directories

### Anti-Pattern Example

```typescript
// ❌ BAD: This test will fail if developer has HF_HOME set
it('should use default cache directory', () => {
    const tokenizer = new HuggingFaceTokenizer('meta-llama/Llama-2-7b-hf');
    const cacheDir = tokenizer.getCacheDir();
    expect(cacheDir).toBe(path.join(os.homedir(), '.cache', 'huggingface', 'hub'));
});
```

### Correct Pattern

```typescript
// ✅ GOOD: Environment is explicitly controlled
describe('Cache directory behavior', () => {
    beforeEach(() => {
        process.env = {}; // Clear all environment variables
    });

    it('should use default cache directory', () => {
        const tokenizer = new HuggingFaceTokenizer('meta-llama/Llama-2-7b-hf');
        const cacheDir = tokenizer.getCacheDir();
        expect(cacheDir).toBe(path.join(os.homedir(), '.cache', 'huggingface', 'hub'));
    });
});
```

### Alternative: Using Jest Mock Functions

```typescript
describe('Environment variable handling', () => {
    const originalEnv = process.env;

    afterEach(() => {
        process.env = originalEnv;
    });

    it('should handle missing API key', () => {
        process.env = { ...originalEnv };
        delete process.env.API_KEY;

        expect(() => new ApiClient()).toThrow('API_KEY environment variable is required');
    });

    it('should use API key when provided', () => {
        process.env = { ...originalEnv, API_KEY: 'test-key-123' };

        const client = new ApiClient();
        expect(client.apiKey).toBe('test-key-123');
    });
});
```

## Standard 2: File System Isolation

### Mandatory Practice

**Tests must never read from or write to actual user directories.**

### Using Temporary Directories

All file operations should use temporary directories. For Vitest, you can use the `os.tmpdir()` function and clean up after tests:

```typescript
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync, writeFileSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

describe('Config file loading', () => {
    let tempDir: string;

    beforeEach(() => {
        // Create unique temporary directory
        tempDir = mkdtempSync(join(tmpdir(), 'test-'));
    });

    afterEach(() => {
        // Clean up temporary directory
        rmSync(tempDir, { recursive: true, force: true });
    });

    it('should load configuration from file', () => {
        // Create temporary config file
        const configFile = join(tempDir, 'config.json');
        writeFileSync(configFile, JSON.stringify({
            defaultProvider: 'openai'
        }));

        // Test with temporary file
        const config = ConfigManager.load(configFile);
        expect(config.defaultProvider).toBe('openai');
    });
});
```

### Using temp-fs or temp-dir Libraries

For more convenient temporary file handling:

```typescript
import tmp from 'tmp-promise';

describe('Config file operations', () => {
    it('should load configuration from file', async () => {
        // Create temporary directory with automatic cleanup
        await tmp.withDir(async ({ path: tempDir }) => {
            const configFile = join(tempDir, 'config.json');
            await fs.writeFile(configFile, JSON.stringify({
                defaultProvider: 'openai'
            }));

            const config = await ConfigManager.load(configFile);
            expect(config.defaultProvider).toBe('openai');
        }, { unsafeCleanup: true });
    });
});
```

### Never Access Real User Directories

```typescript
// ❌ BAD: Reads from actual user config directory
it('should load user config', () => {
    const configPath = join(os.homedir(), '.config', 'myapp', 'config.json');
    const config = ConfigManager.load(configPath);
    // What if user doesn't have this file? Or has different settings?
});

// ✅ GOOD: Uses temporary directory
it('should load config from file', () => {
    const tempDir = mkdtempSync(join(tmpdir(), 'test-'));
    process.env = { CONFIG_HOME: tempDir };

    const configFile = join(tempDir, 'config.json');
    writeFileSync(configFile, JSON.stringify({ defaultProvider: 'openai' }));

    const config = ConfigManager.load(configFile);
    expect(config.defaultProvider).toBe('openai');

    rmSync(tempDir, { recursive: true, force: true });
});
```

### Test Fixtures Location

Permanent test data files belong in `tests/fixtures/` or `tests/test-data/`:

```
tests/
├── fixtures/
│   ├── sample-config.json
│   ├── external-model-data.json
│   └── models/
│       └── minimal-test.bin
```

These are **version-controlled fixtures**, not developer configuration files.

## Standard 3: Configuration File Isolation

### Mandatory Practice

**Tests must never depend on developer's actual configuration files.**

### Pattern: Mock Config Loading

```typescript
import { vi } from 'vitest';

describe('CLI with config', () => {
    it('should use config values', async () => {
        // Create mock config in memory
        const mockConfig = {
            defaultProvider: 'anthropic',
            getAlias: vi.fn().mockReturnValue('claude-3-opus-20240229')
        };

        vi.spyOn(ConfigManager, 'load').mockResolvedValue(mockConfig);

        const result = await cli.execute(['chat', '--model', 'opus']);
        expect(result.exitCode).toBe(0);
    });
});
```

### Pattern: Temporary Config Files

```typescript
describe('Config manager platform-specific behavior', () => {
    let tempDir: string;

    beforeEach(() => {
        tempDir = mkdtempSync(join(tmpdir(), 'config-test-'));
        process.env = { CONFIG_HOME: tempDir };
    });

    afterEach(() => {
        rmSync(tempDir, { recursive: true, force: true });
    });

    it('should load aliases from config file', async () => {
        const configPath = join(tempDir, 'config.json');
        await fs.writeFile(configPath, JSON.stringify({
            aliases: {
                gpt4: 'gpt-4-turbo'
            }
        }));

        const manager = new ConfigManager();
        const aliases = await manager.loadAliases();
        expect(aliases).toEqual({ gpt4: 'gpt-4-turbo' });
    });
});
```

### Never Test Against Real User Files

```typescript
// ❌ BAD: Depends on developer's actual .env file
it('should discover API key', () => {
    const apiKey = loadEnvFile('.env');
    expect(apiKey).toBeDefined();
    // What if developer doesn't have .env? Or uses .env.local?
});

// ✅ GOOD: Creates temporary .env file
it('should load API key from env file', () => {
    const tempDir = mkdtempSync(join(tmpdir(), 'env-test-'));
    const envFile = join(tempDir, '.env');
    writeFileSync(envFile, 'API_KEY=test-key-123');

    const config = loadEnvFile(envFile);
    expect(config.API_KEY).toBe('test-key-123');

    rmSync(tempDir, { recursive: true, force: true });
});
```

## Standard 4: Network Isolation

### Mandatory Practice

**Unit tests must mock all network calls. Integration tests requiring network must be opt-in.**

### Unit Tests: Always Mock Network

```typescript
import { vi } from 'vitest';
import axios from 'axios';

vi.mock('axios');

describe('Anthropic tokenization (mocked)', () => {
    it('should count tokens using mocked API', async () => {
        // Mock the API response
        (axios.post as any).mockResolvedValue({
            data: {
                token_count: 42
            }
        });

        const tokenizer = new AnthropicTokenizer('claude-3-opus-20240229');
        const count = await tokenizer.countTokens('Hello world');

        expect(count).toBe(42);
        expect(axios.post).toHaveBeenCalledOnce();
    });
});
```

### Using MSW (Mock Service Worker) for HTTP Mocking

```typescript
import { rest } from 'msw';
import { setupServer } from 'msw/node';

const server = setupServer(
    rest.post('https://api.anthropic.com/v1/messages/count_tokens', (req, res, ctx) => {
        return res(ctx.json({ token_count: 42 }));
    })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('Anthropic API integration (mocked with MSW)', () => {
    it('should count tokens', async () => {
        const tokenizer = new AnthropicTokenizer('claude-3-opus-20240229');
        const count = await tokenizer.countTokens('Hello world');
        expect(count).toBe(42);
    });
});
```

### Integration Tests: Opt-in with describe.skipIf

For tests that genuinely need network access:

```typescript
const hasApiKey = !!process.env.ANTHROPIC_API_KEY;

describe.skipIf(!hasApiKey)('Anthropic API integration (real)', () => {
    it('should count tokens with real API', async () => {
        const tokenizer = new AnthropicTokenizer('claude-3-opus-20240229');
        const count = await tokenizer.countTokens('Hello world');
        expect(count).toBeGreaterThan(0);
    });
});
```

### Custom Test Runner Configuration

```typescript
// vitest.config.ts
export default defineConfig({
    test: {
        testMatch: ['**/*.test.ts'],
        exclude: ['**/*.integration.test.ts'], // Skip integration tests by default
    },
});

// vitest.integration.config.ts
export default defineConfig({
    test: {
        testMatch: ['**/*.integration.test.ts'], // Only run integration tests
    },
});
```

Run tests:
```bash
# Skip integration tests (default)
npm test

# Run only integration tests
npm run test:integration
```

## Standard 5: Test Categories and Isolation Levels

### Unit Tests (Default)

**Characteristics:**
- No network access (mock all external APIs)
- No file system access to user directories (use temporary directories)
- No environment variable dependencies (explicitly control `process.env`)
- Fast execution (milliseconds)
- No external dependencies

**Isolation Requirements:**
- ✅ Environment variables cleared or explicitly set
- ✅ File system isolated to temporary directories
- ✅ Network calls mocked
- ✅ No reading from actual config files

**Run by default:**
```bash
npm test  # Runs all unit tests
```

### Integration Tests (Opt-in)

**Characteristics:**
- May use real network calls to test actual API integration
- Still use controlled environments (not developer's personal config)
- Require explicit opt-in (via flags, separate test files, or environment variables)
- Slower execution (seconds to minutes)

**Isolation Requirements:**
- ✅ Still avoid developer's personal config
- ✅ Use test-specific credentials
- ✅ Clean up any created resources
- ⚠️ May make real network calls

**Run explicitly:**
```bash
npm run test:integration
# Or with environment variable
WITH_API_KEYS=true npm test
```

### End-to-End Tests (Separate)

**Characteristics:**
- Test entire system in production-like environment
- May use real services, databases, APIs
- Significantly slower
- Run in CI/CD only or on-demand

**Best Practice:** Keep these completely separate from unit/integration tests.

## Standard 6: Common Patterns and Fixtures

### Reusable Test Fixtures

```typescript
// tests/helpers/fixtures.ts
import { mkdtempSync, writeFileSync, rmSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

export function createTempConfig(config: object): { path: string; cleanup: () => void } {
    const tempDir = mkdtempSync(join(tmpdir(), 'config-'));
    const configPath = join(tempDir, 'config.json');
    writeFileSync(configPath, JSON.stringify(config));

    return {
        path: configPath,
        cleanup: () => rmSync(tempDir, { recursive: true, force: true })
    };
}

export function withTempConfig<T>(config: object, fn: (configPath: string) => T): T {
    const { path: configPath, cleanup } = createTempConfig(config);
    try {
        return fn(configPath);
    } finally {
        cleanup();
    }
}
```

Usage:

```typescript
describe('Config loading', () => {
    it('should load config', () => {
        withTempConfig({ provider: 'openai' }, (configPath) => {
            const config = ConfigManager.load(configPath);
            expect(config.provider).toBe('openai');
        });
    });
});
```

### Environment Variable Helper

```typescript
// tests/helpers/env.ts
export function withEnv<T>(
    env: Record<string, string | undefined>,
    fn: () => T
): T {
    const originalEnv = process.env;
    try {
        process.env = { ...env };
        return fn();
    } finally {
        process.env = originalEnv;
    }
}

export function withClearEnv<T>(fn: () => T): T {
    return withEnv({}, fn);
}
```

Usage:

```typescript
describe('Environment handling', () => {
    it('should use custom cache dir', () => {
        withEnv({ CACHE_DIR: '/custom/cache' }, () => {
            const cache = new CacheManager();
            expect(cache.cacheDir).toBe('/custom/cache');
        });
    });

    it('should use default when env not set', () => {
        withClearEnv(() => {
            const cache = new CacheManager();
            expect(cache.cacheDir).toContain('.cache');
        });
    });
});
```

### Mock API Helper

```typescript
// tests/helpers/mockApi.ts
import { vi } from 'vitest';

export function mockApiResponse<T>(response: T) {
    return vi.fn().mockResolvedValue({ data: response });
}

export function mockApiError(error: Error) {
    return vi.fn().mockRejectedValue(error);
}
```

## Standard 7: Anti-Patterns to Avoid

### Anti-Pattern 1: Assuming Developer Environment

```typescript
// ❌ BAD: Assumes developer has specific directory structure
it('should find user config', () => {
    const config = findConfig(); // Looks in process.cwd() or home directory
    expect(config).toBeDefined();
});

// ✅ GOOD: Explicitly creates test environment
it('should find config in specified directory', () => {
    const tempDir = mkdtempSync(join(tmpdir(), 'test-'));
    const configFile = join(tempDir, 'config.json');
    writeFileSync(configFile, '{}');

    const config = findConfig(tempDir);
    expect(config).toBeDefined();

    rmSync(tempDir, { recursive: true, force: true });
});
```

### Anti-Pattern 2: Tests That Require Manual Setup

```typescript
// ❌ BAD: Requires developer to manually set environment variable
it('should connect to database', () => {
    // This test assumes DATABASE_URL is set in developer's environment
    const db = connectDatabase();
    expect(db.isConnected()).toBe(true);
});

// ✅ GOOD: Test provides all necessary configuration
it('should connect to test database', () => {
    process.env = { DATABASE_URL: 'sqlite::memory:' };
    const db = connectDatabase();
    expect(db.isConnected()).toBe(true);
});
```

### Anti-Pattern 3: Shared Mutable State Between Tests

```typescript
// ❌ BAD: Tests share state
let sharedCache: Cache;

beforeAll(() => {
    sharedCache = new Cache();
});

it('test 1', () => {
    sharedCache.set('key', 'value1');
    // ...
});

it('test 2', () => {
    // This test depends on state from test 1!
    const value = sharedCache.get('key');
    expect(value).toBe('value1'); // Brittle!
});

// ✅ GOOD: Each test is independent
describe('Cache operations', () => {
    let cache: Cache;

    beforeEach(() => {
        cache = new Cache();
    });

    it('should set and get values', () => {
        cache.set('key', 'value1');
        expect(cache.get('key')).toBe('value1');
    });

    it('should handle missing keys', () => {
        expect(cache.get('nonexistent')).toBeUndefined();
    });
});
```

### Anti-Pattern 4: Not Cleaning Up After Tests

```typescript
// ❌ BAD: Leaves files and processes running
it('should start server', async () => {
    const server = await startServer();
    expect(server.isRunning()).toBe(true);
    // Server never stopped!
});

// ✅ GOOD: Always clean up
it('should start server', async () => {
    const server = await startServer();
    try {
        expect(server.isRunning()).toBe(true);
    } finally {
        await server.stop();
    }
});
```

### Anti-Pattern 5: Hardcoded Paths

```typescript
// ❌ BAD: Hardcoded absolute paths
it('should load fixture', () => {
    const data = readFileSync('/Users/developer/project/tests/fixtures/data.json');
    // Breaks on other machines!
});

// ✅ GOOD: Relative to project root or __dirname
it('should load fixture', () => {
    const data = readFileSync(join(__dirname, '../fixtures/data.json'));
    // Works anywhere
});
```

## Standard 8: Case Study - Environment Variable Issues

### The Problem

Consider a service that uses an environment variable to determine its cache directory:

```typescript
class CacheService {
    getCacheDir(): string {
        return process.env.CACHE_HOME || join(os.homedir(), '.cache', 'myapp');
    }
}
```

### The Failing Test

```typescript
// ❌ This test fails if developer has CACHE_HOME set
it('should use default cache directory', () => {
    const service = new CacheService();
    expect(service.getCacheDir()).toBe(join(os.homedir(), '.cache', 'myapp'));
});
```

### Why It Fails

If the developer has `CACHE_HOME=/custom/cache` in their shell:
- Test expects: `~/.cache/myapp`
- Test gets: `/custom/cache`
- Result: ❌ Test fails

### The Fix

```typescript
// ✅ Explicitly control environment
describe('CacheService default behavior', () => {
    beforeEach(() => {
        process.env = {}; // Clear environment
    });

    it('should use default cache directory when CACHE_HOME not set', () => {
        const service = new CacheService();
        expect(service.getCacheDir()).toBe(join(os.homedir(), '.cache', 'myapp'));
    });
});

describe('CacheService with custom CACHE_HOME', () => {
    beforeEach(() => {
        process.env = { CACHE_HOME: '/custom/cache' };
    });

    it('should use custom cache directory when CACHE_HOME is set', () => {
        const service = new CacheService();
        expect(service.getCacheDir()).toBe('/custom/cache');
    });
});
```

### Lessons Learned

1. **Always control environment variables explicitly**
2. **Test both "set" and "unset" scenarios**
3. **Don't assume clean environment**
4. **Separate tests for different environment configurations**

## Standard 9: Cache State Isolation

### Mandatory Practice

**Tests must not depend on or modify persistent cache state.**

### Pattern: Temporary Cache Directories

```typescript
describe('Cache operations', () => {
    let tempCacheDir: string;
    let cache: CacheManager;

    beforeEach(() => {
        tempCacheDir = mkdtempSync(join(tmpdir(), 'cache-'));
        cache = new CacheManager(tempCacheDir);
    });

    afterEach(() => {
        rmSync(tempCacheDir, { recursive: true, force: true });
    });

    it('should store and retrieve cached values', async () => {
        await cache.set('key1', { data: 'value1' });
        const result = await cache.get('key1');
        expect(result).toEqual({ data: 'value1' });
    });

    it('should handle cache misses', async () => {
        const result = await cache.get('nonexistent');
        expect(result).toBeUndefined();
    });
});
```

### Pattern: In-Memory Cache for Tests

```typescript
class TestCache implements CacheInterface {
    private store = new Map<string, any>();

    async get(key: string): Promise<any> {
        return this.store.get(key);
    }

    async set(key: string, value: any): Promise<void> {
        this.store.set(key, value);
    }

    async clear(): Promise<void> {
        this.store.clear();
    }
}

describe('Service with caching', () => {
    let cache: TestCache;
    let service: MyService;

    beforeEach(() => {
        cache = new TestCache();
        service = new MyService(cache);
    });

    it('should use cached values', async () => {
        await cache.set('key1', 'cached-value');
        const result = await service.getValue('key1');
        expect(result).toBe('cached-value');
    });
});
```

### Never Use Shared Persistent Cache

```typescript
// ❌ BAD: Uses shared cache directory
it('should cache results', async () => {
    const cache = new CacheManager(); // Uses ~/.cache/myapp
    await cache.set('test-key', 'value');
    // Pollutes developer's cache, may conflict with other tests
});

// ✅ GOOD: Uses isolated cache
it('should cache results', async () => {
    const tempDir = mkdtempSync(join(tmpdir(), 'cache-'));
    const cache = new CacheManager(tempDir);

    await cache.set('test-key', 'value');
    expect(await cache.get('test-key')).toBe('value');

    rmSync(tempDir, { recursive: true, force: true });
});
```

## Standard 10: Global State and Singleton Isolation

### Mandatory Practice

**Tests must reset or mock global state and singletons.**

### Pattern: Resetting Singletons

```typescript
// Singleton implementation
class ConfigManager {
    private static instance: ConfigManager | null = null;
    private config: Config;

    static getInstance(): ConfigManager {
        if (!ConfigManager.instance) {
            ConfigManager.instance = new ConfigManager();
        }
        return ConfigManager.instance;
    }

    // For testing only
    static resetInstance(): void {
        ConfigManager.instance = null;
    }
}

// Test usage
describe('ConfigManager singleton', () => {
    afterEach(() => {
        ConfigManager.resetInstance();
    });

    it('should return same instance', () => {
        const instance1 = ConfigManager.getInstance();
        const instance2 = ConfigManager.getInstance();
        expect(instance1).toBe(instance2);
    });

    it('should be independent test', () => {
        // This test gets fresh instance due to afterEach reset
        const instance = ConfigManager.getInstance();
        expect(instance).toBeDefined();
    });
});
```

### Pattern: Dependency Injection for Testability

```typescript
// Instead of singleton, use dependency injection
class MyService {
    constructor(private config: ConfigManager) {}

    doSomething(): string {
        return this.config.getValue('key');
    }
}

// Easy to test
describe('MyService', () => {
    it('should use injected config', () => {
        const mockConfig = {
            getValue: vi.fn().mockReturnValue('test-value')
        };

        const service = new MyService(mockConfig as any);
        expect(service.doSomething()).toBe('test-value');
    });
});
```

### Pattern: Mocking Global Variables

```typescript
describe('Global state handling', () => {
    const originalFetch = global.fetch;

    afterEach(() => {
        global.fetch = originalFetch;
    });

    it('should use mocked fetch', async () => {
        global.fetch = vi.fn().mockResolvedValue({
            json: async () => ({ data: 'test' })
        });

        const result = await fetchData();
        expect(result.data).toBe('test');
    });
});
```

## Standard 11: Working Directory Isolation

### Mandatory Practice

**Tests must not depend on the current working directory.**

### Pattern: Always Use Absolute Paths

```typescript
// ❌ BAD: Depends on cwd
it('should load config', () => {
    const config = loadConfig('config.json'); // Looks in cwd
    // Fails if test is run from different directory
});

// ✅ GOOD: Uses absolute path
it('should load config', () => {
    const configPath = join(__dirname, '../fixtures/config.json');
    const config = loadConfig(configPath);
    expect(config).toBeDefined();
});
```

### Pattern: Temporarily Change Working Directory

```typescript
describe('CWD-dependent operations', () => {
    const originalCwd = process.cwd();
    let tempDir: string;

    beforeEach(() => {
        tempDir = mkdtempSync(join(tmpdir(), 'cwd-test-'));
        process.chdir(tempDir);
    });

    afterEach(() => {
        process.chdir(originalCwd);
        rmSync(tempDir, { recursive: true, force: true });
    });

    it('should find config in cwd', () => {
        writeFileSync(join(tempDir, 'config.json'), '{"key":"value"}');
        const config = findConfigInCwd();
        expect(config.key).toBe('value');
    });
});
```

### Using __dirname and import.meta.url

```typescript
// For CommonJS
const fixtureDir = join(__dirname, '../fixtures');

// For ES modules
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const fixtureDir = join(__dirname, '../fixtures');
```

## Standard 12: Standard Stream Isolation (CLI Testing)

### Mandatory Practice

**CLI tests must capture stdout/stderr and not pollute test output.**

### Pattern: Capture Console Output

```typescript
describe('CLI output', () => {
    let consoleLogSpy: any;
    let consoleErrorSpy: any;

    beforeEach(() => {
        consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
        consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
        consoleLogSpy.mockRestore();
        consoleErrorSpy.mockRestore();
    });

    it('should output success message', () => {
        cli.execute(['success']);
        expect(consoleLogSpy).toHaveBeenCalledWith('Operation successful');
    });

    it('should output error message', () => {
        cli.execute(['error']);
        expect(consoleErrorSpy).toHaveBeenCalledWith(expect.stringContaining('Error:'));
    });
});
```

### Pattern: Capture Process Streams

```typescript
import { Writable } from 'stream';

class StringWritable extends Writable {
    private chunks: string[] = [];

    _write(chunk: any, encoding: string, callback: () => void) {
        this.chunks.push(chunk.toString());
        callback();
    }

    getOutput(): string {
        return this.chunks.join('');
    }
}

describe('CLI with stream capture', () => {
    let stdout: StringWritable;
    let stderr: StringWritable;

    beforeEach(() => {
        stdout = new StringWritable();
        stderr = new StringWritable();
    });

    it('should output to stdout', async () => {
        const cli = new CLI({ stdout, stderr });
        await cli.execute(['info']);

        expect(stdout.getOutput()).toContain('Information message');
        expect(stderr.getOutput()).toBe('');
    });
});
```

### Pattern: Test Exit Codes Without Exiting

```typescript
describe('CLI exit codes', () => {
    let exitSpy: any;

    beforeEach(() => {
        exitSpy = vi.spyOn(process, 'exit').mockImplementation(() => {
            throw new Error('process.exit called');
        });
    });

    afterEach(() => {
        exitSpy.mockRestore();
    });

    it('should exit with code 0 on success', async () => {
        try {
            await cli.execute(['success']);
        } catch (e: any) {
            expect(e.message).toBe('process.exit called');
        }
        expect(exitSpy).toHaveBeenCalledWith(0);
    });

    it('should exit with code 1 on error', async () => {
        try {
            await cli.execute(['error']);
        } catch (e: any) {
            expect(e.message).toBe('process.exit called');
        }
        expect(exitSpy).toHaveBeenCalledWith(1);
    });
});
```

### Using Testing Libraries for CLI

For more robust CLI testing, consider libraries like:

```typescript
import { execa } from 'execa';

describe('CLI integration', () => {
    it('should execute CLI command', async () => {
        const { stdout, exitCode } = await execa('node', ['dist/cli.js', '--version']);
        expect(exitCode).toBe(0);
        expect(stdout).toMatch(/\d+\.\d+\.\d+/);
    });

    it('should handle errors', async () => {
        try {
            await execa('node', ['dist/cli.js', 'invalid-command']);
        } catch (error: any) {
            expect(error.exitCode).toBe(1);
            expect(error.stderr).toContain('Unknown command');
        }
    });
});
```

---

## Summary: The Golden Rules

### 1. Environment Variables
- ✅ **DO** clear environment with `process.env = {}` before tests
- ✅ **DO** explicitly set required variables
- ✅ **DO** restore original environment in `afterEach`
- ❌ **DON'T** assume any environment variable is set or unset

### 2. File System
- ✅ **DO** use temporary directories for all file operations
- ✅ **DO** clean up temporary files in `afterEach`
- ✅ **DO** use version-controlled fixtures for test data
- ❌ **DON'T** read from or write to user directories

### 3. Configuration
- ✅ **DO** create temporary config files for tests
- ✅ **DO** mock configuration loading
- ✅ **DO** use dependency injection for testability
- ❌ **DON'T** depend on developer's actual config files

### 4. Network
- ✅ **DO** mock all network calls in unit tests
- ✅ **DO** use MSW or similar tools for HTTP mocking
- ✅ **DO** make integration tests opt-in
- ❌ **DON'T** make real API calls in unit tests

### 5. State Management
- ✅ **DO** reset singletons between tests
- ✅ **DO** use `beforeEach` and `afterEach` for setup/teardown
- ✅ **DO** ensure tests are independent
- ❌ **DON'T** share mutable state between tests

### 6. Working Directory
- ✅ **DO** use absolute paths relative to `__dirname`
- ✅ **DO** restore original CWD if changed
- ❌ **DON'T** depend on `process.cwd()`

### 7. Standard Streams
- ✅ **DO** capture console output in tests
- ✅ **DO** mock `process.exit` to test exit codes
- ✅ **DO** use proper CLI testing libraries
- ❌ **DON'T** pollute test output with CLI logs

---

## Testing the Tests

**How to verify your tests are properly isolated:**

1. **Run tests in random order**
   ```bash
   # Vitest
   vitest --sequence.shuffle
   ```

2. **Run tests in different directories**
   ```bash
   cd /tmp && npm test
   ```

3. **Run with cleared environment**
   ```bash
   env -i npm test
   ```

4. **Run in fresh Docker container**
   ```bash
   docker run --rm -v $(pwd):/app -w /app node:20 npm test
   ```

If tests pass in all these scenarios, they're properly isolated!

---

## Conclusion

These standards ensure that TypeScript tests are deterministic, portable, and maintainable. By explicitly controlling all external dependencies—environment variables, file systems, network calls, and configuration—we create test suites that provide genuine confidence in code quality.

**Remember:** If a test fails only on certain machines or requires manual setup, it's not a proper automated test—it's a maintenance burden. Fix it by applying these isolation standards.

**The ultimate test of test quality:** Can a new developer clone the repository and run `npm test` successfully on the first try, without any setup? If yes, you've achieved proper test isolation.
