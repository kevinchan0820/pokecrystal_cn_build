#!/usr/bin/env python3
"""Apply the Traditional Crystal IPS patch to your own legally backed-up US v1.1 ROM.

Python 3 standard library only. Nothing is uploaded or shared.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

BASE_SHA1 = "f2f52230b536214ef7c9924f483392993e226cfb"


def apply_ips(source: bytes, patch: bytes) -> bytes:
    if not patch.startswith(b"PATCH"):
        raise ValueError("Invalid IPS file: header is missing")
    data = bytearray(source)
    pos = 5
    while True:
        if pos + 3 > len(patch):
            raise ValueError("Invalid IPS file: missing EOF")
        if patch[pos:pos + 3] == b"EOF":
            pos += 3
            break
        if pos + 5 > len(patch):
            raise ValueError("Invalid IPS file: short record header")
        offset = int.from_bytes(patch[pos:pos + 3], "big")
        length = int.from_bytes(patch[pos + 3:pos + 5], "big")
        pos += 5
        if length == 0:
            if pos + 3 > len(patch):
                raise ValueError("Invalid IPS file: short RLE record")
            count = int.from_bytes(patch[pos:pos + 2], "big")
            payload = patch[pos + 2:pos + 3] * count
            pos += 3
        else:
            payload = patch[pos:pos + length]
            if len(payload) != length:
                raise ValueError("Invalid IPS file: truncated payload")
            pos += length
        end = offset + len(payload)
        if end > len(data):
            data.extend(b"\x00" * (end - len(data)))
        data[offset:end] = payload
    if pos + 3 == len(patch):
        del data[int.from_bytes(patch[pos:pos + 3], "big"):]
    elif pos != len(patch):
        raise ValueError("Invalid IPS file: bytes after EOF")
    return bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original_rom", type=Path, help="Your own Pokémon Crystal US v1.1 .gbc")
    parser.add_argument("patch", type=Path, help="Crystal_Traditional_Chinese_v1.1.ips")
    parser.add_argument("--output", type=Path, default=Path("Pokemon_Crystal_zh_TW.gbc"))
    parser.add_argument("--manifest", type=Path, default=None)
    args = parser.parse_args()
    base = args.original_rom.read_bytes()
    if hashlib.sha1(base).hexdigest() != BASE_SHA1:
        parser.error("Wrong base ROM: expected Pokémon Crystal US v1.1 (SHA1: " + BASE_SHA1 + ")")
    patch = args.patch.read_bytes()
    manifest_file = args.manifest or args.patch.with_name("zh_tw_patch_manifest.json")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8")) if manifest_file.exists() else None
    if manifest and hashlib.sha256(patch).hexdigest() != manifest["patch_sha256"]:
        parser.error("Patch checksum mismatch. Download again.")
    result = apply_ips(base, patch)
    if manifest and hashlib.sha256(result).hexdigest() != manifest["result_sha256"]:
        parser.error("Patched ROM checksum mismatch. Aborting.")
    if args.output.exists():
        parser.error("Output file already exists; choose a different --output name.")
    args.output.write_bytes(result)
    print("Created:", args.output)
    print("SHA256:", hashlib.sha256(result).hexdigest())
    print("The game file stays on your computer; it is not uploaded.")


if __name__ == "__main__":
    main()
