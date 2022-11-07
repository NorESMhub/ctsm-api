# Attribution

The scripts provided here wrap around the code related to `CTSM/tools/site_and_regional/subset_data` for single point data creation, available in [the CTSM repository](https://github.com/ESCOMP/CTSM/tree/ctsm5.1.dev112/tools/site_and_regional). A tutorial is available [here](https://github.com/NCAR/CTSM-Tutorial-2022/blob/main/notebooks/Day2a_GenericSinglePoint.ipynb). Please ensure to attribute this work if you use this code.

_Kaveh Karimi & Lasse Keetz, 31-10-2022._

# Instructions to create input data for a custom site

The scripts to create new input data with this `ctsm-api` version require the following global datasets and file structures:

- `<cesm-data-root>/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516`
- `<cesm-data-root>/share/domains/domain.lnd.fv0.9x1.25_gx1v7.151020.nc`
- `<cesm-data-root>/lnd/clm2/surfdata_map/release-clm5.0.18/surfdata_0.9x1.25_hist_16pfts_Irrig_CMIP6_simyr2000_c190214.nc`
- `<cesm-data-root>/lnd/clm2/surfdata_map/release-clm5.0.18/surfdata_0.9x1.25_hist_78pfts_CMIP6_simyr2000_c190214.nc`

The datasets are available at https://svn-ccsm-inputdata.cgd.ucar.edu/trunk/inputdata/. **Warning!** The datasets have a total size of approx. 2.3 TB, make sure you have enough disk space available before downloading files.

If you want to use different versions of these data (WARNING! Might break the model, only if you know what you are doing!), make sure they exist in the given paths and adapt the names of the files in:

- `<ctsm-api-root>/data/create_data.py` -> Adapt name of atmospheric forcing
- `<ctsm-root>/tools/site_and_regional/default_data.cfg` -> Adapt other file names

This document provides a working example tested on a remote server, [SAGA](https://documentation.sigma2.no/hpc_machines/saga.html), with Anaconda. The time it takes to create the data is dependent on the machine and the amount of cores you use; on Saga, creating data for a single site requires approximately 1.5 hours.

## 1 Clone `CTSM` and `ctsm-api`, checkout externals

Optional but recommended: also checkout the CTSM tag we have tested the scripts for.

```
git clone https://github.com/ESCOMP/CTSM.git  # CTSM
### Optional start ###
cd CTSM
git checkout tags/ctsm5.1.dev112 -b subset-data
cd ..
### Optional end ###
./CTSM/manage_externals/checkout_externals
git clone https://github.com/NorESMhub/ctsm-api.git  # ctsm-api
```

## 2 Install/load Python dependencies

You need a recent Python environment that has `xarray` with `netcdf4` installed to run the scripts.
On SAGA:

```
# Load Anaconda module
module load Anaconda3/2022.05
# Install new conda environment
conda create -n subset-data-env -c conda-forge python=3.10 xarray netCDF4
# Activate conda environment. Try the commented out version if this throws an error.
source activate subset-data-env  # conda activate subset-data-env
```

## 3 Add new site information to config file

Edit `<ctsm-api-root>/data/sites.json` or use it as a template to create a new file.
You need to provide `lon` and `lat` coordinates and a site name (convention: three capital letters plus optional integer). Site names must be alphanumeric (i.e., no special characters) without spaces. You can include one or multiple sites (see example below).

Example for a `sites.json` file:

```
[
  {
    "name": "ALP1",
    "lon": 8.12343,
    "lat": 61.0243
  },
  {
    "name": "TST1",
    "lon": -59.9590,
    "lat": -2.7008
  },
  {
    "name": "TST2",
    "lon": -132.0512,
    "lat": 62.1421
  },
  {
    "name": "TST3",
    "lon": 23.9325,
    "lat": -13.9705
  }
]
```

Note the square brackets around all site entries and that the last entry between curly brackets `{...}`
cannot have a trailing comma.

## 4 Create the data

To create a `.zip` file with input data for custom sites, you need to run `<ctsm-api-root>/data/create_data.py`. You can either run it directly or send it as a batch job to a queue system (see further down).

`create_data.py` requires the following command line arguments:

| Flag        | Description           | Example  |
| ------------- |:-------------:| ----- |
| `--ctsm-root`      | Root path to local CTSM installation with checked out externals. | `--ctsm-root ~/CTSM` |
| `--cesm-data-root` | Root path to global CESM dataset netCDF files. | `--cesm-data-root /cluster/shared/noresm/inputdata` |
| `--output-dir`     | Path where the zip files with extracted input data will be created. OBS! Make sure this directory already exists, otherwise the scripts will fail! | `--output-dir /cluster/shared/noresm/sites` |
| `--sites`      | Path to a `sites.json` instruction file as described in 3. | `--sites sites.json` |
| `--cpu-count`      | OPTIONAL. Provide a number of CPUs for multiprocessing. Will use all available CPUs if omitted.  | `--cpu-count 10` |

WARNING! The `subset_data` scripts require a recent version of git that implements the `-C` flag. On SAGA, load the following module before running `create_data.py`:

```
module load git/2.36.0-GCCcore-11.3.0-nodocs
```

Finally, run the script. Full example:

```
python3 create_data.py \
    --ctsm-root ~/CTSM \
    --cesm-data-root /cluster/shared/noresm/inputdata \
    --output-dir /cluster/shared/noresm/sites \
    --sites sites.json
```

---

To send the input data creation as a batch job to an HPC queue, you can write a bash script that follows the syntax requirements of the system. E.g. on SAGA:

```
cd <ctsm-api-root>/data
vi create_site_data.sh
```

and add (NB! Adjust your project account, machine dependent module versions/names, and paths if necessary):

```
#!/bin/bash
#SBATCH --account=nn2806k
#SBATCH --cpus-per-task=10
#SBATCH --ntasks=1
#SBATCH --job-name=LSP-data-test
#SBATCH --mem-per-cpu=16G
#SBATCH --nodes=1
#SBATCH --time=12:00:00

set -o errexit  # Exit the script on any error

module --quiet purge  # Reset the modules to the system default
module load git/2.36.0-GCCcore-11.3.0-nodocs

module load Anaconda3/2022.05
eval "$(/cluster/software/Anaconda3/2022.05/bin/conda shell.bash hook)"
conda activate subset-data-env

python3 create_data.py \
    --ctsm-root ~/CTSM \
    --cesm-data-root /cluster/shared/noresm/inputdata \
    --output-dir /cluster/shared/noresm/sites \
    --sites sites-test.json \
    --cpu-count 10
```

Then run:

```
sbatch create_site_data.sh
```

You can check the state of the job by entering `squeue --me` (or `squeue -u <user-name>`) and by investigating the `slurm-<job-id>.out` log files created in the current working directory.
