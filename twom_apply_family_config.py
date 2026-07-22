from pathlib import Path
import shutil
import subprocess
import sys

from twom_family_config import (
    documents_mod_source,
    documents_mods_dir,
    game_mod_dir,
    load_config,
    mod_id,
)


ROOT = Path(__file__).resolve().parent
CONFIG = load_config()


def run_script(name: str) -> None:
    print("\n==", name)
    subprocess.run([sys.executable, str(ROOT / name)], check=True)


def pack_mod_localizations() -> None:
    print("\n== pack mod localizations")
    packroot = ROOT / "packroot_myfamily_localizations"
    if packroot.exists():
        shutil.rmtree(packroot)
    target = packroot / "localizations"
    target.mkdir(parents=True)
    shutil.copy2(
        documents_mod_source(CONFIG) / "localizations" / "russian.lang",
        target / "russian.lang",
    )

    out_base = documents_mods_dir() / f"{mod_id(CONFIG)}_localizations"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "twom_pack_mod_common.py"),
            str(packroot),
            str(out_base),
        ],
        check=True,
    )
    game_target = game_mod_dir(CONFIG)
    game_target.mkdir(parents=True, exist_ok=True)
    for suffix in (".dat", ".idx", ".str"):
        shutil.copy2(out_base.with_suffix(suffix), game_target / out_base.with_suffix(suffix).name)
    print("packed", out_base)


def main() -> None:
    print("Close the game before applying the config.")
    run_script("twom_patch_russian_lang_structured.py")
    pack_mod_localizations()
    run_script("twom_try_female_template_models.py")
    run_script("twom_patch_character03dirty_portraits.py")
    run_script("twom_patch_base_russian_lang.py")
    print("\nDone. Start the game and choose the MyFamily scenario again.")


if __name__ == "__main__":
    main()
