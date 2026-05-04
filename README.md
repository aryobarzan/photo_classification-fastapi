# Setup

## Environment file (.env)

Adjust the example environment `.env-example` by replacing the missing values, then rename the file to `.env`.

1. Set up a secret key `SECRET_KEY` for the JWT authentication using the following command: `openssl rand -hex 32`
2. Set up a secret key `GARAGE_RPC_SECRET` for the storage layer Garage using the same command: `openssl rand -hex 32`

The other key-value pairs can be left as is for this demonstration.

## docker-compose.yaml

A one-time setup run is required to finalize the storage layer's (Garage) settings.

1. Run the following command to launch the Docker services: `docker-compose up -d`
2. Run the following command and copy the output node id: `docker compose exec garage /garage node id`
3. Run the following command, with `<node-id>` being replaced by the prior command's output node id: `docker compose exec garage /garage layout assign -z dc1 -c 1G <node-id>`
4. Run the following command: `docker compose exec garage /garage layout apply --version 1`
5. Run the following command: `docker compose exec garage /garage key create my-app-key`
   1. Copy the value of `Key ID:` to `STORAGE_ACCESS_KEY` in your environment file `.env`
   2. Copy the value of `Secret key:` to `STORAGE_SECRET_KEY` in your environment file `.env`
6. Run the following command: `docker compose exec garage /garage bucket create profile-pictures`
7. Run the following command: `docker compose exec garage /garage bucket allow --read --write profile-pictures --key my-app-key`

Your setup of the environment file and docker is now complete. Run `docker-compose down` to shutdown the Docker containers.

# Run

To launch the FastAPI-based REST server with its associated PostgreSQL database and Garage storage layer, use `docker-compose up -d`.

- The server will be accessible from your host machine at `http://localhost:8000/`
- The documentation with the endpoint details (using Swagger) can be found at `http://localhost:8000/docs`

To have sample data for testing purposes, run the following command once while the docker containers are running: `docker-compose --profile seed run --rm seeder`

- This will run the script `sample-generator.py`.

Note that the Python dependencies of this project are listed in `requirements.txt`, which are automatically fetched thanks to the `Dockerfile` setup.

# Pre-commit linting

We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting the codebase, enforced automatically via [pre-commit](https://pre-commit.com/), i.e., before each git commit.

To install and set up this pre-commit hook:

```bash
pip install -r requirements-dev.txt
pre-commit install
```
