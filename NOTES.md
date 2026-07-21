# Notes

## Why Patch `templates.dat`

The mod `common` container successfully changes scenario config and localization archives successfully change names, but character backpack sizes are loaded from base binary templates.

The working path for stats is therefore a targeted patch of these entries inside base `templates.dat`:

- `characters/player_characters/dweller_warrior.binarytemplate`
- `characters/player_characters/dweller_trader.binarytemplate`
- `characters/player_characters/dweller_crafter.binarytemplate`
- `characters/player_characters/dweller_cook.binarytemplate`

The patcher replaces only those compressed entries and adjusts subsequent offsets in `templates.idx`.

## Current Limitation

Some desired behavior is not yet implemented:

- Custom full-body character models.
- True per-character depression immunity.
- Grandma demotivating other characters through a custom morale aura.
- New radio/intel trading mechanic.

Those likely require deeper template/component work or Lua/game-code hooks.

## Scenario Select Image

The scenario select card now uses `UI/select/PhotoWindow_White.dds`.

The custom collage is patched into the base `textures-s3.dat` entry:

- `ui/select/photowindow_white.texture`

Putting a new `ui/select/myfamily_01.texture` inside the mod `common` container made the game show a black placeholder, so the reliable path is patching an existing texture slot in the base texture archive.

## In-Game Portraits

The lower-right in-game character cards use the base character atlas:

- `ui/characters/characters_02.texture`
- `ui/characters/characters_02_closed.texture`
- `ui/characters/characters_02_blinked.texture`

Current patched tiles:

- `Ромакович`: tile `(3, 0)`.
- `Катя`: tile `(0, 1)`, used by `Dweller_Cook`.
- `Настя`: tile `(2, 1)`.
- `Бабуля`: tile `(1, 2)`, used by `Dweller_Trader`.

`Dweller_Cook` is patched to portrait tile `(0, 1)`, and `Dweller_Trader` is patched to `(1, 2)` so Катя is the cook and Бабуля is the trader.

## Full-Body Models

Directly replacing `GFX/CHARACTERS/RDY2/...` model references in the dweller templates was tested and rolled back because the game exited during startup.

The attempted set was:

- `Dweller_Cook`: `bruno` -> `kucharka`.
- `Dweller_Crafter`: `marin` -> `zlodziejka`.
- `Dweller_Trader`: `katia` -> `ciocia_nauczycielka`.

Changing `Male_Protector` to `Female_Protector` for the converted templates did not fix the startup exit. The current stable build keeps the stock full-body models and only changes portrait cards, names, roles, and stats.
