import json
import logging
import os

from azure.functions import AuthLevel, FunctionApp, HttpRequest, HttpResponse
from psycopg2.pool import SimpleConnectionPool
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    POSTGRESQL_HOST: str
    POSTGRESQL_USER: str
    POSTGRESQL_PASSWORD: str
    POSTGRESQL_DATABASE_NAME: str


# Read env vars
database_config: DatabaseConfig = DatabaseConfig()

# Create a connection pool (this code is shared across function invocations)
pool: SimpleConnectionPool = SimpleConnectionPool(
    minconn=1,  # minimum number of connections
    maxconn=20,  # maximum number of connections
    host=database_config.POSTGRESQL_HOST,
    user=database_config.POSTGRESQL_USER,
    password=database_config.POSTGRESQL_PASSWORD,
    dbname=database_config.POSTGRESQL_DATABASE_NAME,
)

# Azure Functions bindings are restricted to the AzureSQL family
# Azure Cosmos DB for PostgreSQL is not part of this family
# which is why we need to instantiate a database connection pool

print("Initialized database connection pool", flush=True)


app: FunctionApp = FunctionApp()


@app.function_name(name="Env")
@app.route(route="env", methods=["GET"], auth_level=AuthLevel.ANONYMOUS)
def get_env_vars(req: HttpRequest):
    """
    Returns all the environment variables
    """
    logging.info("Returning all the environment variables")

    result: dict = dict(os.environ)
    return HttpResponse(
        body=json.dumps(result), mimetype="application/json", status_code=200
    )


@app.function_name(name="User")
@app.route(route="user", methods=["GET"], auth_level=AuthLevel.ANONYMOUS)
def user(req: HttpRequest):
    return HttpResponse(
        body=json.dumps({"user": True}), mimetype="application/json", status_code=200
    )


@app.function_name(name="Master")
@app.route(route="master", methods=["GET"], auth_level=AuthLevel.ANONYMOUS)
def master(req: HttpRequest):
    return HttpResponse(
        body=json.dumps({"master": True}), mimetype="application/json", status_code=200
    )
