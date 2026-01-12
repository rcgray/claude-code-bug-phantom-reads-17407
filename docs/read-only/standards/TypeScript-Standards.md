# TypeScript Development Best Practices

## General Guidelines

- **`tsconfig.json`**: Respect project's TypeScript compiler options (`strict`, `noImplicitAny`, `strictNullChecks`, etc.).
- **Linting & Formatting**: Adhere to project ESLint & Prettier configs. Format/lint regularly.

## Typing

- **Avoid `any`**: Minimize `any`; prefer specific types or `unknown`.
- **`unknown` Safely**: With `unknown`, always perform type checks (e.g., `typeof`, `instanceof`, type guards) before use.
- **Explicit Types**: Prefer explicit types for function params, return types, and variable declarations, especially for exported/public members and complex data structures. Type inference is fine for obvious local variables.
- **`interface` vs `type`**: Use `interface` for object shapes (can merge, use with `implements`). Use `type` for unions, intersections, primitives, tuples, mapped/conditional types.
- **Utility Types**: Leverage built-in utility types (`Partial`, `Readonly`, `Pick`, `Omit`, `Record`, etc.).
- **Readonly**: Use `readonly` properties and `Readonly<T>`/`ReadonlyArray<T>` for immutability.
- **Const Assertions**: Use `as const` for literal types and immutability (e.g., `const CMD = 'INIT' as const;`).

## Tools and Libraries
- Many TypeScript projects have a Node.js server component. Use `pnpm` instead of `npm`.

## Code Style & Structure

- **Naming**: `camelCase` (vars, fns), `PascalCase` (classes, types, enums, components), `UPPER_SNAKE_CASE` (constants). Avoid `I` prefix for interfaces unless a strict project convention.
- **File Naming**: Use `PascalCase` for TypeScript files (e.g., `UserService.ts`, `ProjectManager.ts`). Never use `camelCase` (`userService.ts`) or `kebab-case` (`user-service.ts`) for `.ts`/`.tsx` files. File names should reflect their primary export and architectural role: use `Manager` suffix for workspace coordinators, `DataManager` for data layer with state, `Service` for stateless operations, `Utilities` for pure functions.
- **Modularity**: Use ES modules (`import`/`export`). Keep files focused (single responsibility).
- **Exports**: Export only necessary items. Prefer named exports; use default exports sparingly.
- **Constants**: Define constants for magic strings/numbers; export if shared (e.g., `shared/constants.ts`).

## Modern Features & Practices

- **`let`/`const`**: Prefer `const`; use `let` only for reassignment. Avoid `var`.
- **`async`/`await`**: Use for Promises to improve readability.
- **Error Handling**: Use `try...catch` for sync/async errors. Handle Promise rejections. Consider custom Error classes for specific scenarios.
- **Nullish Coalescing (`??`)**: Use `??` for `null` or `undefined` defaults (vs `||` for any falsy).
- **Optional Chaining (`?.`)**: Use `?.` for safe access on nullable objects/functions.

## Readability & Maintainability

- **Comprehensive TypeDoc (`/** ... */`)**:
    - **File-Level**: Every `.ts`/`.tsx` file must start with a TypeDoc block:
      ```typescript
      /**
       * @file Module purpose, responsibilities, and role.
       * @see {@link path/to/relevant/doc.md} (If applicable)
       */
      ```
    - **All Exports**: Document all exported functions, classes, types, interfaces, enums, constants.
    - **Functions/Methods**:
        - Summary, `@async` (if applicable), `@param`, `@returns` (incl. `null`/error cases), `@throws`, `{@link}`, side effects.
        - Example:
          ```typescript
          /**
           * Brief summary of what it does.
           * @param {string} id - Identifier for the item.
           * @returns {Promise<Item | null>} The item or null if not found.
           * @remarks Updates last access time.
           */
          async function getItem(id: string): Promise<Item | null> { /* ... */ }
          ```
    - **Types/Interfaces/Enums/Constants**: Document with `@description`. For objects, comment each property:
      ```typescript
      /** @description Defines user preferences. */
      interface UserPrefs {
        /** @description UI theme selection. */
        theme: 'light' | 'dark';
      }
      ```
    - **Internal Helpers**: Use JSDoc for complex internal logic; consider `@internal`.

- **Data Schemas & Validation (e.g., Zod)**:
    - For serialized data (JSON, API, IPC), define schemas (e.g., Zod) for validation.
    - Infer TS types from schemas: `type MyData = z.infer<typeof MyDataSchema>;`.
    - Document schemas and their properties clearly within the schema definition:
      ```typescript
      /** @description Zod schema for MyData. */
      export const MyDataSchema = z.object({
        /** @description Unique identifier. */
        id: z.string().uuid(),
        /** @description Optional user comment. */
        comment: z.string().optional(),
      });
      /** @description TS Type for MyData. @see {@link MyDataSchema} */
      export type MyData = z.infer<typeof MyDataSchema>;
      ```

- **Function Length**: Keep functions concise, focused on a single task. Refactor large functions.
- **Code Comments**: Use `//` or `/* ... */` to explain *why* (non-obvious logic, workarounds), not *what*.

## React/Frontend Specific (If Applicable)

- **Component Props**: Define explicit `interface` or `type` for component props.
- **Hooks**: Follow Rules of Hooks. Use built-in hooks effectively.
- **State Management**: Adhere to project's state management patterns (see `docs/core/Frontend-Technical-Spec.md`).
- **CSS/Styling**: Follow project styling conventions (see `docs/core/Frontend-Design.md`).

Following these practices helps build a robust, maintainable, and type-safe TypeScript codebase.
