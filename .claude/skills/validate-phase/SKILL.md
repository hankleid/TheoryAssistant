---
name: validate-phase
description: "Check a completed analysis phase folder for all required outputs and report pass/fail per criterion"
argument-hint: "<phase number>"
allowed-tools: Read, Bash, Glob, Grep
---
# Validate Phase

Check `analysis/phase_$ARGUMENTS/` for completeness and correctness. Report pass/fail for each criterion below.

## Prerequisites

- `execution_checkpoints.json` — to know what outputs are required for phase $ARGUMENTS
- `analysis/phase_$ARGUMENTS/` — the phase folder to validate

---

## Validation Criteria

### 1. Required files present

Check that all of the following exist in `analysis/phase_$ARGUMENTS/`:

- [ ] `phase_$ARGUMENTS.py` — the phase script
- [ ] `phase_$ARGUMENTS_summary.md` — the phase report
- [ ] `runtime_log.txt` — execution metadata
- [ ] At least one results file (`*_results.json` or `*.csv`)
- [ ] At least one figure file (`*.png`, `*.pdf`, or `*.svg`)

### 2. Summary has numerical content

Open `phase_$ARGUMENTS_summary.md` and verify:
- [ ] Contains at least one numerical result (a number, percentage, or parameter value)
- [ ] Mentions the Python tools from `tools/` that were used
- [ ] Is not a stub (> 200 words)

### 3. Results file has substantive content

Open the results JSON/CSV and verify:
- [ ] Is valid JSON/CSV (parseable)
- [ ] Contains model parameters or fit metrics (not just metadata)
- [ ] Has at least one numeric value

### 4. No convergence failures in runtime_log.txt

Open `runtime_log.txt` and check:
- [ ] No `ERROR` or `FAILED` lines that indicate the script crashed
- [ ] At least one convergence warning (or explicit "converged") logged
- [ ] Execution time recorded

### 5. Cross-check with execution_checkpoints.json

Read `execution_checkpoints.json`, find the entry for `phase_id: $ARGUMENTS`, and verify:
- [ ] The outputs described in the `output` field are present

---

## Report Format

Print a checklist like:

```
Phase $ARGUMENTS Validation
===========================
[PASS] phase_$ARGUMENTS.py exists
[PASS] phase_$ARGUMENTS_summary.md exists
[FAIL] runtime_log.txt missing
...
Summary: X/Y criteria passed
```

If any criterion fails, state what is missing and what command would produce it.
