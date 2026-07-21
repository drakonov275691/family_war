from pathlib import Path
import struct
import sys
import zlib


def read_filemap(path: Path) -> dict[int, str]:
    names: dict[int, str] = {}
    data = path.read_bytes()
    pos = 0
    while pos + 4 <= len(data):
        h = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        end = data.find(b"\n", pos)
        if end == -1:
            break
        names[h] = data[pos:end].decode("utf-8", errors="replace")
        pos = end + 1
    return names


def extract(container: str, game_dir: Path, out_dir: Path, filemap: dict[int, str]) -> None:
    idx = game_dir / f"{container}.idx"
    dat = game_dir / f"{container}.dat"
    index = idx.read_bytes()
    data = dat.read_bytes()
    pos = 11
    target_root = out_dir / container
    target_root.mkdir(parents=True, exist_ok=True)
    while pos + 17 <= len(index):
        h, size, inflated_size, offset, compressed = struct.unpack_from("<IIIIB", index, pos)
        pos += 17
        payload = data[offset:offset + size]
        if compressed:
            inflater = zlib.decompressobj(16 + zlib.MAX_WBITS)
            payload = inflater.decompress(payload)
        name = filemap.get(h, str(h))
        target = target_root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("usage: twom_extract.py <container> <game_dir> <out_dir> <filemap>")
        raise SystemExit(2)
    extract(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), read_filemap(Path(sys.argv[4])))
