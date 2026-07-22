from pathlib import Path
import gzip
import re
import shutil
import struct
import subprocess
import time
import zlib

from twom_pack_common import murmur_hash
from twom_family_config import (
    character_by_id,
    documents_mod_source,
    documents_mods_dir,
    game_mod_dir,
    game_mod_source,
    game_path,
    load_config,
    mod_id,
    scenario_name,
    scenario_templates,
    target_templates,
)


CONFIG = load_config()
GAME = game_path(CONFIG)
MOD_SOURCE = documents_mod_source(CONFIG)
MOD_ID = mod_id(CONFIG)
DOC_MODS = documents_mods_dir()
GAME_MOD_DIR = game_mod_dir(CONFIG)
GAME_MOD_SOURCE = game_mod_source(CONFIG)
OUT_ROOT = Path(r"C:\Users\user\Downloads\thiswarofmine\packroot_myfamily_female_templates")

TEMPLATES_DAT = GAME / "templates.dat"
TEMPLATES_IDX = GAME / "templates.idx"

TARGETS = target_templates(CONFIG)
CHARACTERS = character_by_id(CONFIG)


def read_all_entries() -> list[dict[str, int]]:
    data = TEMPLATES_IDX.read_bytes()
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
            print(name, "size", entry["size"], "inflated", entry["inflated"])
    missing = set(TARGETS.values()) - set(entries)
    if missing:
        raise RuntimeError(f"Missing template entries: {sorted(missing)}")
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
            print("backpack", old, "->", new)
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
    print("backpack", old, "->", new)


def patch_portrait_tile(data: bytearray, marker: bytes, values: tuple[float, float, float, float]) -> None:
    pos = data.find(marker)
    if pos < 0:
        print("portrait marker missing")
        return
    tile_pos = pos + len(marker)
    old = struct.unpack_from("<ffff", data, tile_pos)
    struct.pack_into("<ffff", data, tile_pos, *values)
    print("portrait", old, "->", values)


def patch_hp(data: bytearray, health: float) -> None:
    name = b"KosovoHPComponentConfig"
    pos = data.find(name)
    if pos >= 0:
        set_float(data, pos + len(name) + 2, health)
        print("hp ->", health)


def patch_combat(data: bytearray, hit: float, close_hit: float) -> None:
    name = b"KosovoCombatComponentConfig"
    pos = data.find(name)
    if pos >= 0:
        set_float(data, pos + len(name) + 1, hit)
        set_float(data, pos + len(name) + 5, close_hit)
        print("combat ->", hit, close_hit)


def patch_trading(data: bytearray, value: float) -> None:
    name = b"KosovoTradingClientComponentConfig"
    pos = data.find(name)
    if pos >= 0:
        set_float(data, pos + len(name) + 2, value)
        print("trading ->", value)


def patch_payload(label: str, payload: bytes) -> bytes:
    data = bytearray(payload)
    char = CHARACTERS[label]
    stats = char.get("stats", {})
    print("\npatch", label)

    if "backpack" in stats:
        new_backpack = int(stats["backpack"])
        old_values = [new_backpack] + list(stats.get("backpack_search_values", []))
        patch_backpack(data, list(dict.fromkeys(old_values)), new_backpack)
    if "hp" in stats:
        patch_hp(data, float(stats["hp"]))
    if "combat_hit" in stats or "combat_close_hit" in stats:
        patch_combat(
            data,
            float(stats.get("combat_hit", 1.0)),
            float(stats.get("combat_close_hit", stats.get("combat_hit", 1.0))),
        )
    if "trading_value" in stats:
        patch_trading(data, float(stats["trading_value"]))

    markers = {
        "Characters_02": b"UI/Characters/Characters_02_Closed.dds\x00",
        "Characters_03Dirty": b"UI/Characters/Characters_03Dirty_close.dds\x00",
    }
    atlas = char.get("portrait_atlas")
    if atlas in markers:
        tile_x, tile_y = char["atlas_tile"]
        patch_portrait_tile(data, markers[atlas], (float(tile_x), float(tile_y), 4.0, 4.0))
    return bytes(data)


def update_scenario_xml(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    entries = "\n".join(
        f'                        <Entry Value="{template}" />'
        for template in scenario_templates(CONFIG)
    )
    pattern = (
        r'(<Properties ClassName="KosovoInitialDwellerSet">\s*'
        rf'<Prop Name="Name" Value="{re.escape(scenario_name(CONFIG))}" />.*?'
        r'<Prop Name="DwellerTemplates">\s*)'
        r'.*?'
        r'(\s*</Prop>)'
    )
    updated, count = re.subn(pattern, rf"\1{entries}\2", text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"Could not update {scenario_name(CONFIG)} DwellerTemplates in {path}")
    path.write_text(updated, encoding="utf-8")
    print("scenario templates ->", ", ".join(scenario_templates(CONFIG)))


def patch_templates_dat() -> dict[str, bytes]:
    all_entries = read_all_entries()
    entries = find_entries(all_entries)
    dat = bytearray(TEMPLATES_DAT.read_bytes())
    idx = bytearray(TEMPLATES_IDX.read_bytes())

    stamp = "before-female-template-models"
    backup_dat = TEMPLATES_DAT.with_suffix(f".dat.bak-codex-{stamp}")
    backup_idx = TEMPLATES_IDX.with_suffix(f".idx.bak-codex-{stamp}")
    if not backup_dat.exists():
        shutil.copy2(TEMPLATES_DAT, backup_dat)
    if not backup_idx.exists():
        shutil.copy2(TEMPLATES_IDX, backup_idx)
    print("backups", backup_dat, backup_idx)

    patched_payloads = {}
    replacements = []
    for label, entry in entries.items():
        old_payload = unpack_entry(dat, entry)
        new_payload = patch_payload(label, old_payload)
        patched_payloads[label] = new_payload
        compressed = gzip.compress(new_payload, compresslevel=9, mtime=0)
        if not entry["compressed"]:
            compressed = new_payload
        replacements.append((label, entry, compressed, len(new_payload)))

    for label, entry, compressed, inflated in sorted(
        replacements, key=lambda item: item[1]["offset"], reverse=True
    ):
        old_size = entry["size"]
        new_size = len(compressed)
        offset = entry["offset"]
        delta = new_size - old_size
        dat[offset : offset + old_size] = compressed
        struct.pack_into("<I", idx, entry["idx_pos"] + 4, new_size)
        struct.pack_into("<I", idx, entry["idx_pos"] + 8, inflated)
        for other in all_entries:
            if other["offset"] > offset:
                other["offset"] += delta
                struct.pack_into("<I", idx, other["idx_pos"] + 12, other["offset"])
        print(label, "written", new_size, "/", old_size, "delta", delta)

    TEMPLATES_DAT.write_bytes(dat)
    TEMPLATES_IDX.write_bytes(idx)
    return patched_payloads


def run_modtools_common() -> None:
    update_scenario_xml(MOD_SOURCE / "ScenariosConfig.xml")
    shutil.copy2(MOD_SOURCE / "ScenariosConfig.xml", GAME_MOD_SOURCE / "ScenariosConfig.xml")
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out_name = f"{MOD_ID}_female_models_{stamp}"
    out_dir = MOD_SOURCE.parent / out_name
    cmd = [
        str(GAME / "ModToolsNS.exe"),
        "-bcommon",
        f"Mods/MyFamilyMod/{MOD_ID}",
        f"Mods/MyFamilyMod/{out_name}",
    ]
    print("run", " ".join(cmd))
    subprocess.run(cmd, cwd=GAME, check=False)
    built = MOD_SOURCE / "ScenariosConfig.bin"
    if not built.exists():
        raise RuntimeError(f"ModTools did not produce {built}")
    print("compiled", built)


def pack_active_common(payloads: dict[str, bytes]) -> None:
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)
    target = OUT_ROOT / "characters" / "player_characters"
    target.mkdir(parents=True)
    mapping = {
        char["id"]: Path(char["template_path"]).name
        for char in CHARACTERS.values()
    }
    for label, filename in mapping.items():
        (target / filename).write_bytes(payloads[label])
    shutil.copy2(MOD_SOURCE / "ScenariosConfig.bin", OUT_ROOT / "ScenariosConfig.bin")

    out_base = DOC_MODS / f"{MOD_ID}_common"
    subprocess.run(
        [
            "python",
            str(Path(__file__).with_name("twom_pack_mod_common.py")),
            str(OUT_ROOT),
            str(out_base),
        ],
        check=True,
    )

    GAME_MOD_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in (".dat", ".idx", ".str"):
        shutil.copy2(out_base.with_suffix(suffix), GAME_MOD_DIR / out_base.with_suffix(suffix).name)
    print("active common packed", out_base)


def main() -> None:
    run_modtools_common()
    payloads = patch_templates_dat()
    pack_active_common(payloads)


if __name__ == "__main__":
    main()
