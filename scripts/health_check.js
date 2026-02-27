/**
 * Health check script for Node.js projects (TypeScript and JavaScript).
 * Runs code quality checks including build validation, type checking, security scanning,
 * dependency auditing, documentation validation, linting, and code formatting.
 * Designed to be run before git commits to ensure code quality.
 *
 * Uses Node.js ecosystem tools (ESLint, Prettier, TypeDoc, npm audit).
 *
 * Flags:
 *   --aggressive: Enable all auto-fixes including those that may change behavior.
 *   --clean: Clear TypeScript build cache (.tsbuildinfo files) before running checks.
 *       Use this flag for quality gates (pre-commit, CI/CD) to ensure deterministic
 *       results. Incremental builds are faster but may mask configuration errors
 *       when tsconfig or imports change.
 *   --commands: Display all commands used by each check without running them.
 *   --help, -h: Show help message with available options.
 *
 * Usage Examples:
 *   # Standard development check (uses cached build information for speed)
 *   node scripts/health_check.js
 *
 *   # Quality gate check (fresh analysis, no cached state)
 *   node scripts/health_check.js --clean
 *
 *   # Aggressive fixes with clean analysis
 *   node scripts/health_check.js --aggressive --clean
 *
 *   # Show available commands
 *   node scripts/health_check.js --commands
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Import shared utilities
const {
  findPackageJsonRoot,
  detectProjectLanguages,
  detectPackageManager,
  getCheckDirs,
  isToolAvailable,
  isScriptAvailable,
} = require('./wsd_utils.js');

/**
 * Clear TypeScript build cache by removing .tsbuildinfo files.
 *
 * Recursively searches for .tsbuildinfo files in the project root
 * and removes them to ensure fresh type checking analysis.
 * @param {string} rootDir - The root directory to search from
 * @returns {void}
 */
function clearTypeScriptCache(rootDir) {
  console.log('  Clearing TypeScript cache for fresh analysis...');

  /**
   * Recursively find all .tsbuildinfo files in a directory.
   * @param {string} dir - Directory to search
   * @returns {string[]} Array of absolute paths to .tsbuildinfo files
   */
  function findTsBuildInfoFiles(dir) {
    const files = [];
    try {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          // Skip node_modules for performance
          if (entry.name !== 'node_modules') {
            files.push(...findTsBuildInfoFiles(fullPath));
          }
        } else if (entry.name.endsWith('.tsbuildinfo')) {
          files.push(fullPath);
        }
      }
    } catch (_error) {
      // Ignore permission errors or inaccessible directories
    }
    return files;
  }

  const buildInfoFiles = findTsBuildInfoFiles(rootDir);
  let removedCount = 0;

  for (const file of buildInfoFiles) {
    try {
      fs.unlinkSync(file);
      removedCount++;
    } catch (_error) {
      // Ignore errors for locked or inaccessible files
    }
  }

  if (removedCount > 0) {
    console.log(`  Removed ${removedCount} .tsbuildinfo file(s)`);
  }
}

const projectRoot = findPackageJsonRoot();

/**
 * Execute a shell command and return the result with captured output.
 *
 * Captures stdout and stderr into variables for later analysis without
 * streaming to console. Callers are responsible for displaying output
 * as needed based on success/failure status.
 * @param {string} command - The command to execute
 * @param {boolean} allowFailure - If true, don't exit on failure
 * @returns {{success: boolean, stdout: string, stderr: string, exitCode: number}} Object containing execution results with success flag, captured stdout/stderr strings, and process exit code
 */
function runCommand(command, allowFailure = false) {
  try {
    const stdout = execSync(command, {
      cwd: projectRoot,
      encoding: 'utf-8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    return { success: true, stdout: stdout || '', stderr: '', exitCode: 0 };
  } catch (error) {
    const stdout = error.stdout ? error.stdout.toString() : '';
    const stderr = error.stderr ? error.stderr.toString() : '';
    const exitCode = error.status || 1;

    if (!allowFailure) {
      console.error(`Health Check: ERROR during command execution!`);
      console.error('Command:', command);
      console.error('Return code:', exitCode);
      if (stdout) {
        console.error('Output:\n', stdout);
      }
      if (stderr) {
        console.error('Errors:\n', stderr);
      }
      process.exit(1);
    }

    return { success: false, stdout: stdout, stderr: stderr, exitCode: exitCode };
  }
}

/**
 * Run a health check step with minimal progress reporting and captured output.
 *
 * Provides a standardized interface for running checks that:
 * - Displays a brief single-line progress indicator
 * - Captures all output without streaming to console
 * - Returns captured output for caller analysis (caller handles display)
 *
 * Output is intentionally minimal - callers are responsible for displaying
 * error details only when checks fail, keeping successful runs quiet.
 * @param {string} command - The command to execute
 * @param {string} stepName - Human-readable description of the check step
 * @param {object} options - Configuration options
 * @param {boolean} options.allowFailure - If true, don't exit on failure (default: true)
 * @param {boolean} options.silent - If true, suppress all progress output (default: false)
 * @returns {{success: boolean, stdout: string, stderr: string, exitCode: number}} Object containing check execution results with success flag, captured stdout/stderr output, and process exit code
 */
function runCheck(command, stepName, options = {}) {
  const { allowFailure = true, silent = false } = options;

  if (!silent) {
    process.stdout.write(`  ${stepName}... `);
  }

  const result = runCommand(command, allowFailure);

  if (!silent) {
    if (result.success) {
      console.log('✓');
    } else {
      console.log('✗');
    }
  }

  return result;
}

/**
 * Check if dependencies are in sync and install if needed.
 *
 * Runs silently unless installation is required, keeping output minimal.
 * Exits with error if no package manager lock file is found.
 */
function checkDependencies() {
  const packageManager = detectPackageManager();
  if (packageManager === null) {
    console.error('Error: No package manager lock file found.');
    console.error('Create one by running: pnpm install, npm install, yarn install, or bun install');
    process.exit(1);
  }
  const nodeModulesExists = fs.existsSync(path.join(projectRoot, 'node_modules'));
  const packageLock = path.join(projectRoot, 'package-lock.json');
  const packageJson = path.join(projectRoot, 'package.json');

  let needsInstall = !nodeModulesExists;

  // Check if package-lock.json is newer than node_modules
  if (!needsInstall && fs.existsSync(packageLock)) {
    const lockMtime = fs.statSync(packageLock).mtime;
    const nodeModulesMtime = fs.statSync(path.join(projectRoot, 'node_modules')).mtime;
    needsInstall = lockMtime > nodeModulesMtime;
  }

  // Check if package.json is newer than node_modules
  if (!needsInstall && fs.existsSync(packageJson)) {
    const packageMtime = fs.statSync(packageJson).mtime;
    const nodeModulesMtime = fs.existsSync(path.join(projectRoot, 'node_modules'))
      ? fs.statSync(path.join(projectRoot, 'node_modules')).mtime
      : new Date(0);
    needsInstall = packageMtime > nodeModulesMtime;
  }

  if (needsInstall) {
    console.log(`Dependencies out of sync. Running '${packageManager} install'...`);
    runCommand(`${packageManager} install`, false);
    console.log('Dependencies installed.');
  }
}

/**
 * Parse ESLint JSON output for error analysis.
 *
 * Handles npm script output which includes header lines before the JSON array.
 * Extracts the JSON array portion and parses it to count errors and warnings.
 * @param {string} output - Raw ESLint output (may include npm script headers)
 * @returns {{errorCount: number, warningCount: number, fixableCount: number}} Object containing total error count, warning count, and count of auto-fixable issues
 */
function parseESLintOutput(output) {
  try {
    // Extract JSON array from output - npm/pnpm prepend headers and may append errors
    // Match JSON array: '[' at line start through ']' at line end
    const jsonArrayMatch = output.match(/^\[.*\]$/m);
    if (!jsonArrayMatch) {
      throw new Error('No JSON array found in output');
    }
    const jsonOutput = jsonArrayMatch[0];

    const results = JSON.parse(jsonOutput);
    let errorCount = 0;
    let warningCount = 0;
    let fixableCount = 0;

    for (const result of results) {
      errorCount += result.errorCount || 0;
      warningCount += result.warningCount || 0;
      fixableCount += result.fixableErrorCount + result.fixableWarningCount || 0;
    }

    return { errorCount, warningCount, fixableCount };
  } catch {
    // Fallback: parse text output (for non-JSON ESLint formats)
    const errorMatch = output.match(/(\d+)\s+errors?/i);
    const warningMatch = output.match(/(\d+)\s+warnings?/i);

    return {
      errorCount: errorMatch ? parseInt(errorMatch[1]) : 0,
      warningCount: warningMatch ? parseInt(warningMatch[1]) : 0,
      fixableCount: 0,
    };
  }
}

/**
 * Parse npm audit JSON output for vulnerability analysis.
 * Implements multi-strategy parsing with automatic fallbacks and self-validation
 * to handle variations across npm versions and output formats.
 *
 * Strategy Priority:
 * 1. npm v7+ format (metadata.vulnerabilities) - primary
 * 2. npm v6 format (actions.resolves) - secondary
 * 3. Regex fallback (text pattern matching) - for non-JSON output
 * 4. ID counting (GHSA/CVE identifiers) - when regex yields 0
 * 5. Proximity extraction (numbers near "vulnerability" text) - last resort
 *
 * Self-validates results by detecting contradictory output (e.g., "vulnerability"
 * text present but count is 0) and attempts additional extraction strategies.
 * @param {string} output - Raw npm audit output (JSON or text)
 * @returns {{total: number, critical: number, high: number, moderate: number, low: number, info: number, parseStrategy: string}}
 *   parseStrategy indicates which parsing approach succeeded: 'v7', 'v6', 'json-unknown',
 *   'regex-fallback', 'id-counting', or 'proximity-extraction'
 */
function parseNpmAuditOutput(output) {
  let parseStrategy = 'unknown';

  try {
    const audit = JSON.parse(output);

    // npm v7+ format (primary strategy)
    if (audit.metadata && audit.metadata.vulnerabilities) {
      const vuln = audit.metadata.vulnerabilities;
      parseStrategy = 'v7';
      return {
        total: vuln.total || 0,
        critical: vuln.critical || 0,
        high: vuln.high || 0,
        moderate: vuln.moderate || 0,
        low: vuln.low || 0,
        info: 0,
        parseStrategy,
      };
    }

    // npm v6 format (secondary strategy)
    if (audit.actions) {
      parseStrategy = 'v6';
      let total = 0;
      const severities = { critical: 0, high: 0, moderate: 0, low: 0, info: 0 };

      for (const action of audit.actions) {
        if (action.resolves) {
          for (const resolve of action.resolves) {
            total++;
            const severity = resolve.severity;
            if (severity in severities) {
              severities[severity]++;
            }
          }
        }
      }

      return { total, ...severities, parseStrategy };
    }

    // JSON parsed but no recognized format
    parseStrategy = 'json-unknown';
    return { total: 0, critical: 0, high: 0, moderate: 0, low: 0, info: 0, parseStrategy };
  } catch {
    // Fallback: regex-based parsing for non-JSON output
    parseStrategy = 'regex-fallback';
    console.log('Warning: Using fallback npm audit parsing strategy');

    // Primary fallback pattern
    const vulnMatch = output.match(/found\s+(\d+)\s+vulnerabilit/i);
    let total = vulnMatch ? parseInt(vulnMatch[1]) : 0;

    // Secondary fallback: count GHSA/CVE IDs
    if (total === 0) {
      const ghsaCount = (output.match(/GHSA-[\w-]+/g) || []).length;
      const cveCount = (output.match(/CVE-\d{4}-\d+/g) || []).length;
      if (ghsaCount > 0 || cveCount > 0) {
        total = ghsaCount + cveCount;
        parseStrategy = 'id-counting';
      }
    }

    // Self-validation: detect contradictory output
    if (total === 0 && /vulnerabilit/i.test(output)) {
      console.log('Warning: Detected vulnerability text but count is 0 - parsing may have failed');
      // Try proximity extraction as last resort
      const numbersNearVuln = output.match(/(\d+)[^0-9]*vulnerabilit/i);
      if (numbersNearVuln) {
        total = parseInt(numbersNearVuln[1]);
        parseStrategy = 'proximity-extraction';
      }
    }

    return {
      total,
      critical: 0,
      high: 0,
      moderate: 0,
      low: 0,
      info: 0,
      parseStrategy,
    };
  }
}

/**
 * Parse bun audit JSON output for vulnerability analysis.
 *
 * Bun outputs a dictionary keyed by package name, where each value is an array
 * of vulnerability objects containing severity information.
 *
 * Example format:
 * {
 *   "lodash": [{ "severity": "moderate", ... }],
 *   "express": [{ "severity": "high", ... }, { "severity": "low", ... }]
 * }
 * @param {string} output - Raw bun audit JSON output
 * @returns {{total: number, critical: number, high: number, moderate: number, low: number, info: number, parseStrategy: string}}
 *   Object containing vulnerability counts by severity and 'bun' or 'bun-parse-error' strategy.
 */
function parseBunAuditOutput(output) {
  try {
    const audit = JSON.parse(output);
    const packages = Object.keys(audit);

    let total = 0;
    const severities = { critical: 0, high: 0, moderate: 0, low: 0, info: 0 };

    for (const pkg of packages) {
      const vulns = audit[pkg];
      if (Array.isArray(vulns)) {
        for (const vuln of vulns) {
          total++;
          const severity = vuln.severity;
          if (severity in severities) {
            severities[severity]++;
          }
        }
      }
    }

    return { total, ...severities, parseStrategy: 'bun' };
  } catch {
    return {
      total: 0,
      critical: 0,
      high: 0,
      moderate: 0,
      low: 0,
      info: 0,
      parseStrategy: 'bun-parse-error',
    };
  }
}

/**
 * Parse yarn audit JSON-lines (NDJSON) output for vulnerability analysis.
 *
 * Yarn outputs one JSON object per line. The final line typically contains the
 * auditSummary with aggregated vulnerability counts. This parser scans all lines
 * looking for the summary line.
 *
 * Example format (each line is separate JSON):
 * {"type":"auditAdvisory","data":{"resolution":{...},"advisory":{...}}}
 * {"type":"auditSummary","data":{"vulnerabilities":{"info":0,"low":1,"moderate":2,"high":0,"critical":0}}}
 * @param {string} output - Raw yarn audit NDJSON output
 * @returns {{total: number, critical: number, high: number, moderate: number, low: number, info: number, parseStrategy: string}}
 *   Object containing vulnerability counts by severity. Strategy is 'yarn' on success,
 *   'yarn-no-summary' if valid JSON but no summary line, or 'yarn-parse-error' if no valid JSON.
 */
function parseYarnAuditOutput(output) {
  const lines = output.trim().split('\n');
  let hasValidJson = false;

  for (const line of lines) {
    try {
      const obj = JSON.parse(line);
      hasValidJson = true;

      if (obj.type === 'auditSummary' && obj.data && obj.data.vulnerabilities) {
        const vuln = obj.data.vulnerabilities;
        return {
          total:
            (vuln.info || 0) +
            (vuln.low || 0) +
            (vuln.moderate || 0) +
            (vuln.high || 0) +
            (vuln.critical || 0),
          critical: vuln.critical || 0,
          high: vuln.high || 0,
          moderate: vuln.moderate || 0,
          low: vuln.low || 0,
          info: vuln.info || 0,
          parseStrategy: 'yarn',
        };
      }
    } catch {
      // Not valid JSON, continue to next line
    }
  }

  // Distinguish between parse error (no valid JSON at all) and no summary line
  if (!hasValidJson) {
    return {
      total: 0,
      critical: 0,
      high: 0,
      moderate: 0,
      low: 0,
      info: 0,
      parseStrategy: 'yarn-parse-error',
    };
  }

  return {
    total: 0,
    critical: 0,
    high: 0,
    moderate: 0,
    low: 0,
    info: 0,
    parseStrategy: 'yarn-no-summary',
  };
}

/**
 * Registry mapping package managers to their audit output parsers.
 * @type {{[key: string]: function(string): {total: number, critical: number, high: number, moderate: number, low: number, info: number, parseStrategy: string}}}
 */
const AUDIT_PARSERS = {
  npm: parseNpmAuditOutput,
  pnpm: parseNpmAuditOutput,
  bun: parseBunAuditOutput,
  yarn: parseYarnAuditOutput,
};

/**
 * Parse package manager audit output using the appropriate parser.
 *
 * Dispatches to the correct parser based on the package manager. Each package
 * manager has a different JSON format for audit output, so this function routes
 * to the appropriate parser function via the AUDIT_PARSERS registry.
 * @param {string} output - Raw audit command output (typically JSON)
 * @param {string} packageManager - Package manager name ('npm', 'pnpm', 'yarn', 'bun')
 * @returns {{total: number, critical: number, high: number, moderate: number, low: number, info: number, parseStrategy: string}}
 *   Object containing vulnerability counts by severity and the parsing strategy used.
 *   If no parser exists for the package manager, returns zeros with 'unsupported' strategy.
 */
function parseAuditOutput(output, packageManager) {
  const parser = AUDIT_PARSERS[packageManager];
  if (!parser) {
    console.log(`Warning: No audit parser for package manager: ${packageManager}`);
    return {
      total: 0,
      critical: 0,
      high: 0,
      moderate: 0,
      low: 0,
      info: 0,
      parseStrategy: 'unsupported',
    };
  }
  return parser(output);
}

/**
 * Extract error lines from generic tool output using common error patterns.
 *
 * Identifies lines matching common error indicators:
 * - "error:" (case-insensitive)
 * - "error TS####" (TypeScript compiler errors)
 * - ":line:col ... error" (standard lint/compiler format)
 * - "failed" (case-insensitive)
 *
 * Deduplicates identical error lines and trims whitespace.
 * @param {string} output - Raw tool output to scan
 * @returns {string[]} Array of unique error lines found in output, empty if none found
 */
function extractErrorLines(output) {
  if (!output) return [];

  const lines = output.split('\n');
  const errorLines = [];

  for (const line of lines) {
    // Match common error patterns
    if (
      /error\s*:/i.test(line) ||
      /error\s+TS\d+/i.test(line) ||
      /:\d+:\d+.*error/i.test(line) ||
      /failed/i.test(line)
    ) {
      const trimmed = line.trim();
      if (trimmed && !errorLines.includes(trimmed)) {
        errorLines.push(trimmed);
      }
    }
  }

  return errorLines;
}

/**
 * Extract error lines from ESLint JSON output with structured formatting.
 *
 * Parses ESLint JSON format and extracts severity 2 (error-level) messages,
 * formatting them as "fileName:line:column - message".
 *
 * Handles npm script output which includes header lines before the JSON array.
 * Falls back to generic text extraction if JSON parsing fails.
 * @param {string} output - Raw ESLint JSON output (may include npm script headers)
 * @returns {string[]} Array of formatted error lines ("file:line:col - message"), empty if no errors
 */
function extractESLintErrorLines(output) {
  try {
    // Extract JSON array from output - npm/pnpm prepend headers and may append errors
    // Match JSON array: '[' at line start through ']' at line end
    const jsonArrayMatch = output.match(/^\[.*\]$/m);
    if (!jsonArrayMatch) {
      throw new Error('No JSON array found in output');
    }
    const jsonOutput = jsonArrayMatch[0];

    const results = JSON.parse(jsonOutput);
    const errorLines = [];

    for (const result of results) {
      if (result.messages) {
        for (const msg of result.messages) {
          if (msg.severity === 2) {
            // Error level
            const filePath = result.filePath || 'unknown';
            const fileName = filePath.split('/').pop();
            errorLines.push(`${fileName}:${msg.line}:${msg.column} - ${msg.message}`);
          }
        }
      }
    }

    return errorLines;
  } catch {
    // Fallback for non-JSON output
    return extractErrorLines(output);
  }
}

/**
 * Extract security-relevant messages from ESLint JSON output.
 *
 * Parses ESLint JSON format and extracts messages from security-related rules
 * (both errors and warnings). Security rules are identified by ruleId prefix
 * 'security/' or by being from eslint-plugin-security.
 *
 * This function captures warnings (severity 1) in addition to errors (severity 2)
 * because security warnings are actionable and should be visible to the user.
 *
 * Handles npm script output which includes header lines before the JSON array.
 * @param {string} output - Raw ESLint JSON output (may include npm script headers)
 * @returns {string[]} Array of formatted security messages ("file:line:col - [rule] message")
 */
function extractSecurityMessages(output) {
  try {
    // Extract JSON array from output - npm/pnpm prepend headers and may append errors
    // Match JSON array: '[' at line start through ']' at line end
    const jsonArrayMatch = output.match(/^\[.*\]$/m);
    if (!jsonArrayMatch) {
      throw new Error('No JSON array found in output');
    }
    const jsonOutput = jsonArrayMatch[0];

    const results = JSON.parse(jsonOutput);
    const messages = [];

    for (const result of results) {
      if (result.messages) {
        for (const msg of result.messages) {
          // Include both errors (2) and warnings (1) for security-related rules
          const isSecurityRule =
            msg.ruleId && (msg.ruleId.startsWith('security/') || msg.ruleId.includes('security'));
          const isSeverityRelevant = msg.severity === 1 || msg.severity === 2;

          if (isSeverityRelevant && (isSecurityRule || msg.severity === 2)) {
            const filePath = result.filePath || 'unknown';
            const fileName = filePath.split('/').pop();
            const ruleInfo = msg.ruleId ? `[${msg.ruleId}] ` : '';
            messages.push(`${fileName}:${msg.line}:${msg.column} - ${ruleInfo}${msg.message}`);
          }
        }
      }
    }

    return messages;
  } catch {
    // Fallback for non-JSON output
    return extractErrorLines(output);
  }
}

/**
 * Display error summary showing first N errors with count of remaining.
 *
 * Outputs first maxDisplay errors from the provided array, followed by
 * a summary line "...and N more error(s)" if more errors exist.
 *
 * Example output:
 * First 5 Linting errors:
 * utils.ts:45:10 - Type 'string' is not assignable
 * Header.tsx:23:5 - Cannot find name 'React'
 * ...and 12 more error(s)
 * @param {string[]} errorLines - Array of error lines to display
 * @param {string} checkName - Name of the check for display (e.g., "Linting", "Security")
 * @param {number} maxDisplay - Maximum errors to display before truncating (default 5)
 * @returns {void}
 */
function displayErrorSummary(errorLines, checkName, maxDisplay = 5) {
  if (errorLines.length === 0) return;

  console.log(`\nFirst ${Math.min(errorLines.length, maxDisplay)} ${checkName} errors:`);
  for (let i = 0; i < Math.min(errorLines.length, maxDisplay); i++) {
    console.log(`  ${errorLines[i]}`);
  }

  if (errorLines.length > maxDisplay) {
    console.log(`  ...and ${errorLines.length - maxDisplay} more error(s)`);
  }
}

/**
 * Display all commands used in the health check.
 *
 * Uses placeholder when package manager cannot be detected, allowing the
 * informational display to proceed even without a lock file.
 */
function showCommands() {
  const detectedPackageManager = detectPackageManager();
  const packageManager = detectedPackageManager || '<package-manager>';
  let dirs = getCheckDirs();

  if (dirs === null) {
    console.error(
      'Warning: wsd.checkDirs is not configured in package.json. WSD setup may be incomplete.'
    );
  }

  console.log('='.repeat(60));
  console.log('HEALTH CHECK COMMANDS REFERENCE');
  console.log('='.repeat(60));
  console.log(`Package Manager: ${packageManager}`);
  if (detectedPackageManager === null) {
    console.log('Note: No lock file found. Create one to run actual health checks.');
  }
  if (dirs !== null && dirs.length > 0) {
    console.log(`Directories checked: ${dirs.join(', ')}`);
  } else {
    console.log('Note: No checkDirs configured. Commands shown are for reference only.');
    console.log('Configure wsd.checkDirs in package.json to enable code quality checks.');
    dirs = ['<source_dir>']; // Placeholder for command display
  }
  console.log('='.repeat(60));

  const commands = [
    ['Build', `${packageManager} run build`],
    ['Type Checking', `${packageManager} run typecheck (optional)`],
    ['Security Scan', `${packageManager} run lint:security (optional)`],
    ['Dependency Audit', `${packageManager} audit --json`],
    ['TypeDoc Validation', `${packageManager} run typedoc:validate (optional)`],
    [
      'Doc Completeness',
      `node scripts/doc_validator_typescript.js --dirs=${dirs.join(',')} (optional)`,
    ],
    ['Linting Check', `${packageManager} run lint:json`],
    ['Linting Fix (safe)', `${packageManager} run lint:fix`],
    ['Linting Fix (aggressive)', `${packageManager} run lint:fix -- --max-warnings 0`],
    ['Formatting Check', `${packageManager} run format:check`],
    ['Formatting Fix', `${packageManager} run format`],
  ];

  const maxCheckLength = Math.max(...commands.map((c) => c[0].length));
  console.log(`${'Check'.padEnd(maxCheckLength + 2)} Command`);
  console.log('-'.repeat(100));

  for (const [check, command] of commands) {
    console.log(`${check.padEnd(maxCheckLength + 2)} ${command}`);
  }

  console.log('='.repeat(60));
  console.log('\nNote: All commands should be run from the project root directory.');
  console.log(
    '      Package.json scripts define tool commands; health check adds execution flags.'
  );
  console.log('      Directories are read from package.json "wsd.checkDirs" configuration.');
}

/**
 * Format and display the health check summary table.
 * @param {Array<Array<string>>} results - Array of check results where each inner array is [checkName, status, details]
 */
function printSummaryTable(results) {
  console.log('\n' + '='.repeat(60));
  console.log('HEALTH CHECK SUMMARY');
  console.log('='.repeat(60));
  console.log(`${'Check'.padEnd(20)} ${'Status'.padEnd(15)} ${'Details'.padEnd(25)}`);
  console.log('-'.repeat(60));

  for (const [checkName, status, details] of results) {
    console.log(`${checkName.padEnd(20)} ${status.padEnd(15)} ${details.padEnd(25)}`);
  }

  console.log('='.repeat(60));
}

/**
 * Main health check execution.
 */
function main() {
  // Check for help flag
  if (process.argv.includes('--help') || process.argv.includes('-h')) {
    console.log('Node.js Health Check Script');
    console.log('\nUsage: node scripts/health_check.js [OPTIONS]');
    console.log('\nOptions:');
    console.log('  --aggressive    Enable all auto-fixes (not just safe ones)');
    console.log('  --clean         Clear TypeScript cache before running checks');
    console.log('  --commands      Show all commands used by each check');
    console.log('  --help, -h      Show this help message');
    process.exit(0);
  }

  // Check for --commands flag
  if (process.argv.includes('--commands')) {
    showCommands();
    process.exit(0);
  }

  const aggressiveMode = process.argv.includes('--aggressive');
  const clean = process.argv.includes('--clean');
  const packageManager = detectPackageManager();
  if (packageManager === null) {
    console.error('Error: No package manager lock file found.');
    console.error('Create one by running: pnpm install, npm install, yarn install, or bun install');
    process.exit(1);
  }
  const dirs = getCheckDirs();

  if (dirs === null) {
    console.error(
      'Warning: wsd.checkDirs is not configured in package.json. WSD setup may be incomplete.'
    );
  }

  // Determine if directory-dependent checks should run
  const dirsConfigured = dirs !== null && dirs.length > 0;

  // Detect project languages and check for TypeScript
  const languages = detectProjectLanguages();
  const isTypeScript = languages.includes('typescript');

  // Brief header - keep it minimal
  console.log(
    `\n${isTypeScript ? 'TypeScript' : 'JavaScript'} Health Check ${aggressiveMode ? '(aggressive)' : ''}`
  );
  console.log('-'.repeat(40));

  // Check dependencies first (runs silently unless install needed)
  checkDependencies();

  // Show what we're checking
  console.log('Running checks...');

  // Track overall success and individual results
  let allPassed = true;
  const checkResults = []; // Array of [name, status, notes]

  // Build validation runs first - structural failures (type errors, import issues) block meaningful analysis
  if (isTypeScript) {
    if (!isScriptAvailable('build')) {
      process.stdout.write('  Build... ');
      console.log('⏭');
      checkResults.push(['Build Validation', '⏭️  SKIPPED', 'No build script configured']);
    } else {
      // Clear TypeScript cache if --clean flag is set
      if (clean) {
        clearTypeScriptCache(projectRoot);
      }

      const buildResult = runCheck(`${packageManager} run build`, 'Build');

      if (!buildResult.success) {
        allPassed = false;
        const errorLines = extractErrorLines(buildResult.stdout + '\n' + buildResult.stderr);
        displayErrorSummary(errorLines, 'Build');
        checkResults.push(['Build Validation', '❌ FAILED', 'Check tsconfig.json']);
      } else {
        checkResults.push(['Build Validation', '✅ PASSED', '']);
      }
    }
  } else {
    checkResults.push(['Build Validation', '⏭️  SKIPPED', 'JavaScript project']);
  }

  // Type checking - delegates to the optional "typecheck" script in package.json.
  // Positioned after Build Validation so that structural failures are caught first,
  // and before Security Scan following the check execution order contract:
  // structural checks → security → documentation → code quality → formatting.
  //
  // Clean-state behavior: clearTypeScriptCache() removes .tsbuildinfo files before
  // Build Validation when --clean is set. Since Type Checking runs after Build
  // Validation in the execution sequence, it inherits the clean state automatically.
  if (!isScriptAvailable('typecheck')) {
    process.stdout.write('  Type Checking... ');
    console.log('⏭');
    checkResults.push(['Type Checking', '⏭️  SKIPPED', 'No typecheck script configured']);
  } else {
    const typeCheckResult = runCheck(`${packageManager} run typecheck`, 'Type Checking');

    if (!typeCheckResult.success) {
      allPassed = false;
      const errorLines = extractErrorLines(typeCheckResult.stdout + '\n' + typeCheckResult.stderr);
      displayErrorSummary(errorLines, 'Type Checking');
      checkResults.push(['Type Checking', '❌ FAILED', 'Type errors found']);
    } else {
      checkResults.push(['Type Checking', '✅ PASSED', '']);
    }
  }

  // Security checks - Requires checkDirs
  if (dirsConfigured) {
    if (isToolAvailable('eslint-plugin-security') && isScriptAvailable('lint:security')) {
      const securityResult = runCheck(`${packageManager} run lint:security`, 'Security Scan');

      if (!securityResult.success) {
        const analysis = parseESLintOutput(securityResult.stdout);
        if (analysis.errorCount > 0) {
          allPassed = false;
          const securityMessages = extractSecurityMessages(securityResult.stdout);
          displayErrorSummary(securityMessages, 'Security');
          checkResults.push(['Security Scan', '❌ FAILED', `${analysis.errorCount} issue(s)`]);
        } else if (analysis.warningCount > 0) {
          // Show security warnings even though they don't fail the check
          const securityMessages = extractSecurityMessages(securityResult.stdout);
          displayErrorSummary(securityMessages, 'Security');
          checkResults.push([
            'Security Scan',
            '⚠️  WARNING',
            `${analysis.warningCount} warning(s)`,
          ]);
        }
      } else {
        checkResults.push(['Security Scan', '✅ PASSED', '']);
      }
    } else {
      checkResults.push(['Security Scan', '⏭️  SKIPPED', 'Not configured']);
    }
  } else {
    checkResults.push(['Security Scan', '⏭️  SKIPPED', 'No checkDirs configured']);
  }

  // Dependency audit - Always runs (scans installed packages, not checkDirs)
  try {
    const auditResult = runCheck(`${packageManager} audit --json`, 'Dependency Audit');

    if (!auditResult.success) {
      allPassed = false;
      const vulnAnalysis = parseAuditOutput(auditResult.stdout, packageManager);

      let details = `${vulnAnalysis.total} vulnerabilit${vulnAnalysis.total === 1 ? 'y' : 'ies'}`;
      if (vulnAnalysis.critical > 0) {
        details += ` (${vulnAnalysis.critical} critical)`;
      }

      checkResults.push(['Dependency Audit', '❌ FAILED', details]);
    } else {
      checkResults.push(['Dependency Audit', '✅ PASSED', '']);
    }
  } catch (_error) {
    checkResults.push(['Dependency Audit', '⏭️  SKIPPED', 'Audit command failed']);
  }

  // TypeDoc Validation - Validates TypeScript documentation can be generated
  // Independent check #1 of TypeScript documentation validation
  if (dirsConfigured) {
    if (!isTypeScript) {
      process.stdout.write('  TypeDoc Validation... ');
      console.log('⏭');
      checkResults.push(['TypeDoc Validation', '⏭️  SKIPPED', 'JavaScript project']);
    } else {
      const typedocAvailable = isToolAvailable('typedoc') && isScriptAvailable('typedoc:validate');

      if (!typedocAvailable) {
        process.stdout.write('  TypeDoc Validation... ');
        console.log('⏭');
        checkResults.push(['TypeDoc Validation', '⏭️  SKIPPED', 'Not configured']);
      } else {
        const typedocResult = runCheck(
          `${packageManager} run typedoc:validate`,
          'TypeDoc Validation',
          {
            silent: true,
          }
        );

        process.stdout.write('  TypeDoc Validation... ');
        if (!typedocResult.success) {
          allPassed = false;
          console.log('✗');
          checkResults.push(['TypeDoc Validation', '❌ FAILED', 'Validation errors']);
        } else {
          console.log('✓');
          checkResults.push(['TypeDoc Validation', '✅ PASSED', '']);
        }
      }
    }
  } else {
    checkResults.push(['TypeDoc Validation', '⏭️  SKIPPED', 'No checkDirs configured']);
  }

  // Doc Completeness - Validates TypeScript documentation semantic completeness
  // Independent check #2 of TypeScript documentation validation
  if (dirsConfigured) {
    if (!isTypeScript) {
      process.stdout.write('  Doc Completeness... ');
      console.log('⏭');
      checkResults.push(['Doc Completeness', '⏭️  SKIPPED', 'JavaScript project']);
    } else {
      const astValidatorPath = path.join(__dirname, 'doc_validator_typescript.js');
      const astValidatorAvailable = fs.existsSync(astValidatorPath);

      if (!astValidatorAvailable) {
        process.stdout.write('  Doc Completeness... ');
        console.log('⏭');
        checkResults.push(['Doc Completeness', '⏭️  SKIPPED', 'Not configured']);
      } else {
        const docValidatorResult = runCheck(
          `node "${astValidatorPath}" --dirs=${dirs.join(',')}`,
          'Doc Completeness',
          { silent: true }
        );

        process.stdout.write('  Doc Completeness... ');
        if (!docValidatorResult.success) {
          const errorMatch = docValidatorResult.stdout.match(/Errors:\s+(\d+)/);
          const warningMatch = docValidatorResult.stdout.match(/Warnings:\s+(\d+)/);
          const errorCount = errorMatch ? parseInt(errorMatch[1]) : 0;
          const warningCount = warningMatch ? parseInt(warningMatch[1]) : 0;

          if (errorCount > 0 || warningCount > 0) {
            console.log('⚠');
            checkResults.push([
              'Doc Completeness',
              '⚠️  WARNING',
              `${errorCount} error(s), ${warningCount} warning(s) (non-blocking)`,
            ]);
          } else {
            console.log('✓');
            checkResults.push(['Doc Completeness', '✅ PASSED', '']);
          }
        } else {
          console.log('✓');
          checkResults.push(['Doc Completeness', '✅ PASSED', '']);
        }
      }
    }
  } else {
    checkResults.push(['Doc Completeness', '⏭️  SKIPPED', 'No checkDirs configured']);
  }

  // Linting - Requires checkDirs
  //
  // Three-Tier Status System for Linting Results:
  // ---------------------------------------------
  // The linting check uses a three-tier status system to accurately report code quality:
  //
  //   ✅ PASSED  - No errors AND no warnings. Code is fully compliant.
  //   ⚠️ WARNING - No errors but warnings exist. Code compiles but has style/quality issues.
  //   ❌ FAILED  - Errors exist (with or without warnings). Code has problems that must be fixed.
  //
  // ESLint Exit Code Semantics:
  // ---------------------------
  // ESLint's exit codes do NOT distinguish between clean code and warnings-only:
  //   - Exit 0: No errors (but warnings may exist - ESLint treats warnings as non-blocking)
  //   - Exit 1: Errors found (severity 2 violations)
  //   - Exit 2: Configuration or internal error
  //
  // Because ESLint exits with code 0 when only warnings exist, we MUST parse the JSON
  // output to accurately detect and report warnings. Relying solely on exit codes would
  // incorrectly report "PASSED" when hundreds of warnings exist.
  //
  // Warning Behavior:
  // -----------------
  // Warnings are reported with ⚠️ WARNING status but do not cause the health check to
  // fail (exit code remains 0). Only errors cause the health check to fail (exit code 1).
  // This allows teams to see code quality issues while not blocking commits for non-critical
  // style violations.
  //
  if (dirsConfigured) {
    if (!isScriptAvailable('lint:json')) {
      process.stdout.write('  Linting... ');
      console.log('⏭');
      checkResults.push(['Linting', '⏭️  SKIPPED', 'No lint:json script configured']);
    } else {
      // Run ESLint with JSON output for structured parsing
      const lintCheckResult = runCheck(`${packageManager} run lint:json`, 'Linting');

      // Always parse ESLint output regardless of exit code to detect warnings.
      // This is required because ESLint exits 0 when only warnings exist.
      const analysis = parseESLintOutput(lintCheckResult.stdout);

      if (analysis.errorCount > 0) {
        // Errors exist - attempt auto-fix
        const lintFixCmd = aggressiveMode
          ? `${packageManager} run lint:fix -- --max-warnings 0`
          : `${packageManager} run lint:fix`;

        runCheck(lintFixCmd, 'Lint fix', { silent: true });

        // Re-check after fix attempt
        const postFixResult = runCheck(`${packageManager} run lint:json`, 'Lint recheck', {
          silent: true,
        });
        const postFixAnalysis = parseESLintOutput(postFixResult.stdout);

        if (postFixAnalysis.errorCount > 0) {
          // Still have errors after fix attempt
          allPassed = false;
          const errorLines = extractESLintErrorLines(postFixResult.stdout);
          displayErrorSummary(errorLines, 'Linting');

          let details = `${postFixAnalysis.errorCount} error(s), ${postFixAnalysis.warningCount} warning(s)`;
          if (!aggressiveMode && postFixAnalysis.fixableCount > 0) {
            details += ` (${postFixAnalysis.fixableCount} fixable)`;
          }

          checkResults.push(['Linting', '❌ FAILED', details]);
        } else if (postFixAnalysis.warningCount > 0) {
          // Errors fixed but warnings remain
          checkResults.push([
            'Linting',
            '⚠️  WARNING',
            `${postFixAnalysis.warningCount} warning(s) (errors fixed)`,
          ]);
        } else {
          // All issues fixed
          checkResults.push(['Linting', '✅ FIXED', 'All issues auto-fixed']);
        }
      } else if (analysis.warningCount > 0) {
        // No errors but warnings exist - report WARNING status
        checkResults.push(['Linting', '⚠️  WARNING', `${analysis.warningCount} warning(s)`]);
      } else {
        // Truly clean - no errors and no warnings
        checkResults.push(['Linting', '✅ PASSED', '']);
      }
    }
  } else {
    checkResults.push(['Linting', '⏭️  SKIPPED', 'No checkDirs configured']);
  }

  // Formatting - Requires checkDirs
  if (dirsConfigured) {
    if (!isScriptAvailable('format:check')) {
      process.stdout.write('  Formatting... ');
      console.log('⏭');
      checkResults.push(['Code Formatting', '⏭️  SKIPPED', 'No format:check script configured']);
    } else {
      const formatResult = runCheck(`${packageManager} run format:check`, 'Formatting');

      if (!formatResult.success) {
        // Auto-fix silently
        runCheck(`${packageManager} run format`, 'Format fix', {
          silent: true,
          allowFailure: false,
        });
        checkResults.push(['Code Formatting', '✅ FIXED', 'Auto-formatted']);
      } else {
        checkResults.push(['Code Formatting', '✅ PASSED', '']);
      }
    }
  } else {
    checkResults.push(['Code Formatting', '⏭️  SKIPPED', 'No checkDirs configured']);
  }

  // Always print summary table - this is the primary output
  printSummaryTable(checkResults);

  // Brief final status
  if (allPassed) {
    console.log('✅ Health check passed');
    process.exit(0);
  } else {
    console.log('❌ Health check found issues');
    process.exit(1);
  }
}

// Run main if this is the entry point
if (require.main === module) {
  // Handle keyboard interrupts (Ctrl+C) gracefully
  process.on('SIGINT', () => {
    console.error('\n\nHealth check interrupted or encountered an error:');
    console.error('User interrupted with Ctrl+C');
    process.exit(1);
  });

  try {
    main();
  } catch (error) {
    console.error('\n\nHealth check interrupted or encountered an error:');
    console.error(error.message);
    process.exit(1);
  }
}

module.exports = {
  runCommand,
  runCheck,
  parseESLintOutput,
  parseAuditOutput,
  extractErrorLines,
  extractESLintErrorLines,
  extractSecurityMessages,
  displayErrorSummary,
};
