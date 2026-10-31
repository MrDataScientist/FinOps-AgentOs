# Contributing to FinOps-AgentOS

## Gitmoji commit messages

This repository adopts [Gitmoji](https://gitmoji.dev/) for **every new commit**, including contributions from AI coding agents.

**Format:** `<emoji> <type>(optional-scope): <short imperative description>`

Examples:

| Gitmoji | Use | Example commit subject |
| --- | --- | --- |
| ✨ | New feature | `✨ feat(gateway): expose routing plans` |
| 🐛 | Bug fix | `🐛 fix(providers): handle inference timeout` |
| 📝 | Documentation | `📝 docs: explain cost assumptions` |
| ✅ | Tests | `✅ test(routing): verify budget denial` |
| 💚 | Fix failing CI | `💚 ci: repair test workflow` |
| 👷 | Add or update CI | `👷 ci: add policy validation job` |
| 🔒️ | Security or privacy fix | `🔒️ fix(security): reject unsafe provider` |
| ♻️ | Refactor | `♻️ refactor(policies): extract eligibility rules` |
| 🏗️ | Architectural change | `🏗️ refactor: isolate control plane` |
| 🧱 | Infrastructure changes | `🧱 build(infra): define local containers` |
| 📈 | Analytics and tracking | `📈 feat(metrics): track routing decisions` |
| 🚨 | Linter warnings | `🚨 style: resolve Ruff warnings` |
| 🔧 | Configuration | `🔧 chore: update development defaults` |

Guidelines:
1. Put exactly one relevant Gitmoji at the beginning of each new commit subject.
2. Describe **what changed**, not an ambiguous phrase like `updates` or `more work`.
3. Use a focused commit and review its diff before pushing.
4. When merging or squashing PRs, keep the resulting commit message Gitmoji-prefixed too.
5. The rule applies prospectively. Do not rewrite shared commit history just to add emojis.

## Development checks

```bash
pip install -e '.[dev]'
python -m pytest -q
ruff check .
```

Do not add secrets or real enterprise customer data. Benchmark figures and financial savings must be clearly distinguished from synthetic examples.
