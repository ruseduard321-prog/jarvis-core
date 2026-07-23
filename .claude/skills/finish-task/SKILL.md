---
name: finish-task
description: Standardized completion workflow for Jarvis dev tasks — validates changes, runs targeted checks, updates docs if needed, and produces a concise completion report. Use when a coding task is done and needs to be wrapped up before handing back to the user.
---

# finish-task

Run this checklist at the end of a Jarvis development task, once code changes are in place. Do not use it for open-ended exploration — only for closing out work already done.

## Steps

1. **Review changes**
   - `git status` and `git diff` (or `git diff --stat` for large diffs) to enumerate exactly which files changed in this task.
   - Do not touch or restage files outside the scope of the current task.

2. **Compile check (backend only, if backend files changed)**
   - Run: `python -m compileall backend`
   - Fix any syntax/compile errors before continuing.

3. **Targeted tests only**
   - Identify which modules/services were touched and map them to their test files under `backend/tests/` (e.g. `backend/services/workflow_engine.py` → `backend/tests/test_workflow_engine.py`).
   - Run only those with: `python -m pytest backend/tests/test_<relevant>.py -q`
   - **Never run the full test suite** (`pytest backend/tests/`) unless the user explicitly asks for it.
   - If frontend files changed, run only the relevant check (e.g. `npm run lint` scoped to changed files) — do not run a full build unless asked.

4. **Regression sanity check**
   - Skim the diff for obvious issues: broken imports, removed error handling, unhandled edge cases introduced by the change, leftover debug code.
   - Confirm the service/repository/schema layering from [AGENTS.md](../../../AGENTS.md) wasn't bypassed.

5. **Documentation impact check**
   - Check whether the change affects the *current* state described in root `PROJECT_STATE.md`, `docs/architecture/ARCHITECTURE.md`, or `docs/planning/ROADMAP.md` (new feature completed, architecture changed, roadmap item finished/added).
   - Cosmetic or internal refactors with no behavior/status change do not require doc updates.

6. **Update docs if required**
   - If step 5 found a real gap, make a small, targeted edit to the relevant doc(s) only — no rewrites, no unrelated cleanup.
   - If no doc changes are needed, state that explicitly in the report rather than skipping the question.

7. **Completion report**
   - Output a concise report (no more than what's below — do not pad it):

     ```
     ## Completion Report

     **Files changed:** <list, or "none outside task scope">
     **Validation:** <compileall result> | <tests run + pass/fail> | <lint/build if applicable>
     **Docs updated:** <files updated, or "none needed — <reason>">
     **Remaining work:** <short list, or "none">
     **Risks:** <short list, or "none identified">
     ```

## Constraints

- Never run the full test suite unless explicitly requested.
- Never modify files unrelated to the current task.
- Keep all output concise — this is a summary step, not a narrative.
- Prefer existing project scripts/conventions (see [AGENTS.md](../../../AGENTS.md)) over inventing new tooling.
