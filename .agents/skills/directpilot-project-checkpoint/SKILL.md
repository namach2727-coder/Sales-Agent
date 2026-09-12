---
name: directpilot-project-checkpoint
description: Update DirectPilot docs/project-status.md from verified evidence. Use after implementation, validation, release, deployment, UAT, or credential-rotation milestones; not for speculative plans.
---

# DirectPilot project checkpoint

1. Read the current `docs/project-status.md`, relevant Git state, and only the evidence produced by the completed task.
2. Record durable facts: canonical lineage/head, migration head, commercial/runtime invariants, validated test counts, deployment state, UAT results, and genuine blockers.
3. Label each claim precisely as implemented, locally tested, committed, pushed, deployed, or cloud-UAT verified. Never promote one state into another.
4. Do not record temporary correlation IDs, marker strings, session paths, deployment IDs, timestamps, dirty-file lists, secrets, or unverifiable claims.
5. Preserve prior valid history and update only stale sections. Keep one concise next action and only genuine P0 blockers.
6. Run a diff/secret check on the documentation change. Do not commit unless separately authorized.
