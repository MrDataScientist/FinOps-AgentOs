# Agent instructions — FinOps-AgentOS

These instructions apply to all coding agents and automated contributors working in this repository.

## Commit convention (required)

**Prefix every new Git commit message with a purpose-matched emoji from https://gitmoji.dev/.**

Format: `<gitmoji> <type>(optional-scope): <imperative summary>`

Examples:
- `✨ feat(routing): add policy-aware model selection`
- `🐛 fix(accounting): handle missing usage metadata`
- `✅ test(policies): cover restricted-data rejection`
- `📝 docs: document the evaluation methodology`
- `💚 ci: repair the Python test workflow`
- `🔒️ fix(security): block unauthorized cloud fallback`
- `🏗️ refactor: separate cost accounting from inference`
- `🧱 build(infra): add sandbox deployment configuration`

Choose the emoji for the **primary purpose** of the changes. Do not use generic celebration emoji for every commit. Write clear, descriptive, specific summaries. Gitmoji shortcodes are documented at gitmoji.dev; prefer the rendered emoji in GitHub commit subjects.

Do not force-push or rewrite already published commits merely to change historical messages without explicit authorization.

## Engineering safety

- Keep live inference opt-in and protect it with authentication.
- Treat price assumptions as illustrative until reconciled with actual provider billing.
- Do not send restricted company data to personal or unapproved models.
- Keep Stormscope's deterministic risk decisions under application control.
- Require policy checks and human authorization before consequential infrastructure writes.
- Run tests and lint where feasible before opening or updating a PR.
