--- STDOUT ---
============================================================
Starting Health Check...
Checking directories: src tests
Running in SAFE mode (use --aggressive for more fixes)
============================================================

Health Check: Verifying development dependencies...
Health Check: Running Dependency verification...
Health Check: Dependency verification completed successfully.

----------------------------------------
Health Check: Running Build validation...
Health Check: Build validation completed successfully.

----------------------------------------
Health Check: Running Type checking (mypy)...
Health Check: Type checking (mypy) completed successfully.
Output:
 Success: no issues found in 6 source files


----------------------------------------
Health Check: Running Security scanning (bandit)...
Health Check: Security scanning (bandit) completed successfully.
Output:
 [95mRun started:2026-01-19 18:39:54.619733+00:00[0m
[95m
Test results:[0m
	No issues identified.
[95m
Code scanned:[0m
	Total lines of code: 1063
	Total lines skipped (#nosec): 0
[95m
Run metrics:[0m
	Total issues (by severity):
		Undefined: 0
		Low: 1
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 1
[95mFiles skipped (0):[0m


----------------------------------------
Health Check: Running Dependency security audit (pip-audit)...
Health Check: Dependency security audit (pip-audit) completed successfully.
Output:
 Name                          Skip Reason
----------------------------- --------------------------------------------------------------------------------------------
claude-code-bug-phantom-reads Dependency not found on PyPI and could not be audited: claude-code-bug-phantom-reads (0.1.0)


----------------------------------------

----------------------------------------
Health Check: Running Linting check (ruff)...
Health Check: Linting check (ruff) completed successfully.
Output:
 All checks passed!


----------------------------------------
Health Check: Running Code formatting check (ruff format)...
Health Check: Code formatting check (ruff format) completed successfully.
Output:
 6 files already formatted


============================================================
HEALTH CHECK SUMMARY
============================================================
Check                Status          Details                  
------------------------------------------------------------
Build Validation     ✅ PASSED                                 
Type Checking        ✅ PASSED                                 
Security Scan        ✅ PASSED                                 
Dependency Audit     ✅ PASSED                                 
Doc Completeness     ✅ PASSED                                 
Linting              ✅ PASSED                                 
Code Formatting      ✅ PASSED                                 
============================================================

✅ Project Health Check completed successfully!
============================================================


--- STDERR ---
