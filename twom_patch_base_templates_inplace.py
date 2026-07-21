from pathlib import Path
import gzip
import shutil
import struct
import zlib

from twom_pack_common import murmur_hash


GAME = Path(r"D:\Games\This War of Mine")
DAT = GAME / "templates.dat"
IDX = GAME / "templates.idx"

TARGETS = {
    "characters/player_characters/dweller_warrior.binarytemplate": "warrior",
    "characters/player_characters/dweller_trader.binarytemplate": "trader",
    "characters/player_characters/dweller_crafter.binarytemplate": "crafter",
    "characters/player_characters/dweller_cook.binarytemplate": "cook",
}


def read_all_entries() -> list[dict[str, int]]:
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


def find_entries(all_entries: list[dict[str, int]]) -> dict[str, dict[str, int]]:
    wanted = {murmur_hash(name.encode("utf-8")): (name, label) for name, label in TARGETS.items()}
    entries = {}
    for entry in all_entries:
        if entry["hash"] in wanted:
            name, label = wanted[entry["hash"]]
            entries[label] = entry
            print(
                name,
                "idx",
                entry["idx_pos"],
                "size",
                entry["size"],
                "inflated",
                entry["inflated"],
                "offset",
                entry["offset"],
                "compressed",
                entry["compressed"],
            )
    missing = set(TARGETS.values()) - set(entries)
    if missing:
        raise RuntimeError(f"Missing template entries: {sorted(missing)}")
    return entries


def unpack_entry(dat: bytes, entry: dict[str, int]) -> bytes:
    size = entry["size"]
    inflated = entry["inflated"]
    offset = entry["offset"]
    compressed = entry["compressed"]
    payload = dat[offset : offset + size]
    if compressed:
        decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
        payload = b"".join(
            decompressor.decompress(payload[i : i + 16384])
            for i in range(0, len(payload), 16384)
        )
    if len(payload) != inflated:
        raise RuntimeError(f"Inflated size mismatch: got {len(payload)}, expected {inflated}")
    return payload


def set_float(data: bytearray, offset: int, value: float) -> None:
    data[offset : offset + 4] = struct.pack("<f", value)


def set_int(data: bytearray, offset: int, value: int) -> None:
    data[offset : offset + 4] = struct.pack("<I", value)


def patch_backpack(data: bytearray, old_values: list[int], new: int) -> None:
    for old in old_values:
        pattern = b"\x01" + struct.pack("<I", old) + b"\x00\x00\x00\x3f"
        pos = data.rfind(pattern)
        if pos >= 0:
            set_int(data, pos + 1, new)
            print("backpack", old, "->", new, "at", pos + 1)
            return

    tail_start = max(0, len(data) - 96)
    matches = []
    for old in old_values:
        old_bytes = struct.pack("<I", old)
        start = tail_start
        while True:
            pos = data.find(old_bytes, start)
            if pos < 0:
                break
            matches.append((pos, old))
            start = pos + 1
    if not matches:
        raise ValueError(f"Backpack value {old_values} not found")
    pos, old = matches[-1]
    set_int(data, pos, new)
    print("backpack", old, "->", new, "at", pos)


def patch_portrait_tile(data: bytearray, values: tuple[float, float, float, float]) -> None:
    marker = b"UI/Characters/Characters_02_Closed.dds\x00"
    pos = data.find(marker)
    if pos < 0:
        print("portrait tile marker missing, skipped")
        return
    tile_pos = pos + len(marker)
    old = struct.unpack_from("<ffff", data, tile_pos)
    struct.pack_into("<ffff", data, tile_pos, *values)
    print("portrait tile", old, "->", values)


def patch_hp(data: bytearray, health: float) -> None:
    name = b"KosovoHPComponentConfig"
    pos = data.find(name)
    if pos < 0:
        print("hp component missing, skipped")
        return
    set_float(data, pos + len(name) + 2, health)
    print("hp ->", health)


def patch_combat(data: bytearray, hit: float, close_hit: float) -> None:
    name = b"KosovoCombatComponentConfig"
    pos = data.find(name)
    if pos < 0:
        print("combat component missing, skipped")
        return
    set_float(data, pos + len(name) + 1, hit)
    set_float(data, pos + len(name) + 5, close_hit)
    print("combat ->", hit, close_hit)


def patch_trading(data: bytearray, value: float) -> None:
    name = b"KosovoTradingClientComponentConfig"
    pos = data.find(name)
    if pos < 0:
        print("trading component missing, skipped")
        return
    set_float(data, pos + len(name) + 2, value)
    print("trading ->", value)


def patch_first_craftsman_values(data: bytearray, values: list[float]) -> None:
    name = b"KosovoCraftsmanComponentConfig"
    pos = data.find(name)
    if pos < 0:
        print("craftsman component missing, skipped")
        return
    end = data.find(b"\x01Kosovo", pos + len(name))
    if end < 0:
        end = len(data)
    found = []
    for i in range(pos + len(name), end - 4):
        f = struct.unpack_from("<f", data, i)[0]
        if any(abs(f - expected) < 0.0001 for expected in (0.3, 0.4, 0.5, 0.75, 0.8, 1.0)):
            found.append(i)
    if len(found) < len(values):
        raise ValueError(f"Need {len(values)} craftsman floats, found {len(found)}")
    for off, value in zip(found, values):
        set_float(data, off, value)
        print("craftsman float at", off, "->", value)


def patch_payload(label: str, payload: bytes) -> bytes:
    data = bytearray(payload)
    print("\npatch", label)
    if label == "warrior":
        patch_backpack(data, [10, 40], 40)
        patch_hp(data, 180.0)
        patch_combat(data, 1.0, 0.9)
        patch_portrait_tile(data, (3.0, 0.0, 4.0, 4.0))
    elif label == "trader":
        patch_backpack(data, [12, 8], 8)
        patch_trading(data, 0.5)
        patch_portrait_tile(data, (1.0, 2.0, 4.0, 4.0))
    elif label == "crafter":
        patch_backpack(data, [10, 14], 14)
        patch_first_craftsman_values(data, [0.5])
        patch_portrait_tile(data, (2.0, 1.0, 4.0, 4.0))
    elif label == "cook":
        patch_backpack(data, [10, 8, 12], 12)
        patch_first_craftsman_values(data, [0.3, 0.4, 0.4])
        patch_portrait_tile(data, (0.0, 1.0, 4.0, 4.0))
    return bytes(data)


def main() -> None:
    all_entries = read_all_entries()
    entries = find_entries(all_entries)
    dat = bytearray(DAT.read_bytes())
    idx = bytearray(IDX.read_bytes())

    stamp = "before-inplace-stats"
    backup_dat = DAT.with_suffix(f".dat.bak-codex-{stamp}")
    backup_idx = IDX.with_suffix(f".idx.bak-codex-{stamp}")
    if not backup_dat.exists():
        shutil.copy2(DAT, backup_dat)
    if not backup_idx.exists():
        shutil.copy2(IDX, backup_idx)
    print("backups", backup_dat, backup_idx)

    replacements = []
    for label, entry in entries.items():
        old_payload = unpack_entry(dat, entry)
        new_payload = patch_payload(label, old_payload)
        if len(new_payload) != len(old_payload):
            raise RuntimeError(f"{label}: payload length changed")
        compressed = gzip.compress(new_payload, compresslevel=9, mtime=0)
        old_size = entry["size"]
        inflated = entry["inflated"]
        offset = entry["offset"]
        if not entry["compressed"]:
            compressed = new_payload
        replacements.append((label, entry, compressed))

    for label, entry, compressed in sorted(replacements, key=lambda item: item[1]["offset"], reverse=True):
        old_size = entry["size"]
        new_size = len(compressed)
        offset = entry["offset"]
        delta = new_size - old_size
        dat[offset : offset + old_size] = compressed
        struct.pack_into("<I", idx, entry["idx_pos"] + 4, new_size)
        struct.pack_into("<I", idx, entry["idx_pos"] + 8, entry["inflated"])
        for other in all_entries:
            if other["offset"] > offset:
                other["offset"] += delta
                struct.pack_into("<I", idx, other["idx_pos"] + 12, other["offset"])
        print(label, "written", new_size, "/", old_size, "delta", delta)

    DAT.write_bytes(dat)
    IDX.write_bytes(idx)


if __name__ == "__main__":
    main()
