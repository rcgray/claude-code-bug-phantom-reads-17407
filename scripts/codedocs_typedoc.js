/**
 * @file Generate TypeDoc API documentation for TypeScript projects.
 *
 * This script orchestrates TypeDoc documentation generation:
 * 1. Detects project language (skips JavaScript-only projects)
 * 2. Validates typedoc script availability in package.json
 * 3. Runs TypeDoc via the detected package manager to generate native HTML documentation
 *
 * Uses shared utilities from wsd_utils.js for:
 * - Language detection (detectProjectLanguages)
 * - Package manager detection (detectPackageManager)
 * - Script availability checking (isScriptAvailable)
 * - Directory configuration (getCheckDirs)
 *
 * Configuration:
 * - Output location: dev/reports/typedoc-api-docs/ (HTML directory)
 * - TypeDoc configuration: typedoc.json in project root
 * - Source directories: wsd.checkDirs from package.json (falls back to 'src')
 * - TypeDoc's cleanOutputDir option handles cleanup of stale files
 *
 * For JavaScript-only projects, the script detects the project language and exits
 * gracefully with a helpful message, since TypeDoc is specifically designed for
 * TypeScript projects and requires TypeScript source files.
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Import shared utilities for language detection, package management, and configuration
const {
  detectProjectLanguages,
  detectPackageManager,
  getCheckDirs,
  isScriptAvailable,
} = require('./wsd_utils.js');

// Resolve project root from script location to ensure consistent path resolution
// regardless of the current working directory when the script is invoked.
// This pattern handles both direct execution and require() scenarios.
const __dirname_custom = path.dirname(require.main.filename || __filename);
const PROJECT_ROOT = path.resolve(__dirname_custom, '..');
const REPORTS_DIR = path.join(PROJECT_ROOT, 'dev', 'reports');
const OUTPUT_DIR = path.join(REPORTS_DIR, 'typedoc-api-docs');

/**
 * Run a command and return its results.
 *
 * Executes a shell command synchronously and captures output. Used for running
 * TypeDoc during documentation generation.
 * @param {string[]} cmd - Command and arguments to run (will be joined with spaces)
 * @param {object} options - Options for command execution
 * @param {string} [options.cwd] - Working directory for command execution (defaults to PROJECT_ROOT)
 * @param {boolean} [options.captureOutput] - If true, capture stdout/stderr; if false, inherit stdio
 * @returns {{returncode: number, stdout: string, stderr: string}} Command results with exit code and output
 */
function runCommand(cmd, options = {}) {
  try {
    // Join command array into string for shell execution; execSync handles
    // proper escaping when given a string with shell: false (default)
    const stdout = execSync(cmd.join(' '), {
      encoding: 'utf-8',
      cwd: options.cwd || PROJECT_ROOT,
      // Use 'pipe' for all streams when capturing output, otherwise 'inherit'
      // to show real-time output to user during long-running commands
      stdio: options.captureOutput ? ['pipe', 'pipe', 'pipe'] : 'inherit',
    });
    return {
      returncode: 0,
      stdout: stdout || '',
      stderr: '',
    };
  } catch (error) {
    // execSync throws on non-zero exit codes; extract status and output
    // from the error object for consistent return format
    return {
      returncode: error.status || -1,
      stdout: error.stdout ? error.stdout.toString() : '',
      stderr: error.stderr ? error.stderr.toString() : error.message,
    };
  }
}

/**
 * Generate TypeDoc API documentation.
 *
 * Validates that the 'typedoc' script is available in package.json, then runs
 * TypeDoc via the detected package manager to generate native HTML documentation.
 * TypeDoc's cleanOutputDir option handles cleanup of stale files automatically.
 *
 * Uses shared utilities from wsd_utils.js for package manager detection and
 * script availability checking to ensure consistent behavior across WSD tools.
 * @param {string[]} [checkDirs] - Directories to document (optional, reads from config if not provided)
 * @returns {boolean} True if documentation generated successfully, false on any error
 */
function generateTypedocDocs(checkDirs) {
  // If checkDirs not provided as parameter, read from configuration
  if (!checkDirs) {
    checkDirs = getCheckDirs();
    if (checkDirs.length === 0) {
      console.log('Skipping TypeDoc documentation: no source directories configured.');
      return true; // Return true to indicate graceful skip, not an error
    }
  }

  console.log('Generating TypeDoc API documentation...');

  // Check if typedoc script is available in package.json
  if (!isScriptAvailable('typedoc')) {
    console.error('');
    console.error('Error: "typedoc" script not found in package.json.');
    console.error('');
    console.error('TypeDoc must be configured as a package.json script to generate documentation.');
    console.error('');
    console.error('To fix this issue:');
    console.error('');
    console.error('1. Install TypeDoc as a dev dependency:');
    console.error('   npm install typedoc --save-dev');
    console.error('   # or: pnpm add -D typedoc');
    console.error('   # or: yarn add --dev typedoc');
    console.error('   # or: bun add -d typedoc');
    console.error('');
    console.error('2. Add a "typedoc" script to your package.json:');
    console.error('   "scripts": {');
    console.error('     "typedoc": "typedoc"');
    console.error('   }');
    console.error('');
    process.exit(1);
  }

  // Ensure reports directory exists for output
  if (!fs.existsSync(REPORTS_DIR)) {
    fs.mkdirSync(REPORTS_DIR, { recursive: true });
  }

  // Detect package manager (checkDirs already validated by caller)
  const packageManager = detectPackageManager();
  if (packageManager === null) {
    console.error('Error: No package manager lock file found.');
    console.error('Create one by running: pnpm install, npm install, yarn install, or bun install');
    process.exit(1);
  }

  // Build command using package manager script pattern with directories as entry points
  const typedocCommand = [packageManager, 'run', 'typedoc', '--', ...checkDirs];
  const result = runCommand(typedocCommand, { captureOutput: true, cwd: PROJECT_ROOT });

  if (result.returncode === 0) {
    console.log(`TypeDoc successfully generated HTML documentation in: ${OUTPUT_DIR}`);
    if (result.stdout) {
      console.log(`TypeDoc Output:\n${result.stdout}`);
    }
    if (result.stderr) {
      console.log(`TypeDoc Stderr (Info/Warnings):\n${result.stderr}`);
    }
    return true;
  } else {
    console.error(`Error generating TypeDoc documentation (return code: ${result.returncode}):`);
    if (result.stdout) console.error(`--- TypeDoc STDOUT ---\n${result.stdout}`);
    if (result.stderr) console.error(`--- TypeDoc STDERR ---\n${result.stderr}`);
    console.error('Failed to generate TypeDoc documentation.');
    return false;
  }
}

/**
 * Main function to generate TypeDoc documentation.
 *
 * Detects project language and exits gracefully for JavaScript-only projects,
 * since TypeDoc is specifically designed for TypeScript and requires .ts files.
 */
function main() {
  // Check for configured source directories first
  const checkDirs = getCheckDirs();
  if (checkDirs.length === 0) {
    console.log('Skipping TypeDoc documentation: no source directories configured.');
    return;
  }

  // Detect project languages - TypeDoc requires TypeScript
  const languages = detectProjectLanguages();

  if (!languages.includes('typescript')) {
    console.log('');
    console.log('TypeDoc Generator: Skipping - TypeScript project required');
    console.log('');
    console.log('TypeDoc is a documentation generator specifically designed for TypeScript');
    console.log('projects. It analyzes TypeScript source files and type information to');
    console.log('generate comprehensive API documentation.');
    console.log('');
    if (languages.includes('javascript')) {
      console.log('Detected: JavaScript-only project (no .ts files found)');
      console.log('');
      console.log('For JavaScript projects, consider using JSDoc comments in your source');
      console.log('files and a documentation tool like JSDoc or documentation.js instead.');
    } else {
      console.log('Detected: No package.json found or unable to determine project type.');
    }
    console.log('');
    return;
  }

  if (!generateTypedocDocs(checkDirs)) {
    console.error('\nTypeDoc generation process encountered an error.');
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { generateTypedocDocs };
