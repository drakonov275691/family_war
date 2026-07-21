from pathlib import Path
import struct
import sys

from twom_pack_common import murmur_hash


HEADER = bytes([0x00, 0x03, 0x00])


def collect(root: Path) -> list[tuple[int, str, bytes]]:
    files: list[tuple[int, str, bytes]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix().lower()
        files.append((murmur_hash(rel.encode("utf-8")), rel, path.read_bytes()))
    return sorted(files, key=lambda item: item[0])


def pack(root: Path, out_base: Path) -> None:
    files = collect(root)
    out_base.parent.mkdir(parents=True, exist_ok=True)
    dat_path = out_base.with_suffix(".dat")
    idx_path = out_base.with_suffix(".idx")
    str_path = out_base.with_suffix(".str")

    entries = []
    offset = 0
    with dat_path.open("wb") as dat:
        for h, rel, payload in files:
            dat.write(payload)
            entries.append((h, len(payload), len(payload), offset, 0, rel))
            offset += len(payload)

    with idx_path.open("wb") as idx:
        idx.write(HEADER)
        idx.write(struct.pack("<I", len(entries)))
        idx.write(b"\x00\x00\x00\x00")
        for h, size, inflated_size, file_offset, compressed, _ in entries:
            idx.write(struct.pack("<IIIIB", h, size, inflated_size, file_offset, compressed))

    with str_path.open("wb") as str_file:
        str_file.write(HEADER)
        str_file.write(struct.pack("<I", len(entries)))
        str_file.write(b"\x00\x00\x00\x00")
        for h, _, _, _, _, rel in entries:
            encoded = rel.encode("utf-8")
            str_file.write(struct.pack("<II", h, len(encoded)))
            str_file.write(encoded)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: twom_pack_mod_common.py <root> <out_without_extension>")
        raise SystemExit(2)
    pack(Path(sys.argv[1]), Path(sys.argv[2]))
