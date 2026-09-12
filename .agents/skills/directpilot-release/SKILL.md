---
name: directpilot-release
description: Release reviewed DirectPilot backend or frontend changes safely. Use for staging, committing, pushing, deploying, or verifying a release; do not use for implementation or broad audits.
---

# DirectPilot release

1. Confirm repository root, branch, HEAD, remote, and `git status --short`.
2. Identify the exact user-approved paths. Preserve every unrelated modified or untracked path.
3. Review only the intended diff and run focused checks. Run the repository's full suite once when the release gate requires it; do not repeat already-valid expensive checks without cause.
4. Run diff/secret checks. Reject environment files, credentials, tokens, runtime databases, generated output, and temporary diagnostics.
5. Stage paths explicitly and verify `git diff --cached --name-only` equals the approved set.
6. Commit only when authorized, using the requested message. Never amend, reset, clean, stash, rebase, or force push unless the user explicitly requests that exact operation.
7. Push normally to the named branch. Verify local and remote SHAs match.
8. If deployment is authorized, use only the existing deployment project/flow. Correlate the deployed runtime with the exact commit and verify required health/smoke endpoints.
9. Report local tests, push, deployment, and cloud UAT as separate evidence states.
