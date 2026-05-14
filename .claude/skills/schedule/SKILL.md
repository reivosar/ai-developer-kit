---
name: schedule
description: Schedule a one-off or recurring task to run at a future time. Use
  when the user says "schedule this", "run at X time", "do this every day at Y",
  or wants a cron-based task.
---

# Schedule

Create a scheduled or recurring task using CronCreate.

## Arguments

`$ARGUMENTS` describes what to run and when (e.g. "remind me to review PRs every
weekday at 9am").

## Process

### 1. Parse timing

Extract from $ARGUMENTS:
- **One-off**: a specific date/time ("tomorrow at 3pm", "2026-06-01 10:00")
- **Recurring**: a cron expression or natural-language schedule ("every weekday",
  "every Monday at 9am")

If timing is ambiguous, ask before proceeding.

### 2. Create the cron

Use CronCreate with the appropriate schedule and the task description as the prompt.

### 3. Confirm

Report: what was scheduled, when it will run, and the cron ID so it can be
cancelled later with CronDelete.
