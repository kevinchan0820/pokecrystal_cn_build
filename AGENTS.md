# Agent entrypoint — Pokémon Crystal 1.x Taiwan / Hong Kong

**Start here, especially when a previous chat has ended or the conversation is truncated.**

1. Read [AI_HANDOFF.md](AI_HANDOFF.md) as the canonical project/next-agent recovery document.
2. Read [EXECUTION_STATE.md](EXECUTION_STATE.md) for chronological implementation and regression evidence (older items may be superseded).
3. Fetch BOTH branch heads and latest GitHub Actions CI on `feature/zh-hant-tw-hk-1x`; inspect current run's `zh_tw_ci_handoff.json` and real screenshots if available.
4. Read [SUPERPOWERS_EXECUTION.md](SUPERPOWERS_EXECUTION.md) and [.agents/skills/crystal-end-to-end-localization/SKILL.md](.agents/skills/crystal-end-to-end-localization/SKILL.md).
5. **Do actual work** on first unmet release acceptance: diagnose, test, implement, rerun CI and PyBoy, persist new verified state, advance to next. Do not request "continue" after intermediate checkpoints.
6. Preserve original 1.0; no copyrighted Nintendo ROM distribution; no claims of full completion until every mandatory criterion has independently verifiable evidence.

**Provenance rule:** A green CI, stale saved memory or this README alone cannot verify the latest source. Compare precise SHAs with GitHub live branch heads and built artifacts. If blocked, report accurately and leave exact next action in AI_HANDOFF.md / EXECUTION_STATE.md.

**Do not** create duplicate scheduled tasks; Project Instructions trigger response behavior but cannot keep a chat running after it ends.
