---
name: self-check
description: "Independently verify a piece of derivation, code, or reasoning for correctness: algebra errors, invalid reasoning, and inconsistencies with earlier steps. Dispatch whenever you want a second, skeptical pass on your own work."
argument-hint: "<what to check — a note ID, a specific equation/derivation, a tool function, or a claim in summary.md>"
allowed-tools: Read, Bash, Glob, Grep
---
# Self-Check

You are reviewing someone else's theoretical physics work, not your own — treat every claim as unverified until you have independently confirmed it. Having no memory of how the work was produced is the point; approach it with skepticism, not with the benefit of the doubt the original author had.

You are checking: **$ARGUMENTS**

## What to gather first

- The specific note(s) in `notes/` relevant to what you're checking (and any earlier notes they reference).
- The actual code in `tools/` behind any computational claim — read the implementation itself, not the note's description of it.
- Any file in `data/` the note cites as evidence.
- The governing plan file (EXPLORE_PLAN.md or MAIN_PLAN.md) and any prior notes this claim needs to stay consistent with.

## Checks to run

### 1. Algebra / derivation correctness
Redo the derivation yourself, independently, step by step — don't skim for plausibility. For each nontrivial step, confirm it explicitly: dimensional analysis, a known limiting case, a symmetry argument. State exactly which line or equation breaks, if any, and why.

### 2. Reasoning validity
Does the stated conclusion actually follow from the cited evidence, or is there a logical gap? If an approximation is invoked (a perturbative expansion, an adiabatic/effective-theory reduction, a mean-field or weak-coupling limit, etc.), recompute the relevant ratio/threshold yourself and confirm the parameters used actually sit inside its claimed regime of validity — do not take the note's word for it.

### 3. Code-vs-claim consistency
If a tool or script produced the result, read its actual implementation and check it computes what the note says it computes. Look specifically for: sign errors, off-by-one/index errors, a hardcoded value silently overriding an intended parameter, or a physical restriction from `problem-spec` that the code claims to respect but doesn't actually enforce.

### 4. Cross-step consistency
Compare this claim against other notes and against `summary.md`'s status tags for related threads. Does it contradict an earlier note? Does it depend on a value or assumption that a later note already superseded? Quote both sides of any conflict you find.

### 5. Numerical sanity
Where applicable: check limiting cases (does the result reduce to the known/trivial answer when a coupling or interaction strength → 0, or a system-size/particle-number parameter → its smallest value?), check units/scale, check that a plotted scaling actually matches the fit claimed in the note.

## Report format

```
Self-Check: <what was checked>
=========================================
[PASS/FAIL] Algebra / derivation correctness — <specific finding>
[PASS/FAIL] Reasoning validity — <specific finding>
[PASS/FAIL] Code-vs-claim consistency — <specific finding>
[PASS/FAIL] Cross-step consistency — <specific finding>
[PASS/FAIL] Numerical sanity — <specific finding>

Verdict: CONFIRMED | ISSUES FOUND
```

If issues are found, give the exact location (file:line, or equation number) and the smallest fix that would resolve it. If everything passes, say so plainly — do not manufacture a finding to appear thorough.
