## Setup and Run the Dev Server

> We recommend using a virtual environment for your project.
>
> You can either use [Conda](https://docs.conda.io/en/latest/) or [Python venv](https://docs.python.org/3/library/venv.html) to create a virtual environment.

- Make sure [Poetry](https://python-poetry.org/) is installed in your environment.
- Create a `.env` file in your project root directory. You can use `env-example` as a template and adjust the variables accordingly. See the Variable section below for more information.
- Install the dependencies: `poetry install`.
- Set up the database: `./scripts/migrations_forward.sh`.
- Set up CTSM repo: `./scripts/setup_ctsm.sh`.
- Run the dev server: `./scripts/run_dev_server.sh`.

### Variables

#### Adjustable Variables in `.env`:

|    Variable    | Required |                                                                      Description                                                                      |             Default             | Scope  |
|:--------------:|:--------:|:-----------------------------------------------------------------------------------------------------------------------------------------------------:|:-------------------------------:|--------|
|   CTSM_REPO    |    No    |                                                              The CTSM repository to use.                                                              | https://github.com/ESCOMP/CTSM/ | API    |
|    CTSM_TAG    |   Yes    |                                                            The CTSM repository tag to use                                                             |                -                | API    |
|   SQLITE_DB    |    No    | The path to the SQLite file to use. If the file doesn't exist, it will be created at the given path.  The default DB will be created in project root. |          cases.sqlite           | API    |
| SQLITE_DB_TEST |    No    |                                                          Same as SQLITE_DB, but for testing.                                                          |        cases_test.sqlite        | API    |
|     DEBUG      |    No    |                              Set `DEBUG` state, which is used for adjusting logging level and other debugging purposes.                               |              False              | API    |
|      PORT      |    No    |                                                       The port to use for API service in docker                                                       |              8000               | Docker |
