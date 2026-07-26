---
name: build-tools
description: "Write or extend a reusable Python tool in tools/ before doing any new derivation/simulation work — invoke it whenever you're about to write code"
argument-hint: "<functionality you need>"
---
# Build Tools

Invoke this skill with the Skill tool yourself, in-context, any time you are about to write code — during exploration, during a derivation phase, or mid-phase when you realize you need something new. Do not wait for a dedicated "tool generation" step; because the theory is nonlinear, you often can't know what a phase needs until you're inside it.

`tools/` is a single library that persists across the ENTIRE project — exploration (`init_exploration/`) and the full derivation (`main_derivation/`). A function built to test one candidate approach may be exactly what a later, unrelated investigation needs. Treat everything you write as a permanent addition to that library, not a disposable script for the task in front of you.

---

## Step 0: Check before you write

Before writing a single line, search `tools/` for something that already does this or close to it:
- Read `tools/INDEX.md` if it exists (see below) — it's the fast path.
- Grep function names/docstrings for the specific technique or quantity you need (e.g. the name of an approximation, an observable, a numerical method).

If a close match exists, **extend it** (add a parameter, generalize a special case) rather than writing a near-duplicate. A second function that does almost the same thing as an existing one is a bug, not a convenience — it lets the two silently drift apart.

## Step 1: Decide where the tool belongs

Organize files by **computational/theoretical domain**, not by when you happened to need them. A tool built to test one candidate approach during exploration and a tool needed much later in the main derivation might belong in the same file if they operate on the same kind of object. Name files after the domain they serve (e.g. the class of model they construct, the technique they implement, the observable they compute) — never after a session, date, or "phase."

If you built something useful in `init_exploration/` as a one-off, promote it into `tools/` before moving on — don't leave working logic stranded in a folder that later work won't think to look in.

## Step 2: Construction guidelines

- **Generic interface.** Every physical quantity is an explicit argument with a name that states its physical meaning — no hardcoded numbers. If a value is a true fixed constant from `problem-spec` (something that must never be altered), it still gets passed in as a parameter, sourced from one canonical place, not retyped inline across files.
- **Pure functions, no global state.** Explicit inputs, explicit returns. Nothing implicitly depends on module-level variables set elsewhere.
- **Composable outputs.** Prefer returning intermediate objects (state vectors/operators, arrays, effective parameter dictionaries) over only a final scalar or a plot. A future investigation you haven't scoped yet may need to recombine your intermediate results in a way you can't anticipate today.
- **Bake in the physical sanity checks, don't rely on remembering them.** If `problem-spec` establishes an invariant or a restriction (a conservation law, the validity domain of an approximation, a constant that must not be modified), add an assertion or a documented precondition directly in the function. You (or a future session) will reuse this tool long after the reasoning that produced it has left context.
- **Vectorize, don't parallelize prematurely.** Use numpy vectorization where the math allows it. Don't bake `ProcessPoolExecutor`/multiprocessing into the tool itself unless the tool's own job is inherently the parallel dispatch — the decision of what's "independent" belongs to the caller, not the shared tool.
- **Documentation is physical, not mechanical.** One-line file header stating the domain it serves. One-line function docstring stating what physical quantity goes in and what physical quantity comes out — not what the code mechanically does.
- **Confirm dependencies before importing.** Run `python -c "import <package>"` first; if missing, use an available alternative or implement directly.

## Step 3: Verify immediately

- Run the file. Its `if __name__ == "__main__"` block must exercise the new/changed function on a representative input and complete without exceptions.
- If you EDITED an existing shared tool rather than adding a new one, explicitly flag this: state which tool changed, why, and which prior notes/results (if any) used it and may need re-verification. A silent edit to a shared tool can invalidate an earlier finding without anyone noticing.

## Step 4: Update the index

Maintain `tools/INDEX.md`, one line per function:
```
- `<module>.<function>(<args>)` — one-line physical meaning of what it computes
```
This is what makes Step 0 cheap as the library grows — future invocations of this skill should be able to check for overlap by reading this one file instead of every tool file in the directory.
