from pathlib import Path
import struct
import sys


def murmur_hash(data: bytes, seed: int = 0) -> int:
    m = 0x5BD1E995
    r = 24
    length = len(data)
    h = (seed ^ length) & 0xFFFFFFFF
    pos = 0
    while length >= 4:
        k = struct.unpack_from("<I", data, pos)[0]
        k = (k * m) & 0xFFFFFFFF
        k ^= k >> r
        k = (k * m) & 0xFFFFFFFF
        h = (h * m) & 0xFFFFFFFF
        h ^= k
        pos += 4
        length -= 4
    if length == 3:
        h ^= data[pos + 2] << 16
    if length >= 2:
        h ^= data[pos + 1] << 8
    if length >= 1:
        h ^= data[pos]
        h = (h * m) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * m) & 0xFFFFFFFF
    h ^= h >> 15
    return h & 0xFFFFFFFF


def collect(root: Path) -> list[tuple[int, bytes, bytes]]:
    files: list[tuple[int, bytes, bytes]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        payload = path.read_bytes()
        files.append((murmur_hash(rel.encode("utf-8")), rel.encode("utf-8"), payload))
    return sorted(files, key=lambda item: item[0])


def pack(root: Path, out_base: Path) -> None:
    files = collect(root)
    dat_path = out_base.with_suffix(".dat")
    idx_path = out_base.with_suffix(".idx")
    str_path = out_base.with_suffix(".str")
    offset = 0
    entries = []
    with dat_path.open("wb") as dat:
        for h, rel, payload in files:
            dat.write(payload)
            entries.append((h, len(payload), len(payload), offset, 0))
            offset += len(payload)
    with idx_path.open("wb") as idx:
        idx.write(bytes([0x00, 0x06, 0x01]))
        idx.write(struct.pack("<I", len(entries)))
        idx.write(bytes([0x00, 0x00, 0x00, 0x00]))
        for entry in entries:
            idx.write(struct.pack("<IIIIB", *entry))
    # Some containers, like common/localizations, may have a .str companion.
    # templates in the base game does not, so callers can simply ignore this file.
    str_path.write_bytes(b"\x00\x00\x00\x00")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: twom_pack_common.py <root> <out_without_extension>")
        raise SystemExit(2)
    pack(Path(sys.argv[1]), Path(sys.argv[2]))
