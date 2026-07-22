from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONFIG_PATH = Path(__file__).with_name("characters.json")


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def game_path(config: dict[str, Any]) -> Path:
    return Path(config["game_path"])


def mod_id(config: dict[str, Any]) -> str:
    return config["mod_id"]


def mod_folder_name(config: dict[str, Any]) -> str:
    return config.get("mod_folder_name", "MyFamilyMod")


def scenario_name(config: dict[str, Any]) -> str:
    return config.get("scenario_name", "MyFamily")


def documents_mod_source(config: dict[str, Any]) -> Path:
    return (
        Path.home()
        / "Documents"
        / "This War of Mine"
        / "Mods"
        / mod_folder_name(config)
        / mod_id(config)
    )


def documents_mods_dir() -> Path:
    return Path.home() / "Documents" / "This War of Mine" / "Mods"


def game_mod_dir(config: dict[str, Any]) -> Path:
    return game_path(config) / "Mods" / mod_folder_name(config)


def game_mod_source(config: dict[str, Any]) -> Path:
    return game_mod_dir(config) / mod_id(config)


def characters(config: dict[str, Any]) -> list[dict[str, Any]]:
    return list(config["characters"])


def target_templates(config: dict[str, Any]) -> dict[str, str]:
    return {char["template_path"].lower(): char["id"] for char in characters(config)}


def character_by_id(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {char["id"]: char for char in characters(config)}


def localization_values(config: dict[str, Any]) -> dict[str, str]:
    values: dict[str, str] = {}
    for char in characters(config):
        values[char["base_name_key"]] = char["display_name"]
        skill_key = char.get("skill_key")
        skill_text = char.get("skill_text")
        if skill_key and skill_text:
            values[skill_key] = skill_text
        bio_key = char.get("bio_key")
        bio_text = char.get("bio_text")
        if bio_key and bio_text:
            values[bio_key] = bio_text
        death_note_key = char.get("death_note_key")
        death_note_text = char.get("death_note_text")
        if death_note_key and death_note_text:
            values[death_note_key] = death_note_text
    return values


def scenario_templates(config: dict[str, Any]) -> list[str]:
    return [char["scenario_template"] for char in characters(config)]
