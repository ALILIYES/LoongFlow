# Native PEES Mode

Follow these instructions exactly when the user chooses native PEES mode.

## Create Workspace

Create a uniquely named workspace directory for this task:

```
.loongflow/<task-slug>-<YYYYMMDD-HHMMSS>/
├── index.md
├── task.md
├── iteration_1/
│   ├── plan.md
│   ├── execute.md
│   ├── evaluate.md
│   └── summary.md
└── result.md              # Written at the end
```

- `<task-slug>`: short kebab-case name derived from the task description
- `<YYYYMMDD-HHMMSS>`: timestamp when the workspace is created

## Initialize task.md

Write the task description and success criteria to `task.md`. If the user provided explicit success criteria, use those. Otherwise, derive reasonable criteria from the task description and confirm with the user.

## Initialize index.md

```markdown
# PEES Evolution Index

## Task
<task description>

## Success Criteria
<criteria — user-defined or agent-derived>

## Iterations
(none yet)
```

## Run PEES Iterations

For each iteration (max 5 by default):

### Phase 1: Plan

1. **Read `index.md`** — review all prior iterations, scores, and key insights
2. If this is iteration 2+, read specific `iteration_N/summary.md` files for deeper context if needed
3. Write `iteration_N/plan.md` with:
   - What was learned from prior iterations (if any)
   - Why the new approach differs from previous attempts
   - Concrete action plan for this iteration
4. Update `index.md` with the plan summary line

### Phase 2: Execute

1. Implement the plan using your tools (read/write/edit files, run commands)
2. Write `iteration_N/execute.md` logging every significant action:
   - Files created or modified (with paths)
   - Commands run and their output
   - Decisions made during implementation
3. Update `index.md` with the execute summary line

### Phase 3: Evaluate

1. Evaluate the result:
   - If user provided success criteria: test against those specifically
   - Otherwise: run tests, check output, verify behavior, assess quality
2. Assign a score from 0.0 to 1.0
3. Write `iteration_N/evaluate.md` with:
   - Raw evidence: test output, error messages, command results
   - Score and justification
   - Status: `pass` (score >= target), `partial`, or `fail`
4. Update `index.md` with score and evaluate summary

### Phase 4: Summary

1. Analyze what worked and what didn't, and why
2. Extract reusable insights for the next iteration
3. Decide: **done** (score meets criteria), **iterate** (continue improving), or **escalate** (suggest Engine mode)
4. Write `iteration_N/summary.md` with:
   - What was tried and the outcome
   - Why it worked or failed
   - Key insight for the next iteration
   - Decision: done / iterate / escalate
5. Update `index.md` with summary and key insight

## Termination Conditions

- **Success**: Score meets or exceeds the target — write `result.md` with final outcome
- **Max iterations reached**: Write `result.md` summarizing best result achieved
- **Escalation**: If 3 consecutive iterations show no score improvement (delta < 0.05), suggest switching to LoongFlow Engine mode
- **User intervention**: User can stop or redirect at any time

## Write result.md

When done, write `result.md` with:
- Final score and status
- Best iteration number
- Summary of the solution
- Total iterations attempted
- Path to the best iteration's files
