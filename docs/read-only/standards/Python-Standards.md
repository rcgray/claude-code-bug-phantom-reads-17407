### Python Development Best Practices

#### Tools and Libraries
- Do not use `rye` or `poetry` for managing Python dependencies
- Always work within a virtual environment. Use the command line tool `pyactivate` from the project root directory to activate the virtual environment.
- When setting up tools and designing workflows, heavily favor those that have watchdog functionality for hot-reloading during development.
- Use `ruff` for linting and formatting (includes black and isort functionality)
- Use `mypy` for type checking
- Use `pytest` for testing

#### Command Line Interface
- We are using `uv` to manage our Python dependencies, so please configure your commands accordingly (e.g., `uv sync` or `uv sync --extra dev` to install dependencies, `uv run <script>` to run a script, `uv run pytest` to run tests, etc.).

#### General Python Recommendations
- Use type hints in all Python code
- **ALL functions and methods must have explicit return type annotations** (e.g. `-> None`, `-> str`, `-> list[str]`)
- Ensure that you specify type parameters for generic types (i.e., avoid `ruff` [type-arg] errors)
- **MANDATORY: Type parameters must be lowercase** (e.g. `list[int]` not `List[int]`) - **NEVER use `List`, `Dict`, `Tuple` imports**
- Prefer `Path.open()` over older `open()`. For example, instead of ` with open(model_file) as f:`, use `with model_file.open() as f:`.
- Follow PEP 8 style guidelines
- Keep functions focused and small
- **Document all public functions and classes** - use Google-style docstrings with `Args:`, `Returns:`, and `Raises:` sections where applicable
- **Dataclasses require complete field documentation** - see `Data-Structure-Documentation-Standards.md`
- **Test methods must document ALL parameters** (including pytest fixtures like `tmp_path`, `monkeypatch`, `capsys`) in Args sections with consistent descriptions:
  - `tmp_path: Pytest fixture providing temporary directory for test files`
  - `monkeypatch: Pytest fixture for modifying environment and attributes`
  - `capsys: Pytest fixture for capturing stdout/stderr output`
  - `caplog: Pytest fixture for capturing log messages`
  - Custom fixtures and mocks should describe their specific purpose
- Write tests for new functionality
- Use meaningful variable and function names
- Handle errors gracefully with proper logging
- Use f-strings for string formatting
- Create shebangs as the modern `#!/usr/bin/env python`, NOT the historical `#!/usr/bin/env python3`
