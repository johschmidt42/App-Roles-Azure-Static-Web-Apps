import logging
import os
from typing import List

import azure.functions as func
from azure.functions import AsgiFunctionApp
from fastapi import FastAPI, Request
from starlette import status

app: FastAPI = FastAPI()


@app.post(path="/GetRoles", status_code=status.HTTP_200_OK)
async def extract_roles(request: Request) -> dict:
    logging.info("Extracting roles from the claims")
    body: dict = await request.json()
    identity_provider: str = body["identityProvider"]
    user_id: str = body["userId"]
    claims: dict = body["claims"]

    role_claim_schema: str = (
        "http://schemas.microsoft.com/ws/2008/06/identity/claims/role"
    )

    roles: List[str] = [
        claim["val"]
        for claim in claims
        if claim["typ"] == role_claim_schema or claim["typ"] == "roles"
    ]

    logging.debug(f"Body: {body}")

    logging.info(
        f"Adding roles: {roles} "
        f"to the user: {user_id} "
        f"from the identity provider: {identity_provider}"
    )
    return {"roles": roles}


@app.get(path="/headers", status_code=status.HTTP_200_OK)
def get_headers(request: Request) -> dict:
    """
    Returns all the headers of the fastAPI request
    """
    logging.info("Returning header")

    headers: list = request.headers.items()

    return {"headers": headers}


@app.get(path="/EnvVars-v2-fastapi", status_code=status.HTTP_200_OK)
def get_env_vars() -> dict:
    """
    Returns all the environment variables
    """
    logging.info("Returning all the environment variables")

    result: dict = dict(os.environ)
    return result


app: AsgiFunctionApp = AsgiFunctionApp(
    app=app, http_auth_level=func.AuthLevel.ANONYMOUS
)
