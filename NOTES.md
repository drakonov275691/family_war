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

- Custom in-game portraits.
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
- `Катя`: tile `(0, 1)`.
- `Настя`: tile `(2, 1)`.
- `Бабуля`: tile `(1, 2)`.

`Dweller_Cook` was also patched from portrait tile `(2, 0)` to `(1, 2)` so Бабуля does not share another stock portrait slot.
