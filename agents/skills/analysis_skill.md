# Firmware Validation Analysis Skill

## When Used

Use this skill when the user asks about validation quality, failed requirements, subsystem risk, firmware readiness, root cause, or release decision.

## Input

- device configuration
- validation test results
- pass/fail summary
- failed requirements
- subsystem breakdown
- ranked risky tests

## Output

Return:

- answer
- evidence
- next_action
- recommendation
- decision

## Rules

- Mention exact deterministic metrics.
- Prioritize failed requirements before passing cases.
- Treat release readiness as blocked when failures exist.
- Use triage notes as the debug path.