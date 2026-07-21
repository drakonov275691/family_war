# This War of Mine: MyFamily Patch Tools

Small personal patching toolkit for a custom **This War of Mine** family scenario.

This repository intentionally does **not** include game archives, extracted game assets, screenshots, or personal portraits. It only contains scripts that patch a local copy of the game/mod on the owner's machine.

## What It Does

- Keeps the working `MyFamilyMod` scenario enabled.
- Patches Russian localization names:
  - `Roman` -> `Госик`
  - `Katia` -> `Катя`
  - `Marin / Мэйрин` -> `Настя`
  - `Bruno` -> `Бабка`
- Patches base `templates.dat` in place for the four stock templates used by the scenario:
  - `Dweller_Warrior`: 40-slot backpack, high HP, strong combat.
  - `Dweller_Trader`: stronger trader value.
  - `Dweller_Crafter`: 14-slot backpack, stronger crafting discount.
  - `Dweller_Cook`: 8-slot backpack, stronger food/medicine crafting discounts.

## Important

Back up the game before patching. The main in-place patcher also creates local backups:

- `D:\Games\This War of Mine\templates.dat.bak-codex-before-inplace-stats`
- `D:\Games\This War of Mine\templates.idx.bak-codex-before-inplace-stats`

The scripts are currently tuned for:

```text
D:\Games\This War of Mine
C:\Users\user\Documents\This War of Mine\Mods\MyFamilyMod
```

## Useful Commands

Patch base character templates:

```powershell
python .\twom_patch_base_templates_inplace.py
```

Patch Russian localization source:

```powershell
python .\twom_patch_russian_lang_structured.py
```

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
