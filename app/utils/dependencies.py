import subprocess
from typing import List

from app.core import settings
from app.utils.logger import logger


def check_git(errors: List[str]) -> None:
    """
    Check if git is installed.
    """
    try:
        proc = subprocess.run(["git", "--version"], capture_output=True)
        if proc.returncode != 0:
            errors.append("Git is not installed.")
    except FileNotFoundError:
        errors.append("Git is not installed.")


def check_ctsm(errors: List[str]) -> None:
    """
    Check if the correct version of CTSM is available in `resources/ctsm`.
    """
    if not settings.CTSM_ROOT.exists():
        errors.append("CTSM is not setup. Run `setup_ctsm` first.")
        return

    proc = subprocess.run(
        ["git", "describe"], cwd=settings.CTSM_ROOT, capture_output=True
    )
    if proc.returncode != 0 or proc.stdout.strip().decode("utf8") != settings.CTSM_TAG:
        errors.append("CTSM is not setup correctly. Run `setup_ctsm` first.")


def check_dependencies() -> None:
    """
    Check if the required dependencies are installed.
    """

    errors: List[str] = []

    check_git(errors)

    if not errors:
        # Only run this if git is installed
        check_ctsm(errors)

    if errors:
        raise Exception("\n".join(errors))


def checkout_externals() -> None:
    """
    Checkout CTSM externals.
    """
    proc = subprocess.run(
        ["manage_externals/checkout_externals"],
        cwd=settings.CTSM_ROOT,
        capture_output=True,
    )
    if proc.returncode != 0:
        logger.error(f"Could not checkout externals: {proc.stderr.decode('utf-8')}.")


def setup_ctsm() -> None:
    """
    TODO: add better checkout and cleanup process.
    Clone CTSM with and switch to the correct tag as specified in the settings.
    """
    if settings.CTSM_ROOT.exists():
        proc = subprocess.run(
            ["git", "describe"], cwd=settings.CTSM_ROOT, capture_output=True
        )
        if (
            proc.returncode == 0
            and proc.stdout.strip().decode("utf8") == settings.CTSM_TAG
        ):
            checkout_externals()
            return

        proc = subprocess.run(
            ["git", "fetch", "--all"], cwd=settings.CTSM_ROOT, capture_output=True
        )
        if proc.returncode != 0:
            logger.warning(
                "Could not fetch the latest changes from CTSM remote: "
                f"{proc.stderr.decode('utf-8')}."
            )

        proc = subprocess.run(
            ["git", "checkout", settings.CTSM_TAG],
            cwd=settings.CTSM_ROOT,
            capture_output=True,
        )
        if proc.returncode != 0:
            logger.error(f"Could not checkout CTSM {settings.CTSM_TAG}.")
            return

        checkout_externals()
        return

    proc = subprocess.run(
        [
            "git",
            "clone",
            "-b",
            settings.CTSM_TAG,
            settings.CTSM_REPO,
            "resources/ctsm",
        ],
        capture_output=True,
    )
    if proc.returncode != 0:
        logger.error(f"Could not clone CTSM: {proc.stderr.decode('utf-8')}.")
        return

    checkout_externals()


if __name__ == "__main__":
    setup_ctsm()
