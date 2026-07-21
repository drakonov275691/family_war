from pathlib import Path
import gzip
import shutil
import struct
import zlib

from PIL import Image, ImageOps

from twom_pack_common import murmur_hash
from twom_make_myfamily_select_texture import encode_dxt5


GAME = Path(r"D:\Games\This War of Mine")
DAT = GAME / "textures-s3.dat"
IDX = GAME / "textures-s3.idx"
ROOT = Path(r"C:\Users\user\Downloads")

TARGETS = {
    "ui/characters/characters_03dirty_close.texture": "close",
    "ui/characters/characters_03dirty_open.texture": "open",
}

PORTRAITS = [
    # x tile, y tile, source image
    (1, 0, ROOT / "catya.jpg"),
    (0, 1, ROOT / "nasty.jpg"),
]

HEADER_SIZE = 144
ATLAS_SIZE = 2048
TILE_SIZE = 512
BLOCK_SIZE = 4
DXT5_BLOCK_BYTES = 16


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


def center_crop(img: Image.Image, size: int) -> Image.Image:
    img = ImageOps.exif_transpose(img).convert("RGB")
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return img.crop((left, top, left + side, top + side)).resize((size, size), Image.Resampling.LANCZOS)


def stylize(img: Image.Image) -> Image.Image:
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageOps.colorize(img, black="#111111", white="#e4e0d8")
    overlay = Image.new("RGB", img.size, "#242424")
    img = Image.blend(img, overlay, 0.12)
    return img.convert("RGBA")


def patch_tile(texture: bytearray, tile_x: int, tile_y: int, source: Path) -> None:
    tile_img = stylize(center_crop(Image.open(source), TILE_SIZE))
    encoded = encode_dxt5(tile_img)

    blocks_per_row = ATLAS_SIZE // BLOCK_SIZE
    tile_blocks = TILE_SIZE // BLOCK_SIZE
    row_bytes = blocks_per_row * DXT5_BLOCK_BYTES
    tile_row_bytes = tile_blocks * DXT5_BLOCK_BYTES
    block_x = tile_x * tile_blocks
    block_y = tile_y * tile_blocks

    for row in range(tile_blocks):
        dst = HEADER_SIZE + (block_y + row) * row_bytes + block_x * DXT5_BLOCK_BYTES
        src = row * tile_row_bytes
        texture[dst : dst + tile_row_bytes] = encoded[src : src + tile_row_bytes]
    print(source.name, "-> tile", (tile_x, tile_y))


def patch_texture(payload: bytes) -> bytes:
    texture = bytearray(payload)
    expected = HEADER_SIZE + (ATLAS_SIZE * ATLAS_SIZE // 16) * DXT5_BLOCK_BYTES
    if len(texture) != expected:
        raise RuntimeError(f"Unexpected texture size: {len(texture)} != {expected}")
    for tile_x, tile_y, source in PORTRAITS:
        patch_tile(texture, tile_x, tile_y, source)
    return bytes(texture)


def main() -> None:
    all_entries = read_all_entries()
    wanted = {murmur_hash(name.encode("utf-8")): name for name in TARGETS}
    entries = [entry for entry in all_entries if entry["hash"] in wanted]
    if len(entries) != len(TARGETS):
        raise RuntimeError(f"Found {len(entries)} texture entries, expected {len(TARGETS)}")

    stamp = "before-female-template-portraits"
    backup_dat = DAT.with_suffix(f".dat.bak-codex-{stamp}")
    backup_idx = IDX.with_suffix(f".idx.bak-codex-{stamp}")
    if not backup_dat.exists():
        shutil.copy2(DAT, backup_dat)
    if not backup_idx.exists():
        shutil.copy2(IDX, backup_idx)
    print("backups", backup_dat, backup_idx)

    dat = bytearray(DAT.read_bytes())
    idx = bytearray(IDX.read_bytes())
    replacements = []
    for entry in entries:
        payload = unpack_entry(dat, entry)
        patched = patch_texture(payload)
        compressed = gzip.compress(patched, compresslevel=9, mtime=0)
        replacements.append((entry, compressed, len(patched)))

    for entry, compressed, inflated in sorted(replacements, key=lambda item: item[0]["offset"], reverse=True):
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
        print("written", new_size, "/", old_size, "delta", delta)

    DAT.write_bytes(dat)
    IDX.write_bytes(idx)


if __name__ == "__main__":
    main()
