# Type Error Fixes Required

## Problem
The test functions use `*args: object` in their side_effect mock functions, which prevents mypy from understanding that `args[0]` is indexable and has a length.

## Solution
Change the type annotation from `*args: object` to `*args: Any` to allow mypy to accept the indexing operations.

## Lines to Fix
- Line 883: `def side_effect(*args: object, **kwargs: object) -> Mock:`
- Line 950: `def side_effect(*args: object, **kwargs: object) -> Mock:`
- Line 999: Similar pattern
- Line 1053: Similar pattern
- Line 1100: Similar pattern
- Line 1159: Similar pattern

All should change from `*args: object` to `*args: Any`.
