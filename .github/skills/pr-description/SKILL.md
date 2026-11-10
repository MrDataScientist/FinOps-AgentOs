---
name: pr-description
description: Write or update an evidence-based pull request title and body for the actual branch diff when asked to open a PR, describe a branch or summarize review changes.
---

# Write a reviewable pull request

1. Read the repository instructions and PR template. Use that template before any fallback format.
2. Establish the repository, head SHA, target branch and merge-base. Inspect the complete branch diff and relevant recent title conventions; do not infer a PR from only its last commit.
3. Describe the concrete problem and resulting behavior. Group rationale by purpose. Include only work items supplied by the user or found in repository evidence.
4. Report exact checks, their outcomes and tested scope/SHA. Distinguish passed, failed, skipped and blocked. Never turn expected behavior into observed evidence.
5. Explain material risk and recovery. For infrastructure, distinguish reverting source from reverting applied resources.
6. Respect authorization already present in the task. A request to create a PR authorizes the necessary branch, commit, push and PR creation within that scope; do not introduce repeated approval gates. Reuse an open PR only when its branch and purpose match. Otherwise create a draft PR unless the user requests ready-for-review.
7. Use available authenticated GitHub tools or CLI. With CLI, put multiline UTF-8 bodies in a temporary file and use `--body-file`; do not interpolate prose into shell commands. Verify the remote head, changed files, title and body after posting. Never merge, deploy, enable auto-merge or resolve others' review threads as part of PR creation.

Without a repository template, use: **Problem and Result**, **Changes and Rationale**, **Verification**, and **Impact and Recovery**. Keep small PRs concise. Do not invent tickets, CI passes or reviewer approvals. Follow repository commit conventions; omit AI attribution footers.
