# This War of Mine: MyFamily Patch Tools

Small personal patching toolkit for a custom **This War of Mine** family scenario.

This repository intentionally does **not** include game archives, extracted game assets, screenshots, or personal portraits. It only contains scripts that patch a local copy of the game/mod on the owner's machine.

## What It Does

- Keeps the working `MyFamilyMod` scenario enabled.
- Patches Russian localization names:
  - `Roman` -> `Ромакович`
  - `Katia` -> `Бабуля`
  - `Emilia` -> `Катя`
  - `Arica` -> `Настя`
- Uses a safer full-body model experiment: the current scenario starts with `Dweller_Warrior`, `Dweller_Lawyer`, and `Dweller_Trader`.
- `scenario_character_ids` in `characters.json` controls which configured characters actually start in the scenario.
- Patches base `templates.dat` in place for the stock templates used by the scenario:
  - `Dweller_Warrior`: 40-slot backpack, high HP, strong combat.
  - `Dweller_Trader`: 8-slot backpack, stronger trader value.
  - `Dweller_Lawyer`: 12-slot backpack and Katya's female model.
  - `Dweller_Female_Thief`: 14-slot backpack and Nastya's female stealth model.

See [CHARACTER_STATS.md](CHARACTER_STATS.md) for the current character setup.

## Important

Back up the game before patching. The in-place patchers also create local backups.

The scripts are currently tuned for:

```text
D:\Games\This War of Mine
C:\Users\user\Documents\This War of Mine\Mods\MyFamilyMod
```

## Useful Commands

Edit the family config:

```text
characters.json
```

Then apply it to the local game files:

```powershell
python .\twom_apply_family_config.py
```

Close the game before running the command. The game does not read `characters.json` directly; the script patches/re-packs the `.dat` / `.idx` archives that the game actually loads.

Pack a mod common container:

```powershell
python .\twom_pack_mod_common.py <root> <out_without_extension>
```

## Restore

If the base template patch ever needs to be reverted:

```powershell
Copy-Item 'D:\Games\This War of Mine\templates.dat.bak-codex-before-inplace-stats' 'D:\Games\This War of Mine\templates.dat' -Force
Copy-Item 'D:\Games\This War of Mine\templates.idx.bak-codex-before-inplace-stats' 'D:\Games\This War of Mine\templates.idx' -Force
```
