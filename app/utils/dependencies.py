import re
import subprocess
from pathlib import Path

from app.core import settings


def setup_model(
    model_root: Path = settings.MODEL_ROOT,
    model_repo: str = settings.MODEL_REPO,
    model_version: str = settings.MODEL_VERSION,
    use_overwrites: bool = True,
) -> None:
    """
    Clone the model and switch to the correct tag as specified in the settings.
    """
    try:
        proc = subprocess.run(["git", "--version"], capture_output=True)
        if proc.returncode != 0:
            raise RuntimeError("Could not find a working git installation.")
    except FileNotFoundError:
        raise RuntimeError("Could not find a working git installation.")

    if not model_root.exists():
        subprocess.run(
            [
                "git",
                "clone",
                model_repo,
                model_root,
            ]
        )
        subprocess.run(["git", "checkout", model_version], cwd=model_root)

    proc = subprocess.run(
        ["git", "describe", "--tags"], cwd=model_root, capture_output=True
    )
    if not (
        proc.returncode == 0 and proc.stdout.strip().decode("utf8") == model_version
    ):
        subprocess.run(["git", "fetch", "--all"], cwd=model_root)

        subprocess.run(["git", "restore", "."], cwd=model_root)

        subprocess.run(["git", "checkout", model_version], cwd=model_root)

    if use_overwrites:
        subprocess.run(["rsync", "-ra", "../overwrites/", "."], cwd=model_root)
    subprocess.run(["manage_externals/checkout_externals"], cwd=model_root)


def setup_ctsm() -> None:
    if settings.MODEL_ROOT != settings.CTSM_ROOT:
        setup_model(
            model_root=settings.CTSM_ROOT,
            model_repo=settings.CTSM_REPO,
            model_version=settings.CTSM_VERSION,
            use_overwrites=False,
        )
    with open(
        settings.CTSM_ROOT / "tools" / "site_and_regional" / "default_data.cfg", "r"
    ) as data_config_file:
        data_config = data_config_file.read()
    data_config = re.sub(
        r"clmforcingindir\s+=.*\n",
        f"clmforcingindir = {settings.CESMDATAROOT}\n",
        data_config,
    )
    atm_forcing_path = (
        settings.CESMDATAROOT / "atm" / "datm7",
        "atm_forcing.datm7.GSWP3.0.5d.v1.c170516",
    )
    data_config = re.sub(
        r"dir\s+=.*\n",
        f"dir = {atm_forcing_path}\n",
        data_config,
    )
    with open(
        settings.CTSM_ROOT / "tools" / "site_and_regional" / "default_data.cfg", "w"
    ) as data_config_file:
        data_config_file.write(data_config)
