# FundLens — GSD Workflow Instructions

This project uses **get-shit-done (GSD)** — a structured planning and execution framework that combines atomic commits, phase-based delivery, and goal-backward verification.

## Quick Commands

### Planning

- `/gsd-discuss-phase 1` — Gather context and clarify approach for current phase
- `/gsd-plan-phase 1` — Create detailed execution plan with tasks and dependencies
- `/gsd-research-phase 1` — Research how to implement the phase

### Execution

- `/gsd-execute-phase 1` — Run all tasks for current phase with atomic commits
- `/gsd-verify-work` — Validate phase deliverables match requirements

### Project Management

- `/gsd-progress` — Show current status and next action
- `/gsd-resume-work` — Restore full context after interruption
- `/gsd-check-todos` — List pending ideas/tasks
- `/gsd-pause-work` — Create structured handoff for later resumption

### Documentation

- `/gsd-docs-update` — Generate or update project documentation
- `/gsd-audit-uat` — Cross-phase audit of outstanding validation items

---

## Workflow Overview

### Phase Lifecycle

Each phase follows this cycle:

1. **DISCUSS** — Gather requirements, assumptions, and approach details
   - Understand what success looks like
   - Surface unknowns and risks
   - Align on tech stack choices

2. **PLAN** — Create detailed execution plan
   - Break work into atomic tasks
   - Define dependencies and parallelization
   - Estimate effort and timeline
   - Verify plan achieves phase goal

3. **EXECUTE** — Run all tasks with continuous verification
   - Execute tasks in order (respecting dependencies)
   - Each task generates atomic git commit
   - Verify work as it completes
   - Surface and resolve issues immediately

4. **VERIFY** — Confirm phase goal is achieved
   - All requirements mapped to phase are passing
   - Deliverables match success criteria from ROADMAP
   - No critical bugs or omissions

5. **TRANSITION** — Archive phase and prepare next
   - Update PROJECT.md with decisions/learnings
   - Move validated requirements from Active to Validated
   - Update STATE.md with new progress
   - Route to next phase

---

## Project Structure

### Planning Directory (`.planning/`)

```
.planning/
├── PROJECT.md              # Project context, vision, decisions
├── REQUIREMENTS.md         # v1 requirements with traceability
├── ROADMAP.md              # 5-phase execution plan
├── STATE.md                # Current progress and session continuity
├── config.json             # Workflow preferences
├── research/               # Domain research (if enabled)
│   ├── STACK.md
│   ├── FEATURES.md
│   ├── ARCHITECTURE.md
│   ├── PITFALLS.md
│   └── SUMMARY.md
├── phases/
│   ├── 01-data-ingestion/
│   │   ├── CONTEXT.md      # Approach and assumptions
│   │   ├── PLAN.md         # Detailed tasks
│   │   ├── SUMMARY.md      # Results and decisions (created after execute)
│   │   └── ...             # Phase artifacts
│   ├── 02-storage/
│   └── ...
└── ...
```

### Git Commit Strategy

- **Planning commits:** `docs: [action]` (rarely blocking)
- **Execution commits:** `feat: [task name]` (atomic, frequent, pass all tests)
- **Fix commits:** `fix: [issue]` (for issues discovered during review)
- **Refactor commits:** `refactor: [component]` (if needed)

Each commit is independently testable — if it breaks, that specific commit is reverted.

---

## Phase 1: Data Ingestion Pipeline

### What's Being Built

System to accept CSV/Excel files containing fund data, normalize them to a standard schema, validate for quality, and store for later retrieval.

### Success Looks Like

- User uploads a CSV → system parses and normalizes
- Malformed data logged and reported
- Valid data stored in normalized schema
- API endpoints documented and working

### Key Decisions

- Pandas for CSV/Excel (industry standard, well-tested)
- Pydantic for schema validation (type safety, clear errors)
- FastAPI for HTTP (modern, documented, fast)

### Next Steps

1. `/gsd-discuss-phase 1` — Align on approach
2. `/gsd-plan-phase 1` — Create task breakdown
3. `/gsd-execute-phase 1` — Build and test

---

## Configuration

### Workflow Preferences

- **Mode:** YOLO (auto-approve, trust execution)
- **Granularity:** Standard (5-8 phases, balanced)
- **Execution:** Parallel (independent tasks run simultaneously)
- **Research:** Enabled (investigate domain before planning)
- **Plan Check:** Enabled (verify plans achieve phase goals)
- **Verifier:** Enabled (confirm deliverables match requirements)

### Modify Preferences

```
/gsd-settings — View and change workflow configuration
```

---

## Troubleshooting

### "Where are we?"

```
/gsd-progress
```

Shows current phase, plan, and next action.

### "I was in the middle of something"

```
/gsd-resume-work
```

Loads STATE.md and checks for incomplete work (mid-plan checkpoints, interrupted agents, etc.)

### "I need to pause"

```
/gsd-pause-work
```

Creates structured handoff (HANDOFF.json) with:

- Current task (X of Y)
- Completed vs pending work
- Blockers and next steps
- Session notes for resumption

### "Plans aren't working"

```
/gsd-plan-review-convergence
```

Cycle through plan revisions until no HIGH concerns remain.

### "I think there's a bug"

```
/gsd-debug
```

Systematic debugging with persistent checkpoints across context resets.

---

## Extending This Project

### Add a New Phase

```
/gsd-add-phase — Add new phase to end of roadmap
/gsd-insert-phase — Insert urgent work between existing phases
```

### Remove or Rethink Phases

```
/gsd-remove-phase — Remove future phase and renumber
/gsd-undo — Revert completed phase work
```

### Update Roadmap After Learnings

```
/gsd-audit-milestone — Check if milestone delivered what it promised
/gsd-extract_learnings — Extract decisions/patterns/surprises from phase artifacts
```

---

## Best Practices

### During Planning

- Follow threads in discussion (don't rush)
- Make abstract concrete (ask for examples)
- Surface assumptions early (they hide risks)

### During Execution

- One task at a time (complete → commit → verify)
- If blocked, escalate immediately (don't work around it)
- Tests are first-class artifacts (not afterthought)

### Between Phases

- Update PROJECT.md with decisions
- Move validated requirements to "Validated" section
- Check if assumptions still hold

### For Long Sessions

- Use `/gsd-pause-work` if stepping away mid-phase
- Use `/gsd-check-todos` to capture ideas without disrupting current task
- Use `/gsd-plant-seed` for forward-looking ideas (surfaces at milestone boundaries)

---

## Further Reading

- **PROJECT.md** — Full project context, vision, and key decisions
- **REQUIREMENTS.md** — v1 scope with traceability to phases
- **ROADMAP.md** — 5-phase execution plan with success criteria
- **STATE.md** — Current progress and session continuity

---

_Generated: 2026-04-26 for FundLens MVP_
