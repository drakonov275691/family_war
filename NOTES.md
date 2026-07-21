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
