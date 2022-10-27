import subprocess
import time
from zipfile import ZipFile

from app.core import settings
from app.utils.logger import logger

from .celery_app import celery_app


@celery_app.task
def create_data(site_name: str, lat: float, lon: float) -> None:
    logger.info(f"Creating data for {site_name} at {lat}, {lon}")
    start = time.time()

    output_path_name = f"{site_name}_{lat}_{lon}"
    output_path = settings.CUSTOM_SITES_DATA_ROOT / output_path_name

    cmd = [
        str(settings.CTSM_ROOT / "tools" / "site_and_regional" / "subset_data"),
        "point",
        "--site",
        site_name,
        "--lat",
        str(lat),
        "--lon",
        str(lon),
        "--create-domain",
        "--create-surface",
        "--create-datm",
        "--create-user-mods",
        "--outdir",
        str(output_path),
        "--overwrite",
    ]

    proc = subprocess.run(
        cmd,
        capture_output=True,
    )

    if proc.returncode == 0:
        zipfile_path = settings.CUSTOM_SITES_DATA_ROOT / f"{output_path_name}.zip"
        with ZipFile(zipfile_path, "w") as zip_file:
            for f in output_path.rglob("*"):
                if not f.is_symlink():
                    zip_file.write(f, arcname=f.relative_to(output_path))

        logger.info(
            f"Finished creating data for {site_name} at {lat}, {lon} in {time.time() - start} seconds."
        )
        logger.info(f"Data can be found at {output_path}.")
        logger.info(f"Output zip file can be found at {zipfile_path}.")
    else:
        logger.error(proc.stderr.decode("utf8"))
        raise RuntimeError(f"Error creating data for {site_name} at {lat}, {lon}.")
