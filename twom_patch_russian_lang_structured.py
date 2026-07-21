from pathlib import Path


TARGET = Path(
    r"C:\Users\user\Documents\This War of Mine\Mods\MyFamilyMod"
    r"\30be2babe4ac457c836a07462a83a65e\localizations\russian.lang"
)

PATCHES = {
    "\u0420\u043e\u043c\u0430\u043d": "\u0413\u043e\u0441\u0438\u043a",
    "\u0411\u0440\u0443\u043d\u043e": "\u0411\u0430\u0431\u043a\u0430",
    "\u041c\u0430\u0440\u0438\u043d": "\u041d\u0430\u0441\u0442\u044f",
    "\u041c\u044d\u0439\u0440\u0438\u043d": "\u041d\u0430\u0441\u0442\u044f",
}


def read_u16(data: bytes, pos: int) -> tuple[int, int]:
    return int.from_bytes(data[pos : pos + 2], "little"), pos + 2


def parse_records(data: bytes) -> list[tuple[str, str]]:
    pos = 8
    records = []
    while pos < len(data):
        key_len, pos = read_u16(data, pos)
        key = data[pos : pos + key_len].decode("utf-8")
        pos += key_len

        value_len, pos = read_u16(data, pos)
        value_bytes = data[pos : pos + value_len * 2]
        value = value_bytes.decode("utf-16le")
        pos += value_len * 2
        records.append((key, value))
    if pos != len(data):
        raise ValueError(f"Trailing bytes after parse: {len(data) - pos}")
    return records


def build_lang(records: list[tuple[str, str]]) -> bytes:
    body = bytearray()
    for key, value in records:
        key_bytes = key.encode("utf-8")
        value_bytes = value.encode("utf-16le")
        body += len(key_bytes).to_bytes(2, "little")
        body += key_bytes
        body += len(value).to_bytes(2, "little")
        body += value_bytes

    header = bytearray()
    header += (len(body) + 4).to_bytes(4, "little")
    header += len(records).to_bytes(4, "little")
    return bytes(header + body)


if __name__ == "__main__":
    payload = TARGET.read_bytes()
    records = parse_records(payload)
    changes = 0
    updated = []
    for key, value in records:
        new_value = value
        for old, new in PATCHES.items():
            if old in new_value:
                occurrences = new_value.count(old)
                changes += occurrences
                print(f"{key}: {old} -> {new} ({occurrences})")
                new_value = new_value.replace(old, new)
        updated.append((key, new_value))

    if changes == 0:
        print("No changes needed")
    else:
        TARGET.write_bytes(build_lang(updated))
        print(f"Updated {changes} text occurrence(s)")
