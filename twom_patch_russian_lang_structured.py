from pathlib import Path


TARGETS = [
    Path(
    r"C:\Users\user\Documents\This War of Mine\Mods\MyFamilyMod"
    r"\30be2babe4ac457c836a07462a83a65e\localizations\russian.lang"
    ),
    Path(
        r"D:\Games\This War of Mine\Mods\MyFamilyMod"
        r"\30be2babe4ac457c836a07462a83a65e\localizations\russian.lang"
    ),
]

PATCHES = {
    "\u0420\u043e\u043c\u0430\u043d": "\u0420\u043e\u043c\u0430\u043a\u043e\u0432\u0438\u0447",
    "\u0413\u043e\u0441\u0438\u043a": "\u0420\u043e\u043c\u0430\u043a\u043e\u0432\u0438\u0447",
    "\u041c\u0430\u0440\u0438\u043d": "\u041d\u0430\u0441\u0442\u044f",
    "\u041c\u044d\u0439\u0440\u0438\u043d": "\u041d\u0430\u0441\u0442\u044f",
}

KEY_VALUES = {
    "Names/Bruno": "\u041a\u0430\u0442\u044f",
    "Names/Katia": "\u0411\u0430\u0431\u0443\u043b\u044f",
    "Names/Emilia": "\u041a\u0430\u0442\u044f",
    "Names/Arica": "\u041d\u0430\u0441\u0442\u044f",
    "CharacterSkills/Lawyer": "\u0425\u043e\u0440\u043e\u0448\u0438\u0439 \u043f\u043e\u0432\u0430\u0440",
    "CharacterSkills/Thief": "\u0418\u043d\u0436\u0435\u043d\u0435\u0440-\u0441\u0442\u0435\u043b\u0441\u0435\u0440",
}

KEY_REPLACEMENTS = {
    "CharacterBios/Cook/Bio": {
        "\u041a\u0443\u0445\u043d\u044f \u0411\u0430\u0431\u0443\u043b\u044f": "\u041a\u0443\u0445\u043d\u044f \u041a\u0430\u0442\u044f",
        "\u0411\u0430\u0431\u0443\u043b\u044f": "\u041a\u0430\u0442\u044f",
    },
    "CharacterBios/Cook/DeathNote": {
        "\u0411\u0430\u0431\u0443\u043b\u044f": "\u041a\u0430\u0442\u044f",
    },
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


def patch_file(target: Path) -> None:
    payload = target.read_bytes()
    records = parse_records(payload)
    changes = 0
    updated = []
    for key, value in records:
        new_value = value
        if key in KEY_VALUES:
            new_value = KEY_VALUES[key]
            if new_value != value:
                changes += 1
                print(f"{key}: {value} -> {new_value}")
            updated.append((key, new_value))
            continue

        for old, new in KEY_REPLACEMENTS.get(key, {}).items():
            if old in new_value:
                occurrences = new_value.count(old)
                changes += occurrences
                print(f"{key}: {old} -> {new} ({occurrences})")
                new_value = new_value.replace(old, new)

        for old, new in PATCHES.items():
            if old in new_value:
                occurrences = new_value.count(old)
                changes += occurrences
                print(f"{key}: {old} -> {new} ({occurrences})")
                new_value = new_value.replace(old, new)
        updated.append((key, new_value))

    if changes == 0:
        print(target, "No changes needed")
    else:
        target.write_bytes(build_lang(updated))
        print(target, f"Updated {changes} text occurrence(s)")


if __name__ == "__main__":
    for target in TARGETS:
        patch_file(target)
