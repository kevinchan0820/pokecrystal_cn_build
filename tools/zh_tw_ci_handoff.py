#!/usr/bin/env python3
"""Create reproducible CI evidence for future AI handoffs, without claiming release readiness."""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = {
    "real_quick_entry": ("zh_tw_quick_pyboy_report.json", "passed"),
    "real_full_cangjie_controller": ("zh_tw_cangjie_runtime_report.json", "passed"),
    "real_taiwan_zhuyin_controller": ("zh_tw_zhuyin_runtime_report.json", "passed"),
    "real_26_key_visuals": ("zh_tw_quick_ui_report.json", "passed"),
    "deep_name_entry": ("zh_tw_naming_deep_report.json", "passed"),
    "trainer_card_raster": ("zh_tw_trainer_card_raster_report.json", "verified"),
    "naming_action_and_mode_rasters": ("zh_tw_toolbar_bitmap_audit_report.json", "verified"),
    "bag_sprite_raster": ("zh_tw_pack_pocket_audit_report.json", "verified"),
    "inline_player_names_traditional": ("zh_tw_player_names_report.json", "verified"),
    "mechanical_text_audit": ("zh_tw_complete_text_audit_report.json", "passes_mechanical_translation"),
    "battle_source_text": ("zh_tw_battle_audit_report.json", "verified"),
}
SCREENS = [
    "zh_tw_quick_ui_quick_radical_keyboard.png",
    "zh_tw_quick_ui_typed_VD.png",
    "zh_tw_quick_ui_name_HAO.png",
    "zh_tw_cangjie_five_root_mode.png",
    "zh_tw_cangjie_typed_VND.png",
    "zh_tw_cangjie_committed_VND.png",
    "zh_tw_zhuyin_real_mode7_zhuyin.png",
    "zh_tw_zhuyin_typed_4_symbols.png",
    "zh_tw_zhuyin_committed_4.png",
    "zh_tw_zhuyin_committed_1.png",
    "zh_tw_ui_title.png",
    "zh_tw_ui_options.png",
]
UNFINISHED = [
    "Full player and Pokemon nickname flow plus SRAM save/reload",
    "Actual in-game burn battle, Bag and Trainer Card screenshots",
    "Full-game Traditional font/raster/editorial and scene acceptance",
    "Human readability of every 8x8 Cangjie and 41 Zhuyin key glyph",
    "Full IME edge-case stress and save corruption regression matrix",
]

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def head(path="."):
    return subprocess.check_output(["git", "-C", path, "rev-parse", "HEAD"], text=True).strip()

def main():
    build_sha = head()
    source_sha = head("pokecrystal_cn")
    pin_file = Path("zh_tw_source_commit.txt")
    if not pin_file.is_file() or pin_file.read_text().strip() != source_sha:
        raise SystemExit("FAIL: missing or mismatched source commit pin")
    checks = {}
    for label, (filename, key) in REQUIRED.items():
        file = Path(filename)
        if not file.is_file():
            raise SystemExit("FAIL: report missing: " + filename)
        data = json.loads(file.read_text(encoding="utf-8"))
        if data.get(key) is not True:
            raise SystemExit("FAIL: report does not pass: " + filename + "." + key)
        checks[label] = {"passed": True, "report": filename, "sha256": digest(file)}
    for name in SCREENS:
        if not Path(name).is_file():
            raise SystemExit("FAIL: real PyBoy screenshot missing: " + name)
    patch = Path("Crystal_Traditional_Chinese_TWHK_1x.ips")
    manifest = json.loads(Path("zh_tw_patch_manifest.json").read_text(encoding="utf-8"))
    if digest(patch) != manifest.get("patch_sha256"):
        raise SystemExit("FAIL: IPS checksum disagreement")
    run_id = os.getenv("GITHUB_RUN_ID")
    url = ("https://github.com/" + os.getenv("GITHUB_REPOSITORY") + "/actions/runs/" + run_id
           if run_id and os.getenv("GITHUB_REPOSITORY") else None)
    result = {
        "schema": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_repo": "kevinchan0820/pokecrystal_cn",
        "build_repo": os.getenv("GITHUB_REPOSITORY", "kevinchan0820/pokecrystal_cn_build"),
        "branch": "feature/zh-hant-tw-hk-1x",
        "source_sha": source_sha,
        "build_sha": build_sha,
        "run_id": run_id,
        "run_attempt": os.getenv("GITHUB_RUN_ATTEMPT"),
        "url": url,
        "checks": checks,
        "screenshots": SCREENS,
        "ips": {"name": patch.name, "sha256": digest(patch)},
        "scope": "Checks included in the current CI ONLY, not complete game QA",
        "release_ready": False,
        "unverified_release_gates": UNFINISHED,
        "next_agent_entrypoint": "AI_HANDOFF.md",
    }
    Path("zh_tw_ci_handoff.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# Automatically generated CI handoff", "",
        "Build SHA: " + build_sha,
        "Source SHA: " + source_sha,
        "GitHub Actions: " + (url or "local"),
        "Patch SHA256: " + result["ips"]["sha256"],
        "CI checks: PASS; overall product: NOT READY", "",
        "## Checks run and passed",
    ]
    lines.extend("- " + name + ": " + d["report"] for name, d in checks.items())
    lines.extend(["", "## PyBoy screen evidence"])
    lines.extend("- " + x for x in SCREENS)
    lines.extend(["", "## Unfinished acceptance"])
    lines.extend("- [ ] " + x for x in UNFINISHED)
    lines.extend(["", "Next AI: read AI_HANDOFF.md, then verify the CURRENT branch heads and this run's artifacts."])
    Path("zh_tw_ci_handoff.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("CI handoff: " + str(len(checks)) + " passing checks, "
          + str(len(SCREENS)) + " screenshots; RELEASE_READY=false")

if __name__ == "__main__":
    main()
