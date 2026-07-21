# Notes

## Why Patch Base Archives

The mod `common` container successfully changes the scenario and localization archives successfully change names, but character backpack sizes, model refs, and portrait atlas refs are loaded from base binary templates.

The working path is therefore targeted patching of compressed entries inside base archives:

- `templates.dat` / `templates.idx` for stock character templates.
- `textures-s3.dat` / `textures-s3.idx` for scenario and character portrait atlases.
- `localizations.dat` / `localizations.idx` for the base Russian UI strings used by the scenario selection screen.

The patchers replace only selected compressed entries and adjust subsequent offsets in the matching `.idx`.

The scenario selection screen did not consistently use the mod-localized `russian.lang` override for stock character names, so `twom_patch_base_russian_lang.py` also patches these base-game keys:

- `Names/Roman` -> `Ромакович`
- `Names/Emilia` -> `Катя`
- `Names/Arica` -> `Настя`
- `Names/Katia` -> `Бабуля`
- `CharacterSkills/Lawyer` -> `Хороший повар`
- `CharacterSkills/Thief` -> `Инженер-стелсер`

## Current Scenario

The active `MyFamily` scenario now starts with:

- `Dweller_Warrior` for Ромакович.
- `Dweller_Lawyer` for Катя.
- `Dweller_Female_Thief` for Настя.
- `Dweller_Trader` for Бабуля.

This is the safer full-body model path. Direct model-string swaps in old templates caused startup exits, while whole stock female templates launched successfully on 2026-07-22.

## Scenario Select Image

The scenario select card uses `UI/select/PhotoWindow_White.dds`.

The custom collage is patched into:

- `ui/select/photowindow_white.texture`

Putting a new `ui/select/myfamily_01.texture` inside the mod `common` container made the game show a black placeholder, so the reliable path is patching an existing texture slot in the base texture archive.

## In-Game Portraits

Current patched portrait atlas entries:

- `ui/characters/characters_02.texture`
- `ui/characters/characters_02_closed.texture`
- `ui/characters/characters_02_blinked.texture`
- `ui/characters/characters_03dirty_close.texture`
- `ui/characters/characters_03dirty_open.texture`

Current tiles:

- `Ромакович`: `Characters_02`, tile `(3, 0)`.
- `Катя`: `Characters_03Dirty`, tile `(1, 0)`, used by `Dweller_Lawyer`.
- `Настя`: `Characters_03Dirty`, tile `(0, 1)`, used by `Dweller_Female_Thief`.
- `Бабуля`: `Characters_02`, tile `(1, 2)`, used by `Dweller_Trader`.

## Known Limits

Some desired behavior is not yet implemented:

- True per-character depression immunity.
- Real Bruno cooking component on Katya's current female template.
- Real Marin crafting discount on Nastya's current female template.
- Grandma demotivating other characters through a custom morale aura.
- New radio/intel trading mechanic.

Those likely require deeper template/component work or Lua/game-code hooks.
