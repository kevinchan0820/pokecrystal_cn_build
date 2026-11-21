# Crystal 1.x — Superpowers execution discipline

This is a project-specific adoption of [obra/superpowers](https://github.com/obra/superpowers), **not a claim that the external Skill was installed in ChatGPT**.

## Autonomous completion contract (KC's requested operating mode)

**One request = deliver the result, not a sequence of requests for the user to type "continue".**
The parent goal is **a playable Pokémon Crystal 1.x Taiwan/Hong Kong Traditional Chinese IPS release and reproducible source, plus genuine input methods**. Progress on a subsystem, a green smoke test, or a handoff record is NOT completion of the parent goal.

**Activation / no-premature-final gate (ChatGPT Project and scheduled executor):**
- A request to "continue", "do it", "why did you stop?", "review Project Instructions", or the named final deliverable is **execution intent**. Start live GitHub reads and the first code/test/tool action **in the same assistant turn**, before writing a status or explaining why previous runs stopped.
- A successful micro-fix, a docs handoff, a green historical run, or a CI run merely queued/in-progress is **not** a stopping rule. After a commit, poll the fresh exact-code-head run; if red, inspect the first failed step and patch; if green, inspect genuine PyBoy artifacts and proceed to the next unmet gate while tools remain usable.
- "Update EXECUTION_STATE and next run resumes" is an **emergency checkpoint on an actual hard execution boundary**, not a substitute for running the next test. Never interpret this paragraph as permission to end after one tool call.
- The ChatGPT Project Instructions can trigger actions **while a chat turn or scheduled automation is running**, but cannot keep one response executing after it ends. The existing hourly automation is the continuation mechanism; do not create a duplicate. Do not promise continuous background work beyond that schedule.

**Executor rule for every scheduled run:**
1. Read the source repo and build repo's actual current `feature/zh-hant-tw-hk-1x` heads, `EXECUTION_STATE.md`, `TRUE_IME_ACCEPTANCE.md`, this file and latest CI artifacts. Resolve discrepancies between stale notes and exact branch heads.
2. Establish the remaining concrete failing **release acceptance tests**, automatically select the highest-priority actionable one, then immediately change/test actual implementation. Do not stop at a plan, status message, illustration, or already-green historical CI.
3. Apply Superpowers loop **RED → root cause → GREEN → full regression → PyBoy actual screen → review → GitHub commit**. **After GREEN, immediately start the next failing release gate in the SAME invocation. Repeat while tool access and execution budget remain.** A successful test, commit, handoff note, or `NOT READY` status is never a stopping condition. **Only if the execution environment actually ends the turn or all workable tool paths are exhausted** may you record exact SHAs, reproducer, failing evidence and the next executable step in `EXECUTION_STATE.md` for the existing hourly automation to resume without KC saying "continue". Do not voluntarily finish an active turn merely because a checkpoint was written.
4. Make meaningful progress: at least one new acceptance test, implementation fix, or verified release gate per run when tools permit. **"At least one" is a MINIMUM, not a quota or permission to stop.** Keep advancing independently through unmet release gates. If one route fails (e.g. local checkout DNS), use connected GitHub tools and remote GitHub Actions; don't interpret temporary local tool failure as completion or a reason to stop all work.
5. **Release completion, not discussion completion:** only label FINAL/READY if all requirements below are evidenced against the exact release source/build hashes and the legal patch artifact is available. Until then leave a release blocker visible but keep working in subsequent runs. Don't send KC "next stage, reply to continue" or demand approval for routine technical choices.
6. If a legal/licensing boundary, missing authorized source material, or repeated infrastructure failure truly requires KC, document specifically why autonomous alternatives cannot resolve it, what exact approval/input is required, and continue other independent tests first. Don't silently bypass rights or pretend a test passed.

**Mandatory end-state checks before FINAL/READY:**
- **Localization:** correct Taiwan/Hong Kong Pokémon terms and all user-visible workbook/ASM text; no Simplified/Mandarin-only typography in compiled font or source-referenced bitmap assets; actual gameplay frame sampling covers title, menus, battle HP/status and damage, bags, trainer card, dialogue, naming and credits. Record screen evidence, not just a successful OpenCC conversion.
- **Real IMEs:** Hong Kong **速成** (full practical licensed code table, multiple candidates, paging, wrong-code and deletion), full **倉頡** code composition, Taiwan **注音** symbols/tones; English/Pinyin remain usable. All keyboard keys preserve 8×8 cell dimensions; 26 Rime-style roots and their actual screen pixels are verified. Working player and Pokémon nickname entry, finish, maximum lengths and save/reload.
- **Functional stability:** ROM compile, hardware-compatible GBC boot/navigation, PyBoy real button actions and screenshots, no overlapping/clipped UI, no crashes; reproducible IPS generation + patch roundtrip, artifact checksums and clear application instructions.
- **Delivery:** publish only legally redistributable source and patch, never Nintendo copyrighted ROM; provide GitHub action/release link, screenshots of real gameplay, and concise known limitations only if they do not violate required acceptance.

**State machine:** `NOT READY` / `BLOCKED` describes **release acceptance only**. Execution must be `ACTIVE` or `AUTOMATICALLY RESUMING` as long as independently actionable acceptance tests exist. These are separate axes: never translate `NOT READY` into `STOP EXECUTING`.

## Reliability safeguards (2026-11-21; not all are implemented)

1. **Scheduling:** The existing once-hourly ChatGPT task is a wake-up/retry, not an hour-long continuous worker. Do not create duplicate ChatGPT automations; do not assume a task marked `completed` means 1.x release READY. Never promise that ChatGPT can resume the same closed response.
2. **Checkpoint write-ahead:** At start and after each source/test commit or CI verdict, write `EXECUTION_STATE.md` with UTC, run identity if known, BOTH exact source/build SHAs, CI URL/status, current blocker, and first runnable next action. Verify GitHub responded with a successful commit. A sudden failure can happen before the write; no instruction can guarantee a crash-time commit.
3. **Concurrency:** This execution may overlap interactive development and the scheduled agent. A plain Markdown `LOCKED` field is NOT a safe lock. Before parallel writes, implement and TEST an owner/run-ID + expiry lock using conditional atomic updates, re-check the remote refs, and serialize commits/CI. Never overwrite another active agent's changes; resolve write conflicts by fetching current SHA and reconciling.
4. **Exact-run provenance:** The current build workflow has `cancel-in-progress: true`, and documentation-only commits are ignored. Source-only pushes do NOT independently trigger this build workflow; a build can test source HEAD different from a later live branch head. Confirm source/build SHA **inside the artifact**, then verify they are current. If a code change cancels an in-flight CI, issue another exact-head run. Do not infer success from historical green.
5. **Independent watchdog — REQUIRED BUT NOT YET DEPLOYED:** Add a separate GitHub Actions scheduled workflow or equivalent independent process to monitor stale `STARTED/RUNNING` checkpoints, GitHub Actions failure/cancellation, source/build drift, prolonged lack of verified progress, and concurrent ownership. Account for healthy hour-boundary idle periods and CI durations when choosing thresholds. Persist a diagnostic outcome/notification, with retry limits and no alert spam. A GitHub watchdog can detect/report interruptions; it cannot awaken a previously ended ChatGPT response.
6. **Fault injection before claiming crash safety:** Verify an interrupted run, overlapping agents, a stale lock, cancelled CI, missing screenshots/artifacts, and non-exact SHA all produce the right BLOCKED/RESUME action. If no evidence exists, mark as UNVERIFIED, not DONE.
7. **State separation:** `Product: NOT READY` means no release; it does not authorize stopping actual development. `Execution: CHECKPOINTED_INCOMPLETE` is valid only at a genuine execution boundary. At the next scheduled invocation, recover stale/missing checkpoints from commits/CI/logs and continue.

**Machine-verifiable distinction:** `CI = success` is only evidence for implemented CI checks, not equivalent to `Product = complete`. Update `EXECUTION_STATE.md` with a remaining-blockers set and independent acceptance proof, not a made-up percentage. If all mandatory gates pass, deliver the final patch with its verified run and notify KC; otherwise the recurring task stays enabled.

## Binding rules for an executing agent

1. Before changing code, read `EXECUTION_STATE.md`, `TRUE_IME_ACCEPTANCE.md`, both `feature/zh-hant-tw-hk-1x` branch heads, the latest CI logs, and last actual PyBoy screenshot. **Never change 1.0.**
2. Follow Superpowers' `systematic-debugging`: reproduce → locate the exact source layer (workbook / ASM / title raster / toolbar PNG / glyph bitmap / emulator renderer) → identify root cause → fix the source. Don't assume OpenCC changes PNG files.
3. Follow `test-driven-development`: new regression test must fail on the original bug, then pass after the minimal repair. Record both expected and observed results in the execution ledger. For binary glyphs, check exact 2D pixel data and later the game screen.
4. Follow `verification-before-completion`: run the latest **uncancelled, exact-head** GitHub Action; read every test failure and compile status; inspect real PyBoy screenshots, not only text/RAM. **Never use an older green run as evidence for new edits**.
5. Check release acceptance **across every surface**:
   - `text.zh-TW.xlsx`: all actual imported game-display cells, terminology and official Pokémon naming
   - Displayed quoted ASM: all visible menus/dialogue; preserve intentional code words and original proper nouns
   - Rasterized Chinese: title art, 96×8 naming action strip, 120×8 naming mode strip, any newly discovered visible bitmap
   - DFS glyphs: Traditional Taiwan face used for both unique and shared Unicode characters (e.g. **好**), no original Simplified bitmaps
   - PyBoy: opening/title/menu, player naming, every existing mode and code entry, candidate choice, deletion, backspace, complete name and save/load, nickname entry/exit, screen wrapping/overlap
6. If one check fails, don't package or release a 1.x IPS as ready. Find first failure, fix, rerun. The public-facing result is **BLOCKED** until every criterion passes. Compile-only success is not release acceptance.
7. At any interruption, update `EXECUTION_STATE.md` with latest head SHA, CI run id and result, bug/reproduction, changed files, screenshots, failing tests, next specific action, and a list of unverified surfaces. Don't reset or duplicate the hourly scheduled task.
8. Preserve copyright/legal boundaries: source code and IPS only, no Nintendo ROM redistributions; verify external dictionary licences before importing full Quick/注音 data.

## Current priority

**Traditional Chinese UI parity first**: replace old Simplified naming bitmap `符号／删除` with Traditional `符號／刪除`, replace English `QUICK` with raster `速成`, verify actual screenshots and the Taiwan glyph of `好`, audit other user-provided Simplified screen text.

Then expand true Quick dictionary and real Zhuyin input with GBC controller tests. No static common-character picker may be advertised as a complete IME.

### Source skills

- https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/test-driven-development/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/executing-plans/SKILL.md
