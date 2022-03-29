## Setup and Run the Dev Server

To run the services locally or with docker, first you need to create a `.env` file in your project root directory.
You can use `env-example` as a template and adjust the variables accordingly. See the `Variable` section below for more information.

> Cases are supposed to run in docker, though you can also run them locally. To see what dependencies are needed for a local run,
> check out `docker/Dockerfile`.

### Run locally
> We recommend using a virtual environment for your project.
>
> You can either use [Conda](https://docs.conda.io/en/latest/) or [Python venv](https://docs.python.org/3/library/venv.html) to create a virtual environment, though conda is not tested.

- Make sure [Poetry](https://python-poetry.org/) is installed in your environment.
- Install the dependencies: `poetry install`.
- Set up the database: `./scripts/migrations_forward.sh`.
- Set up CTSM repo: `./scripts/setup_ctsm.sh`.
- Run the dev server: `./scripts/run_dev_server.sh`.

### Run in Docker

> Install [docker](https://docs.docker.com/engine/install/) and [docker-compose](https://docs.docker.com/compose/install/) first.
>
> The current configs and commands are tested with docker 20.10.13 and docker-compose 1.29.2.

- To build the image locally, run `docker-compose -f docker-compose.dev.yaml build`.
- To run the docker services in debug mode, run `docker-compose -f docker-compose.dev.yaml up`.
- For production, run `docker-compose up`.

In order to avoid permission issues on folders handled by docker,
you can set `HOST_USER` and `HOST_UID` variables to their respective values for the host user under which you are running the docker commands.

You can do this either in your `.env` file or by exporting them in your environment.
THe following command is an example of how to set the variables:
`HOST_USER=$(whoami) HOST_UID=$(id -u) docker-compose -f docker-compose.dev.yaml up`

See `docker/entrypoint.sh` to see how permissions are updated when running the docker services.

### Variables

#### Adjustable Variables in `.env`:

|    Variable    | Required |                                                                                     Description                                                                                      |             Default             | Scope      |
|:--------------:|:--------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|:-------------------------------:|------------|
|   CTSM_REPO    |    No    |                                                                              The CTSM repository to use                                                                              | https://github.com/ESCOMP/CTSM/ | API/Docker |
|    CTSM_TAG    |   Yes    |                                                                            The CTSM repository tag to use                                                                            |                -                | API/Docker |
|  MACHINE_NAME  |    No    | The name of the machine to use for running cases. It must either exist in `resources/dotcime/config_machines.xml` or `resources/ctsm/cime/config/cesm/machines/config_machines.xml`. |            container            | API/Docker |
|   SQLITE_DB    |    No    |              The path to the SQLite file to use<br/>If the file doesn't exist, it will be created at the given path<br/>The default DB will be created in project root               |          cases.sqlite           | API        |
| SQLITE_DB_TEST |    No    |                                                                          Same as SQLITE_DB, but for testing                                                                          |        cases_test.sqlite        | API        |
|      PORT      |    No    |                                                                      The port to use for API service in docker                                                                       |              8000               | Docker     |
|   HOST_USER    |    No    |   Docker host user. If specified for a docker container, ownership of all folders within `resources` will be changed to the container host user<br/>It must be used with HOST_UID    |                -                | Docker     |
|    HOST_UID    |    No    |                                                  UID of docker host user. See `HOST_ID` above and the docker section for more info                                                   |                -                | Docker     |

### Resources

TODO: describe the resources and how they must be set up.
