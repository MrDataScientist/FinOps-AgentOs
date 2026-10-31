# Evaluation plan — no measured benchmarks yet

1. Freeze 20–30 **synthetic** tasks with expected policies and independently reviewed quality labels. Reserve holdout examples.
2. Compare fixed cloud, fixed local and governed hybrid policies on the **same** task set, model revisions, timeouts and token limits.
3. Record accepted completions, unsupported claims, groundedness, language quality and latency distribution. Do not treat an LLM's self-rating as independent evaluation.
4. Separate input-token/output-token API charges, local hardware amortization, power, hosting, monitoring, retries, support and staffing.
5. Reconcile estimated costs with cloud invoices; report `cost_per_accepted_task = relevant_TCO / accepted_tasks` (undefined at zero accepted tasks).
6. Compute savings **only** against quality-comparable baseline alternatives at the same traffic and workload.
7. Verify denial behavior for internal/restricted prompts and prompt-injection attempts. Never send real corporate data to unapproved services.
8. Report confidence, workload assumptions, failures and negative results.

Current `scenarios/` examples are **illustrative fictional inputs**, not real Stormscope weather snapshots or proven accuracy evidence. The in-memory ledger reports illustrative per-request dollar assumptions only.
