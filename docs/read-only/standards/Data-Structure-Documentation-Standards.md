# Data Structure Documentation Standards

**Date Created:** 2025-09-13
**Last Updated:** 2025-11-05
**Purpose:** Define clear, enforceable standards for data structure field documentation across Python dataclasses and TypeScript interfaces/types

## Overview

This document establishes mandatory documentation standards for structured data types across both Python and TypeScript projects. These standards address a critical gap where data structure fields are often added without corresponding documentation updates, which may not be caught by quality assurance processes.

**Core Principle:** Every field in a data structure must be documented with clear, meaningful descriptions that explain its purpose, constraints, and behavior.

**Applicability:**
- **Python:** Dataclasses, typed dictionaries, and data-carrying classes
- **TypeScript:** Interfaces, types, and classes used for data structures

---

## Python: Dataclass Documentation

### Core Requirements

#### 1. Mandatory Docstring Presence

**Requirement:** Every dataclass MUST have a docstring immediately following the class declaration.

**Rationale:** Docstrings are essential for API documentation generation, IDE support, and developer understanding.

#### 2. Attributes Section Requirement

**Requirement:** Every dataclass docstring MUST include an "Attributes:" section that documents all fields.

**Rationale:** The Attributes section provides a centralized location for field documentation that tools can parse and developers can reference.

#### 3. Complete Field Coverage

**Requirement:** Every field defined in the dataclass MUST be documented in the Attributes section.

**Rationale:** Undocumented fields create confusion about their purpose and usage, leading to maintenance issues and potential misuse.

#### 4. Clear Field Descriptions

**Requirement:** Each field documentation MUST include:
- The field name
- A clear description of what the field represents
- Any important constraints or special values (e.g., "None indicates no limit")

**Rationale:** Clear descriptions prevent misunderstandings and reduce the need for developers to examine implementation details.

### Standard Format (Python)

#### Correct Format Example

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ProviderInfo:
    """Metadata for a provider.

    This class stores configuration and capability information for
    LLM providers supported by the tokenization system.

    Attributes:
        name: Internal name used in CLI and configuration (e.g., "openai")
        display_name: Human-readable name for display (e.g., "OpenAI")
        offline_capability: How the provider works offline:
            - "native": Full offline support with accurate counts
            - "estimate": Falls back to character-based estimates
            - "cached": Works offline if model previously downloaded
            - "none": No offline support
        api_improves_accuracy: Whether an API key provides more accurate counts than estimates
        supports_lineage: Whether provider supports model lineage information display
        requires_file_path_validation: Whether provider requires model file path validation
        description: Optional description for CLI help text
    """
    name: str
    display_name: str
    offline_capability: str = "estimate"
    api_improves_accuracy: bool = False
    supports_lineage: bool = False
    requires_file_path_validation: bool = False
    description: Optional[str] = None
```

### Common Anti-Patterns (Python)

#### Anti-Pattern 1: Missing Attributes Section

```python
# INCORRECT - No Attributes section
@dataclass
class InputItem:
    """Represents a single input to be processed."""
    path: str
    content: str
    error: Optional[str] = None
```

#### Anti-Pattern 2: Incomplete Field Documentation

```python
# INCORRECT - Missing documentation for some fields
@dataclass
class ProviderInfo:
    """Metadata for a provider.

    Attributes:
        name: Internal provider name
        display_name: Display name for UI
        # supports_lineage field is not documented!
        # requires_file_path_validation field is not documented!
    """
    name: str
    display_name: str
    supports_lineage: bool = False
    requires_file_path_validation: bool = False
```

#### Anti-Pattern 3: Vague or Unhelpful Descriptions

```python
# INCORRECT - Descriptions don't add value
@dataclass
class Config:
    """Configuration settings.

    Attributes:
        provider: The provider  # Just repeats the field name
        model: Model to use     # Too vague
        offline: Boolean value  # Doesn't explain what true/false means
    """
    provider: str
    model: str
    offline: bool
```

### Field Documentation Guidelines (Python)

#### For Boolean Fields

Always explain what `True` and `False` mean:

```python
# GOOD
supports_revision: Whether provider supports model revision/version specification
api_improves_accuracy: Whether an API key provides more accurate counts than estimates

# BAD
supports_revision: Revision support flag
api_improves_accuracy: API accuracy boolean
```

#### For Enum or Limited Value Fields

Document the possible values and their meanings:

```python
# GOOD
offline_capability: How the provider works offline:
    - "native": Full offline support with accurate counts
    - "estimate": Falls back to character-based estimates
    - "cached": Works offline if model previously downloaded
    - "none": No offline support

# BAD
offline_capability: Offline capability type
```

#### For Optional Fields

Explain what `None` represents:

```python
# GOOD
description: Optional description for CLI help text. None indicates no custom description.
error: Error message if processing failed. None indicates successful processing.

# BAD
description: Optional[str]
error: Optional error message
```

#### For Collection Fields

Describe what the collection contains and any constraints:

```python
# GOOD
model_source_names: Names used in external model data sources for provider matching
providers: Dictionary mapping provider names to their configuration objects

# BAD
model_source_names: List of names
providers: Provider dictionary
```

---

## TypeScript: Interface/Type Documentation

### Core Requirements

#### 1. Mandatory TSDoc Presence

**Requirement:** Every exported interface, type, and class MUST have TSDoc documentation.

**Rationale:** TSDoc provides standardized documentation that IDEs, documentation generators, and developers can use to understand the structure's purpose.

#### 2. Property Documentation Requirement

**Requirement:** Every property in an interface, type, or class MUST be documented with a TSDoc comment.

**Rationale:** Property-level documentation clarifies the purpose and constraints of each field, preventing misuse and maintenance issues.

#### 3. Complete Property Coverage

**Requirement:** Every property defined in the structure MUST have documentation.

**Rationale:** Undocumented properties create ambiguity about their purpose, valid values, and usage patterns.

#### 4. Clear Property Descriptions

**Requirement:** Each property documentation MUST include:
- A clear description of what the property represents
- Valid values or constraints (for enums, unions, or constrained types)
- Meaning of optional/undefined values

**Rationale:** Clear descriptions reduce cognitive load and prevent incorrect usage.

### Standard Format (TypeScript)

#### Correct Format Example

```typescript
/**
 * Metadata for a provider.
 *
 * This interface stores configuration and capability information for
 * LLM providers supported by the tokenization system.
 */
export interface ProviderInfo {
    /** Internal name used in CLI and configuration (e.g., "openai") */
    name: string;

    /** Human-readable name for display (e.g., "OpenAI") */
    displayName: string;

    /**
     * How the provider works offline.
     * - "native": Full offline support with accurate counts
     * - "estimate": Falls back to character-based estimates
     * - "cached": Works offline if model previously downloaded
     * - "none": No offline support
     */
    offlineCapability: 'native' | 'estimate' | 'cached' | 'none';

    /** Whether an API key provides more accurate counts than estimates */
    apiImprovesAccuracy: boolean;

    /** Whether provider supports model lineage information display */
    supportsLineage: boolean;

    /** Whether provider requires model file path validation */
    requiresFilePathValidation: boolean;

    /** Optional description for CLI help text */
    description?: string;
}
```

### Common Anti-Patterns (TypeScript)

#### Anti-Pattern 1: Missing TSDoc

```typescript
// INCORRECT - No TSDoc
export interface InputItem {
    path: string;
    content: string;
    error?: string;
}
```

#### Anti-Pattern 2: Incomplete Property Documentation

```typescript
// INCORRECT - Some properties lack documentation
/**
 * Metadata for a provider.
 */
export interface ProviderInfo {
    /** Internal provider name */
    name: string;
    displayName: string; // Missing documentation!
    supportsLineage: boolean; // Missing documentation!
}
```

#### Anti-Pattern 3: Vague or Unhelpful Descriptions

```typescript
// INCORRECT - Descriptions don't add value
/**
 * Configuration settings.
 */
export interface Config {
    /** The provider */ // Just repeats the property name
    provider: string;

    /** Model to use */ // Too vague
    model: string;

    /** Boolean value */ // Doesn't explain what true/false means
    offline: boolean;
}
```

### Field Documentation Guidelines (TypeScript)

#### For Boolean Properties

Always explain what `true` and `false` mean:

```typescript
// GOOD
/** Whether provider supports model revision/version specification */
supportsRevision: boolean;

/** Whether an API key provides more accurate counts than estimates */
apiImprovesAccuracy: boolean;

// BAD
/** Revision support flag */
supportsRevision: boolean;

/** API accuracy boolean */
apiImprovesAccuracy: boolean;
```

#### For Union or Literal Types

Document the possible values and their meanings:

```typescript
// GOOD
/**
 * How the provider works offline.
 * - "native": Full offline support with accurate counts
 * - "estimate": Falls back to character-based estimates
 * - "cached": Works offline if model previously downloaded
 * - "none": No offline support
 */
offlineCapability: 'native' | 'estimate' | 'cached' | 'none';

// BAD
/** Offline capability type */
offlineCapability: 'native' | 'estimate' | 'cached' | 'none';
```

#### For Optional Properties

Explain what `undefined` represents:

```typescript
// GOOD
/** Optional description for CLI help text. Undefined indicates no custom description. */
description?: string;

/** Error message if processing failed. Undefined indicates successful processing. */
error?: string;

// BAD
/** Optional description */
description?: string;

/** Optional error message */
error?: string;
```

#### For Collection Properties

Describe what the collection contains and any constraints:

```typescript
// GOOD
/** Names used in external model data sources for provider matching */
modelSourceNames: string[];

/** Dictionary mapping provider names to their configuration objects */
providers: Record<string, ProviderConfig>;

// BAD
/** List of names */
modelSourceNames: string[];

/** Provider dictionary */
providers: Record<string, ProviderConfig>;
```

---

## Validation and Enforcement

### Automated Validation

#### Python
The Health Inspector agent validates dataclass documentation using these checks:
1. **AST Parsing**: Parse Python files to identify dataclasses
2. **Docstring Extraction**: Extract and parse class docstrings
3. **Field Mapping**: Map dataclass fields to documented attributes
4. **Gap Detection**: Identify missing or undocumented fields

#### TypeScript
Documentation validation for TypeScript uses:
1. **TSDoc Linting**: Use ESLint plugins to enforce TSDoc presence
2. **Type Analysis**: Analyze TypeScript AST to identify interfaces/types
3. **Property Mapping**: Map interface properties to TSDoc comments
4. **Gap Detection**: Identify missing or incomplete documentation

### Manual Review Points

During code review, verify:
- Field/property descriptions are meaningful and accurate
- Special cases and constraints are documented
- Documentation matches actual field/property behavior
- Examples are provided for complex structures

---

## Migration Strategy

### For Existing Python Dataclasses

1. **Identify Non-Compliant Classes**: Use validation scripts or AST analysis
2. **Prioritize by Usage**: Fix most-used dataclasses first
3. **Add Missing Sections**: Add "Attributes:" sections where missing
4. **Document All Fields**: Ensure every field has documentation
5. **Review and Refine**: Improve vague or unclear descriptions

### For Existing TypeScript Interfaces/Types

1. **Identify Non-Compliant Structures**: Use TSDoc linting
2. **Prioritize by Exposure**: Fix exported/public interfaces first
3. **Add TSDoc Comments**: Add interface-level and property-level comments
4. **Document All Properties**: Ensure every property has documentation
5. **Review and Refine**: Improve vague or unclear descriptions

---

## Integration with Development Workflow

### IDE Support

**Python:**
- Configure IDE inspections to highlight undocumented dataclass fields
- Provide templates for Attributes sections
- Auto-generate field documentation stubs

**TypeScript:**
- Enable TSDoc IntelliSense and validation
- Configure IDE to highlight undocumented properties
- Use TSDoc auto-completion for property comments

### Documentation Generation

**Python:**
- Ensure Sphinx or other tools parse Attributes sections correctly
- Generate API documentation from dataclass docstrings
- Flag incomplete documentation during generation

**TypeScript:**
- Use TypeDoc or similar tools to generate API documentation
- Ensure TSDoc comments are included in generated docs
- Flag incomplete documentation during generation

---

## Example Refactoring Patterns

> **Note:** The following examples are drawn from reference projects to illustrate principles. Replace domain-specific references with your own project's concepts.

### Python Example: Adding Missing Documentation

**Before (incomplete documentation):**
```python
@dataclass
class ProviderInfo:
    """Metadata for a provider."""
    name: str
    display_name: str
    supports_lineage: bool = False
    requires_file_path_validation: bool = False
```

**After (complete documentation):**
```python
@dataclass
class ProviderInfo:
    """Metadata for a provider.

    Attributes:
        name: Internal name used in CLI and configuration
        display_name: Human-readable name for display
        supports_lineage: Whether provider supports model lineage information display
        requires_file_path_validation: Whether provider requires model file path validation
    """
    name: str
    display_name: str
    supports_lineage: bool = False
    requires_file_path_validation: bool = False
```

### TypeScript Example: Adding Missing Documentation

**Before (incomplete documentation):**
```typescript
export interface ProviderInfo {
    name: string;
    displayName: string;
    supportsLineage: boolean;
    requiresFilePathValidation: boolean;
}
```

**After (complete documentation):**
```typescript
/**
 * Metadata for a provider.
 */
export interface ProviderInfo {
    /** Internal name used in CLI and configuration */
    name: string;

    /** Human-readable name for display */
    displayName: string;

    /** Whether provider supports model lineage information display */
    supportsLineage: boolean;

    /** Whether provider requires model file path validation */
    requiresFilePathValidation: boolean;
}
```

### Python Example: Improving Vague Documentation

**Before (vague descriptions):**
```python
@dataclass
class InputItem:
    """Represents a single input to be processed.

    Attributes:
        path: The path
        type: The type
        content: The content
        error: Error if any
    """
    path: str
    type: InputType
    content: str
    error: Optional[str] = None
```

**After (clear descriptions):**
```python
@dataclass
class InputItem:
    """Represents a single input to be processed.

    Attributes:
        path: Original input path or string provided by user
        type: Type of input (STRING, FILE, DIRECTORY, or STDIN)
        content: Actual content to tokenize
        error: Error message if processing failed. None indicates successful processing.
    """
    path: str
    type: InputType
    content: str
    error: Optional[str] = None
```

### TypeScript Example: Improving Vague Documentation

**Before (vague descriptions):**
```typescript
/**
 * Represents a single input to be processed.
 */
export interface InputItem {
    /** The path */
    path: string;

    /** The type */
    type: InputType;

    /** The content */
    content: string;

    /** Error if any */
    error?: string;
}
```

**After (clear descriptions):**
```typescript
/**
 * Represents a single input to be processed.
 */
export interface InputItem {
    /** Original input path or string provided by user */
    path: string;

    /** Type of input (STRING, FILE, DIRECTORY, or STDIN) */
    type: InputType;

    /** Actual content to process */
    content: string;

    /** Error message if processing failed. Undefined indicates successful processing. */
    error?: string;
}
```

---

## Conclusion

These standards ensure that all data structures are properly documented across both Python and TypeScript projects, making codebases more maintainable and reducing the likelihood of documentation gaps going unnoticed. The Health Inspector agent and documentation linting tools enforce these standards as part of regular quality assurance, treating documentation completeness as equal in importance to type safety and test coverage.

By following these standards, we prevent "crises of confidence" in quality assurance processes that occur when undocumented fields are added without detection. Documentation is not an afterthought but an integral part of code quality.

**Key Takeaways:**
- Every data structure field must be documented
- Descriptions must be clear and meaningful, not just repetitions of field names
- Boolean fields must explain what true/false or True/False mean
- Optional/nullable fields must explain what None/undefined represents
- Enums and unions must document all possible values
- Collections must describe their contents and constraints
