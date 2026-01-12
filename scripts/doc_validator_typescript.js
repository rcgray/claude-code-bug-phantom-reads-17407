/**
 * @file AST-based documentation validator for TypeScript projects.
 *
 * Uses the TypeScript Compiler API to validate that exported interfaces, types,
 * and functions have complete JSDoc documentation according to project standards.
 * This provides semantic validation beyond what TSDoc/TypeDoc syntax checking offers.
 *
 * Validation checks:
 * - Exported interfaces/types have JSDoc comments
 * - Interface/type properties have JSDoc documentation
 * - Boolean properties explain true/false meanings
 * - Exported functions have @param for each parameter
 * - Exported functions have @returns documentation
 */

const ts = require('typescript');
const path = require('path');

/**
 * Validation error severity levels.
 * @typedef {'error' | 'warning'} Severity
 */

/**
 * Represents a single documentation validation error.
 * @typedef {object} ValidationError
 * @property {string} filePath - Path to the file containing the error
 * @property {number} line - Line number where the error occurs
 * @property {number} column - Column number where the error occurs
 * @property {Severity} severity - Error severity level
 * @property {string} code - Error code for categorization (e.g., 'DOC001')
 * @property {string} message - Human-readable error description
 * @property {string} nodeName - Name of the node with the documentation issue
 * @property {string} nodeKind - Kind of node (interface, type, function, property)
 */

/**
 * Validation result containing all errors found during analysis.
 * @typedef {object} ValidationResult
 * @property {ValidationError[]} errors - Array of validation errors found
 * @property {number} filesAnalyzed - Number of files that were analyzed
 * @property {number} interfacesChecked - Number of interfaces checked
 * @property {number} typesChecked - Number of type aliases checked
 * @property {number} functionsChecked - Number of functions checked
 */

/**
 * Error codes for documentation validation issues.
 *
 * DOC001-DOC009: Interface/Type level errors
 * DOC010-DOC019: Property level errors
 * DOC020-DOC029: Function level errors
 * DOC030-DOC039: Parameter level errors
 * DOC040-DOC049: Return type errors
 */
const ErrorCodes = {
  /** Exported interface missing JSDoc comment */
  INTERFACE_NO_DOC: 'DOC001',
  /** Exported type alias missing JSDoc comment */
  TYPE_NO_DOC: 'DOC002',
  /** Interface/type property missing JSDoc comment */
  PROPERTY_NO_DOC: 'DOC010',
  /** Boolean property doesn't explain true/false meaning */
  BOOLEAN_NO_EXPLANATION: 'DOC011',
  /** Union type property doesn't document all values */
  UNION_NO_VALUES_DOC: 'DOC012',
  /** Optional property doesn't explain undefined meaning */
  OPTIONAL_NO_UNDEFINED_DOC: 'DOC013',
  /** Exported function missing JSDoc comment */
  FUNCTION_NO_DOC: 'DOC020',
  /** Function parameter missing @param documentation */
  PARAM_NO_DOC: 'DOC030',
  /** Function missing @returns documentation */
  RETURN_NO_DOC: 'DOC040',
};

/**
 * Validates TypeScript documentation using the Compiler API.
 *
 * Performs AST-based analysis to ensure exported interfaces, types, and functions
 * have complete documentation according to project standards.
 */
class DocumentationValidator {
  /** @type {ts.Program} */
  program;

  /** @type {ts.TypeChecker} */
  checker;

  /** @type {ValidationError[]} */
  errors = [];

  /** @type {string} */
  projectBasePath;

  /** @type {number} */
  interfacesChecked = 0;

  /** @type {number} */
  typesChecked = 0;

  /** @type {number} */
  functionsChecked = 0;

  /** @type {number} */
  filesAnalyzed = 0;

  /**
   * Creates a new DocumentationValidator instance.
   * @param {string} configPath - Path to tsconfig.json file
   * @throws {Error} If tsconfig.json cannot be read or parsed
   */
  constructor(configPath) {
    const config = ts.readConfigFile(configPath, ts.sys.readFile);
    if (config.error) {
      throw new Error(
        `Failed to read tsconfig.json: ${ts.flattenDiagnosticMessageText(config.error.messageText, '\n')}`
      );
    }

    const parsedConfig = ts.parseJsonConfigFileContent(
      config.config,
      ts.sys,
      path.dirname(configPath)
    );

    this.projectBasePath = path.dirname(configPath);
    this.program = ts.createProgram(parsedConfig.fileNames, parsedConfig.options);
    this.checker = this.program.getTypeChecker();
  }

  /**
   * Validates all source files in the program.
   * @param {string[]} [includeDirectories] - Optional list of directories to include
   * @returns {ValidationResult} Results of the validation
   */
  validate(includeDirectories) {
    this.errors = [];
    this.interfacesChecked = 0;
    this.typesChecked = 0;
    this.functionsChecked = 0;
    this.filesAnalyzed = 0;

    for (const sourceFile of this.program.getSourceFiles()) {
      if (sourceFile.isDeclarationFile || sourceFile.fileName.includes('node_modules')) {
        continue;
      }

      const relativeFilePath = path
        .relative(this.projectBasePath, sourceFile.fileName)
        .replace(/\\/g, '/');

      // Apply directory filtering if specified
      if (includeDirectories && includeDirectories.length > 0) {
        const shouldInclude = includeDirectories.some((dir) => {
          const normalizedDir = dir.replace(/\\/g, '/');
          return (
            relativeFilePath.startsWith(normalizedDir + '/') || relativeFilePath === normalizedDir
          );
        });

        if (!shouldInclude) {
          continue;
        }
      }

      this.filesAnalyzed++;
      this.validateSourceFile(sourceFile, relativeFilePath);
    }

    return {
      errors: this.errors,
      filesAnalyzed: this.filesAnalyzed,
      interfacesChecked: this.interfacesChecked,
      typesChecked: this.typesChecked,
      functionsChecked: this.functionsChecked,
    };
  }

  /**
   * Validates a single source file.
   * @param {ts.SourceFile} sourceFile - The source file to validate
   * @param {string} relativeFilePath - Path relative to project root
   */
  validateSourceFile(sourceFile, relativeFilePath) {
    ts.forEachChild(sourceFile, (node) => {
      if (ts.isInterfaceDeclaration(node) && this.isExported(node)) {
        this.validateInterface(node, sourceFile, relativeFilePath);
      } else if (ts.isTypeAliasDeclaration(node) && this.isExported(node)) {
        this.validateTypeAlias(node, sourceFile, relativeFilePath);
      } else if (ts.isFunctionDeclaration(node) && node.name && this.isExported(node)) {
        this.validateFunction(node, sourceFile, relativeFilePath);
      }
    });
  }

  /**
   * Checks if a node has an export modifier.
   * @param {ts.Node} node - The node to check
   * @returns {boolean} True if the node is exported
   */
  isExported(node) {
    if (!ts.canHaveModifiers(node)) {
      return false;
    }
    const modifiers = ts.getModifiers(node);
    if (!modifiers) {
      return false;
    }
    return modifiers.some((mod) => mod.kind === ts.SyntaxKind.ExportKeyword);
  }

  /**
   * Validates an exported interface declaration.
   * @param {ts.InterfaceDeclaration} node - The interface node
   * @param {ts.SourceFile} sourceFile - The containing source file
   * @param {string} filePath - Path relative to project root
   */
  validateInterface(node, sourceFile, filePath) {
    this.interfacesChecked++;
    const name = node.name.getText();
    const jsDoc = this.getJSDocComment(node);

    // Check interface has JSDoc
    if (!jsDoc) {
      this.addError({
        filePath,
        line: this.getLineNumber(node, sourceFile),
        column: this.getColumnNumber(node, sourceFile),
        severity: 'error',
        code: ErrorCodes.INTERFACE_NO_DOC,
        message: `Exported interface '${name}' is missing JSDoc documentation`,
        nodeName: name,
        nodeKind: 'interface',
      });
    }

    // Validate each property
    node.members.forEach((member) => {
      if (ts.isPropertySignature(member) && member.name) {
        this.validateProperty(member, sourceFile, filePath, name);
      }
    });
  }

  /**
   * Validates an exported type alias declaration.
   * @param {ts.TypeAliasDeclaration} node - The type alias node
   * @param {ts.SourceFile} sourceFile - The containing source file
   * @param {string} filePath - Path relative to project root
   */
  validateTypeAlias(node, sourceFile, filePath) {
    this.typesChecked++;
    const name = node.name.getText();
    const jsDoc = this.getJSDocComment(node);

    // Check type alias has JSDoc
    if (!jsDoc) {
      this.addError({
        filePath,
        line: this.getLineNumber(node, sourceFile),
        column: this.getColumnNumber(node, sourceFile),
        severity: 'error',
        code: ErrorCodes.TYPE_NO_DOC,
        message: `Exported type '${name}' is missing JSDoc documentation`,
        nodeName: name,
        nodeKind: 'type',
      });
    }

    // If it's an object type literal, validate its properties
    if (ts.isTypeLiteralNode(node.type)) {
      node.type.members.forEach((member) => {
        if (ts.isPropertySignature(member) && member.name) {
          this.validateProperty(member, sourceFile, filePath, name);
        }
      });
    }
  }

  /**
   * Validates a property signature within an interface or type.
   * @param {ts.PropertySignature} node - The property node
   * @param {ts.SourceFile} sourceFile - The containing source file
   * @param {string} filePath - Path relative to project root
   * @param {string} parentName - Name of the containing interface/type
   */
  validateProperty(node, sourceFile, filePath, parentName) {
    const propName = node.name.getText();
    const jsDoc = this.getJSDocComment(node);
    const jsDocText = jsDoc ? this.getJSDocText(jsDoc) : '';

    // Check property has JSDoc
    if (!jsDoc) {
      this.addError({
        filePath,
        line: this.getLineNumber(node, sourceFile),
        column: this.getColumnNumber(node, sourceFile),
        severity: 'error',
        code: ErrorCodes.PROPERTY_NO_DOC,
        message: `Property '${propName}' in '${parentName}' is missing JSDoc documentation`,
        nodeName: `${parentName}.${propName}`,
        nodeKind: 'property',
      });
      return; // Skip further checks if no JSDoc at all
    }

    // Check boolean properties explain true/false
    if (node.type && this.isBooleanType(node.type)) {
      if (!this.hasBooleanExplanation(jsDocText)) {
        this.addError({
          filePath,
          line: this.getLineNumber(node, sourceFile),
          column: this.getColumnNumber(node, sourceFile),
          severity: 'warning',
          code: ErrorCodes.BOOLEAN_NO_EXPLANATION,
          message: `Boolean property '${propName}' in '${parentName}' should explain what true and false mean`,
          nodeName: `${parentName}.${propName}`,
          nodeKind: 'property',
        });
      }
    }

    // Check optional properties explain undefined
    if (node.questionToken) {
      if (!this.hasOptionalExplanation(jsDocText)) {
        this.addError({
          filePath,
          line: this.getLineNumber(node, sourceFile),
          column: this.getColumnNumber(node, sourceFile),
          severity: 'warning',
          code: ErrorCodes.OPTIONAL_NO_UNDEFINED_DOC,
          message: `Optional property '${propName}' in '${parentName}' should explain what undefined/omission means`,
          nodeName: `${parentName}.${propName}`,
          nodeKind: 'property',
        });
      }
    }
  }

  /**
   * Validates an exported function declaration.
   * @param {ts.FunctionDeclaration} node - The function node
   * @param {ts.SourceFile} sourceFile - The containing source file
   * @param {string} filePath - Path relative to project root
   */
  validateFunction(node, sourceFile, filePath) {
    this.functionsChecked++;
    const name = node.name ? node.name.getText() : '<anonymous>';
    const jsDoc = this.getJSDocComment(node);
    const jsDocText = jsDoc ? this.getJSDocText(jsDoc) : '';

    // Check function has JSDoc
    if (!jsDoc) {
      this.addError({
        filePath,
        line: this.getLineNumber(node, sourceFile),
        column: this.getColumnNumber(node, sourceFile),
        severity: 'error',
        code: ErrorCodes.FUNCTION_NO_DOC,
        message: `Exported function '${name}' is missing JSDoc documentation`,
        nodeName: name,
        nodeKind: 'function',
      });
      return; // Skip further checks if no JSDoc at all
    }

    // Check each parameter has @param
    node.parameters.forEach((param) => {
      const paramName = param.name.getText();
      if (!this.hasParamDoc(jsDocText, paramName)) {
        this.addError({
          filePath,
          line: this.getLineNumber(param, sourceFile),
          column: this.getColumnNumber(param, sourceFile),
          severity: 'error',
          code: ErrorCodes.PARAM_NO_DOC,
          message: `Parameter '${paramName}' in function '${name}' is missing @param documentation`,
          nodeName: `${name}(${paramName})`,
          nodeKind: 'parameter',
        });
      }
    });

    // Check for @returns if function has non-void return type
    if (node.type && !this.isVoidType(node.type)) {
      if (!this.hasReturnsDoc(jsDocText)) {
        this.addError({
          filePath,
          line: this.getLineNumber(node, sourceFile),
          column: this.getColumnNumber(node, sourceFile),
          severity: 'error',
          code: ErrorCodes.RETURN_NO_DOC,
          message: `Function '${name}' is missing @returns documentation`,
          nodeName: name,
          nodeKind: 'function',
        });
      }
    }
  }

  /**
   * Gets the JSDoc comment for a node.
   * @param {ts.Node} node - The node to get JSDoc for
   * @returns {ts.JSDoc | undefined} The JSDoc comment, or undefined if none
   */
  getJSDocComment(node) {
    const jsDocs = ts.getJSDocCommentsAndTags(node);
    for (const doc of jsDocs) {
      if (ts.isJSDoc(doc)) {
        return doc;
      }
    }
    return undefined;
  }

  /**
   * Extracts the text content from a JSDoc comment.
   * @param {ts.JSDoc} jsDoc - The JSDoc node
   * @returns {string} The full text of the JSDoc comment
   */
  getJSDocText(jsDoc) {
    return jsDoc.getFullText();
  }

  /**
   * Checks if a type node represents a boolean type.
   * @param {ts.TypeNode} typeNode - The type node to check
   * @returns {boolean} True if the type is boolean
   */
  isBooleanType(typeNode) {
    if (typeNode.kind === ts.SyntaxKind.BooleanKeyword) {
      return true;
    }
    // Check for union types that include boolean
    if (ts.isUnionTypeNode(typeNode)) {
      return typeNode.types.some((t) => t.kind === ts.SyntaxKind.BooleanKeyword);
    }
    return false;
  }

  /**
   * Checks if a type node represents a void type.
   * @param {ts.TypeNode} typeNode - The type node to check
   * @returns {boolean} True if the type is void
   */
  isVoidType(typeNode) {
    return (
      typeNode.kind === ts.SyntaxKind.VoidKeyword ||
      typeNode.kind === ts.SyntaxKind.UndefinedKeyword
    );
  }

  /**
   * Checks if JSDoc text contains an explanation of true/false meaning.
   * @param {string} jsDocText - The JSDoc text to check
   * @returns {boolean} True if boolean meaning is explained
   */
  hasBooleanExplanation(jsDocText) {
    const lowerText = jsDocText.toLowerCase();
    // Check for common patterns that explain boolean meaning
    return (
      (lowerText.includes('true') && lowerText.includes('false')) ||
      lowerText.includes('when enabled') ||
      lowerText.includes('when disabled') ||
      lowerText.includes('if set') ||
      lowerText.includes('whether')
    );
  }

  /**
   * Checks if JSDoc text contains an explanation of optional/undefined meaning.
   * @param {string} jsDocText - The JSDoc text to check
   * @returns {boolean} True if optional meaning is explained
   */
  hasOptionalExplanation(jsDocText) {
    const lowerText = jsDocText.toLowerCase();
    return (
      lowerText.includes('optional') ||
      lowerText.includes('if not provided') ||
      lowerText.includes('if omitted') ||
      lowerText.includes('defaults to') ||
      lowerText.includes('undefined')
    );
  }

  /**
   * Checks if JSDoc text contains a @param tag for a specific parameter.
   * @param {string} jsDocText - The JSDoc text to check
   * @param {string} paramName - The parameter name to look for
   * @returns {boolean} True if @param documentation exists
   */
  hasParamDoc(jsDocText, paramName) {
    const paramRegex = new RegExp(`@param\\s+(?:\\{[^}]+\\}\\s+)?${paramName}\\b`, 'i');
    return paramRegex.test(jsDocText);
  }

  /**
   * Checks if JSDoc text contains a @returns tag.
   * @param {string} jsDocText - The JSDoc text to check
   * @returns {boolean} True if @returns documentation exists
   */
  hasReturnsDoc(jsDocText) {
    return /@returns?\b/i.test(jsDocText);
  }

  /**
   * Gets the line number for a node.
   * @param {ts.Node} node - The node to get line number for
   * @param {ts.SourceFile} sourceFile - The containing source file
   * @returns {number} The 1-indexed line number
   */
  getLineNumber(node, sourceFile) {
    const { line } = sourceFile.getLineAndCharacterOfPosition(node.getStart());
    return line + 1; // Convert to 1-indexed
  }

  /**
   * Gets the column number for a node.
   * @param {ts.Node} node - The node to get column number for
   * @param {ts.SourceFile} sourceFile - The containing source file
   * @returns {number} The 1-indexed column number
   */
  getColumnNumber(node, sourceFile) {
    const { character } = sourceFile.getLineAndCharacterOfPosition(node.getStart());
    return character + 1; // Convert to 1-indexed
  }

  /**
   * Adds a validation error to the results.
   * @param {ValidationError} error - The error to add
   */
  addError(error) {
    this.errors.push(error);
  }
}

/**
 * Formats validation results for console output.
 * @param {ValidationResult} result - The validation result to format
 * @returns {string} Formatted output string
 */
function formatResults(result) {
  let output = '';

  // Group errors by file
  const errorsByFile = new Map();
  for (const error of result.errors) {
    if (!errorsByFile.has(error.filePath)) {
      errorsByFile.set(error.filePath, []);
    }
    errorsByFile.get(error.filePath).push(error);
  }

  // Output errors grouped by file
  for (const [filePath, errors] of errorsByFile) {
    output += `\n${filePath}\n`;
    for (const error of errors) {
      const icon = error.severity === 'error' ? '✗' : '⚠';
      output += `  ${error.line}:${error.column}  ${icon} ${error.code}  ${error.message}\n`;
    }
  }

  // Summary
  const errorCount = result.errors.filter((e) => e.severity === 'error').length;
  const warningCount = result.errors.filter((e) => e.severity === 'warning').length;

  output += '\n' + '─'.repeat(60) + '\n';
  output += `Documentation Validation Summary\n`;
  output += `─`.repeat(60) + '\n';
  output += `Files analyzed:     ${result.filesAnalyzed}\n`;
  output += `Interfaces checked: ${result.interfacesChecked}\n`;
  output += `Types checked:      ${result.typesChecked}\n`;
  output += `Functions checked:  ${result.functionsChecked}\n`;
  output += `─`.repeat(60) + '\n';
  output += `Errors:   ${errorCount}\n`;
  output += `Warnings: ${warningCount}\n`;
  output += `─`.repeat(60) + '\n';

  return output;
}

/**
 * Main CLI function for running documentation validation.
 * @returns {Promise<void>}
 */
async function main() {
  const args = process.argv.slice(2);

  // Parse arguments
  let configPath = './tsconfig.json';
  let includeDirectories;
  let jsonOutput = false;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--config' && args[i + 1]) {
      configPath = args[++i];
    } else if (arg.startsWith('--dirs=')) {
      includeDirectories = arg
        .substring(7)
        .split(',')
        .map((d) => d.trim());
    } else if (arg === '--json') {
      jsonOutput = true;
    } else if (arg === '--help' || arg === '-h') {
      console.log('Documentation Validator for TypeScript');
      console.log('\nUsage: node doc_validator_typescript.js [OPTIONS]');
      console.log('\nOptions:');
      console.log('  --config <path>   Path to tsconfig.json (default: ./tsconfig.json)');
      console.log('  --dirs=dir1,dir2  Comma-separated list of directories to check');
      console.log('  --json            Output results as JSON');
      console.log('  --help, -h        Show this help message');
      process.exit(0);
    }
  }

  try {
    console.log('Running documentation validation...');
    if (includeDirectories) {
      console.log(`Checking directories: ${includeDirectories.join(', ')}`);
    }

    const validator = new DocumentationValidator(configPath);
    const result = validator.validate(includeDirectories);

    if (jsonOutput) {
      console.log(JSON.stringify(result, null, 2));
    } else {
      console.log(formatResults(result));
    }

    // Exit with error code if there are errors
    const errorCount = result.errors.filter((e) => e.severity === 'error').length;
    process.exit(errorCount > 0 ? 1 : 0);
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

// Run main if this is the entry point
if (require.main === module) {
  main().catch((error) => {
    console.error('Unexpected error:', error);
    process.exit(1);
  });
}

module.exports = {
  DocumentationValidator,
  ErrorCodes,
  formatResults,
};
