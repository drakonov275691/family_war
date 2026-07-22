from pathlib import Path
import gzip
import shutil
import struct
import zlib

from twom_pack_common import murmur_hash
from twom_patch_russian_lang_structured import build_lang, parse_records
from twom_family_config import game_path, load_config, localization_values


CONFIG = load_config()
GAME = game_path(CONFIG)
DAT = GAME / "localizations.dat"
IDX = GAME / "localizations.idx"
TARGET = "russian.lang"
KEY_VALUES = localization_values(CONFIG)


def read_entries() -> list[dict[str, int]]:
    data = IDX.read_bytes()
    entries = []
    pos = 11
    while pos + 17 <= len(data):
        h, size, inflated, offset, compressed = struct.unpack_from("<IIIIB", data, pos)
        entries.append(
            {
                "idx_pos": pos,
                "hash": h,
                "size": size,
                "inflated": inflated,
                "offset": offset,
                "compressed": compressed,
            }
        )
        pos += 17
    return entries


def unpack_entry(dat: bytes, entry: dict[str, int]) -> bytes:
    payload = dat[entry["offset"] : entry["offset"] + entry["size"]]
    if entry["compressed"]:
        decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        payload = b"".join(
            decompressor.decompress(payload[i : i + 16384])
            for i in range(0, len(payload), 16384)
        )
    if len(payload) != entry["inflated"]:
        raise RuntimeError(f"Inflated size mismatch: got {len(payload)}, expected {entry['inflated']}")
    return payload


def patch_lang(payload: bytes) -> bytes:
    records = parse_records(payload)
    updated = []
    changes = 0
    for key, value in records:
        if key in KEY_VALUES and value != KEY_VALUES[key]:
            print(key, value, "->", KEY_VALUES[key])
            updated.append((key, KEY_VALUES[key]))
            changes += 1
        else:
            updated.append((key, value))
    print("changes", changes)
    return build_lang(updated)


def main() -> None:
    entries = read_entries()
    target_hash = murmur_hash(TARGET.encode("utf-8"))
    target_entry = next((entry for entry in entries if entry["hash"] == target_hash), None)
    if target_entry is None:
        raise RuntimeError(f"{TARGET} not found in {IDX}")

    stamp = "before-myfamily-base-russian-lang"
    backup_dat = DAT.with_suffix(f".dat.bak-codex-{stamp}")
    backup_idx = IDX.with_suffix(f".idx.bak-codex-{stamp}")
    if not backup_dat.exists():
        shutil.copy2(DAT, backup_dat)
    if not backup_idx.exists():
        shutil.copy2(IDX, backup_idx)
    print("backups", backup_dat, backup_idx)

    dat = bytearray(DAT.read_bytes())
    idx = bytearray(IDX.read_bytes())
    payload = unpack_entry(dat, target_entry)
    patched = patch_lang(payload)
    compressed = gzip.compress(patched, compresslevel=9, mtime=0)

    old_size = target_entry["size"]
    new_size = len(compressed)
    offset = target_entry["offset"]
    delta = new_size - old_size
    dat[offset : offset + old_size] = compressed
    struct.pack_into("<I", idx, target_entry["idx_pos"] + 4, new_size)
    struct.pack_into("<I", idx, target_entry["idx_pos"] + 8, len(patched))
    for entry in entries:
        if entry["offset"] > offset:
            entry["offset"] += delta
            struct.pack_into("<I", idx, entry["idx_pos"] + 12, entry["offset"])
    print("written", new_size, "/", old_size, "delta", delta)

    DAT.write_bytes(dat)
    IDX.write_bytes(idx)


if __name__ == "__main__":
    main()
