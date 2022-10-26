import argparse
import json
import logging
import re
import subprocess
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import TypedDict
from zipfile import ZipFile

logger = logging.getLogger(__name__)

CONFIG = {
    "CTSM_ROOT": "",
    "CESM_DATA_ROOT": "",
    "OUTPUT_DIR": "",
}

parser = argparse.ArgumentParser()
parser.add_argument("--ctsm-root", type=str, required=True)
parser.add_argument("--cesm-data-root", type=str, required=True)
parser.add_argument("--output-dir", type=str, required=True)
parser.add_argument("--sites", type=str, required=True)
parser.add_argument("--cpu-count", type=int, default=cpu_count())


class Site(TypedDict):
    name: str
    lat: float
    lon: float


def setup_ctsm():
    ctsm_root = Path(CONFIG["CTSM_ROOT"])
    cesm_data_root = Path(CONFIG["CESM_DATA_ROOT"])
    with open(
        ctsm_root / "tools" / "site_and_regional" / "default_data.cfg", "r"
    ) as data_config_file:
        data_config = data_config_file.read()

    data_config = re.sub(
        r"clmforcingindir\s+=.*\n",
        f"clmforcingindir = {str(cesm_data_root)}\n",
        data_config,
    )

    atm_forcing_path = (
        cesm_data_root / "atm" / "datm7" / "atm_forcing.datm7.GSWP3.0.5d.v1.c170516"
    )
    data_config = re.sub(
        r"dir\s+=.*atm_forcing.datm7.GSWP3.0.5d.v1.c170516\n",
        f"dir = {str(atm_forcing_path)}\n",
        data_config,
    )

    with open(
        ctsm_root / "tools" / "site_and_regional" / "default_data.cfg", "w"
    ) as data_config_file:
        data_config_file.write(data_config)


def create_data(site: Site) -> None:
    site_name = site["name"]
    lat = site["lat"]
    lon = site["lon"]

    logger.info(f"Creating data for {site_name} at {lat}, {lon}")
    start = time.time()

    output_dir = Path(CONFIG["OUTPUT_DIR"])
    output_path = output_dir / site_name

    cmd = [
        str(Path(CONFIG["CTSM_ROOT"]) / "tools" / "site_and_regional" / "subset_data"),
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
        zipfile_path = output_dir / f"{site_name}.zip"
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


if __name__ == "__main__":
    args = parser.parse_args()

    CONFIG["CTSM_ROOT"] = args.ctsm_root
    CONFIG["CESM_DATA_ROOT"] = args.cesm_data_root
    CONFIG["OUTPUT_DIR"] = args.output_dir

    with open(args.sites) as sites_file:
        sites = json.load(sites_file)

    setup_ctsm()

    with Pool(args.cpu_count) as pool:
        pool.map(create_data, sites)
