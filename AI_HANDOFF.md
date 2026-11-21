# Pokémon Crystal 台港繁體 1.x — AI HANDOFF (canonical entrypoint)

> **給下一個 AI：不要讀完整 ChatGPT 對話才開始。先讀呢份文件，再讀最新 GitHub branch / CI。** 本文件係固定入口，不代表其中時間戳一定係最新狀態。

## 1. Parent goal / Definition of Done

KC 要交付 **可重現構建、完整可玩、台港繁體像素字形正確嘅 Pokémon Crystal 1.x IPS Patch**。香港人可以用真正 **速成及倉頡**，台灣人可以用真正 **注音**，訓練家及寶可夢改名、儲存／讀取、實際遊戲畫面都通過驗收。唔好改動 1.0 原味版。只可以分享有權分發嘅 source + IPS，不可分享 Nintendo ROM。

具體驗收見 [SUPERPOWERS_EXECUTION.md](SUPERPOWERS_EXECUTION.md)（Autonomous completion contract）、[TRUE_IME_ACCEPTANCE.md](TRUE_IME_ACCEPTANCE.md)、[RUNTIME_TRADITIONAL_IMAGE_AUDIT.md](RUNTIME_TRADITIONAL_IMAGE_AUDIT.md)。**CI PASS 只代表 CI 涵蓋嘅子測試通過；唔代表產品完成。**

## 2. Branches and exact provenance

| Purpose | Repository | Only branch |
|---|---|---|
| Game source (ASM, graphics, IME) | [kevinchan0820/pokecrystal_cn](https://github.com/kevinchan0820/pokecrystal_cn/tree/feature/zh-hant-tw-hk-1x) | `feature/zh-hant-tw-hk-1x` |
| Build, QA, reproducible IPS | [kevinchan0820/pokecrystal_cn_build](https://github.com/kevinchan0820/pokecrystal_cn_build/tree/feature/zh-hant-tw-hk-1x) | `feature/zh-hant-tw-hk-1x` |

**Latest tested gameplay source at this handoff:** `525f6728ec3d04ede5517fe079a462db72670aab`. **Previously verified complete workflow:** [GitHub Actions #44873879766](https://github.com/kevinchan0820/pokecrystal_cn_build/actions/runs/44873879766), build source code commit `8ef9e14b5f88640d83e26ce6d1bb8d4d56d12d4f`. Earlier full suite green; handoff automation code added after this run, so re-check newer run before claiming current green.

**FIRST ACTION EVERY SESSION:** Read *live* branch heads, latest Action run for the build branch, job logs, downloadable artifact, and current [EXECUTION_STATE.md](EXECUTION_STATE.md). Exact run evidence is more authoritative than old green notes. If current HEAD includes only Markdown changes, CI may not retrigger (`paths-ignore: '**/*.md'`); use latest successful code SHA only if source SHA matches.

The Actions artifact now provides `zh_tw_ci_handoff.json`, `zh_tw_ci_handoff.md`, `zh_tw_source_commit.txt`, PNG screenshots, per-test JSON reports and IPS checksum. These are machine-readable **run evidence**, not release approval.

## 3. Verified functionality, without exaggerating

- 1.x source compiles and boots in PyBoy; initial menus, options, naming flows are exercised in GitHub Actions.
- Quick **tiny prototype dictionary**: real controller `AA → 晶`, `AB → 明`, `VD → 好` with actual candidate selection and named bytes.
- In Quick mode the 26 **日月金木水火土竹戈十大中一弓人心手口尸廿山女田難卜符** roots occupy original A-Z 8x8 key cells; actual Q-Z frame-pixel audit was RED then GREEN after fixing VRAM bank1 copy from 16 to 26. **Human legibility still unapproved**.
- Pixel assets converted and checked: 96x8 `符號／刪除` name action toolbar, Traditional mode headers, title logo checks, `精靈球` bag tilemap, `目前狀態` Trainer Card raster.
- Battle localization **source** audit checks `敵人／灼傷`; original user screenshot may be from earlier patch and has no verified ROM SHA. **No actual burned-battle screenshot pass yet**.

## 4. UNFINISHED — Product is NOT RELEASE READY

1. True practical HK Quick dictionary, multiple candidates, paging, wrong-code/delete, persistent player and Pokémon nicknames.
2. Full HK Cangjie compose and lookup, Taiwan Zhuyin symbol/tones input, 8x8 font UX.
3. Actual PyBoy gameplay screen acceptance: battle/burn status, bag, Trainer Card, credits, overworld, story text, name screen and save/load.
4. Edit remaining visible raster assets only if truly used: unresolved `gfx/new_game/name_chinese.png` needs trace of source references + screen, not random replacement.
5. Regional editorial review beyond mechanical OpenCC; no claims of 100% coverage without real verification.

### NEXT EXECUTABLE TASK (do it; don't ask KC to continue)

Use GitHub connected API and current branch; check if current/latest CI now emits `zh_tw_ci_handoff.json`. If CI RED, inspect job logs and repair manifest/test first; rerun. Then **trace `gfx/new_game/name_chinese.png` usages** across built game ASM and classify as referenced/unreferenced (explicit references do NOT prove runtime rendering). Add reproducible source reference report to CI. Follow up with actual PyBoy Bag/Trainer Card and battle scenarios. Continue to further release blockers within available execution.

## 5. Execution rules (trigger on Intent, not magic words)

**Discover → Define → Test (RED) → Implement → Debug → Retest → Real PyBoy Screenshots → Verify → Commit → Next task.**

- Answer straightforward questions directly. For actual goals, execute immediately; don't hand back a plan or expect `continue`.
- Preserve the user's parent goal and Definition of Done; a green subtask is NOT a final release.
- At natural run boundary update [EXECUTION_STATE.md](EXECUTION_STATE.md) and this file (only if necessary), with exact source SHA, build SHA, CI ID and first next actionable task. New model should resume from it without redoing old investigations.
- Check [project Skill](.agents/skills/crystal-end-to-end-localization/SKILL.md) and Superpowers original [skills](https://github.com/obra/superpowers). Project-specific skill in GitHub isn't automatically installed in ChatGPT.
- Do not guess success; use exact-head CI and genuine PyBoy image evidence. If a tool is unavailable (e.g. local git DNS), prefer connected GitHub + cloud Actions; document real blockers.
- Never make irreversible external decisions, release proprietary ROM binaries, or merge into 1.0 without authorization.

## 6. New ChatGPT conversation recovery

The user can open a fresh chat **inside the same E2E Project** and send:

```text
繼續 Pokémon Crystal 1.x。先讀
https://github.com/kevinchan0820/pokecrystal_cn_build/blob/feature/zh-hant-tw-hk-1x/AI_HANDOFF.md
再查兩個分支 HEAD、最新 CI、EXECUTION_STATE.md，按 Project Instructions 自動恢復最後未完成嘅工作；唔使我逐個 Phase 講 continue。
```

This one-line recovery prompt is a fallback, not a requirement to re-describe the goal. A new model still needs live GitHub access, valid connector permissions and access to this branch. The **Project Instructions** supply behavior; **this repo supplies state/evidence**; **a real ongoing automation** is needed for work after chat session ends.
