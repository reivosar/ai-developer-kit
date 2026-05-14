---
name: loop
description: Run a task repeatedly at a fixed interval. Use when the user invokes
  /loop, says "run this every N minutes", "repeat this", or "keep doing X."
---

# Loop

Execute a task on a repeating schedule using ScheduleWakeup.

## Arguments

`$ARGUMENTS` is the task to repeat, optionally with an interval (e.g. "check
CI every 5 minutes"). If no interval is given, ask or use context to infer one.

## Process

### 1. Clarify

Confirm:
- What to do each iteration
- The desired interval in seconds (default: 270s to stay within cache TTL)
- Any stop condition ("until CI passes", "3 times", etc.)

### 2. Execute first iteration

Perform the task now.

### 3. Schedule next iteration

Call ScheduleWakeup with:
- `delaySeconds`: the interval (clamped to 60-3600 by runtime)
- `prompt`: the original /loop invocation verbatim so the next wake-up re-enters this skill
- `reason`: one sentence describing what is being waited for

### 4. Stop condition

If a stop condition was specified and is now met, do NOT call ScheduleWakeup.
Report that the loop has ended and why.
