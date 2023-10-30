import json
import logging
import os
from typing import List

from azure.functions import AuthLevel, FunctionApp, HttpRequest, HttpResponse

app: FunctionApp = FunctionApp()


@app.function_name(name="GetRoles")
@app.route(route="GetRoles", methods=["POST"], auth_level=AuthLevel.ANONYMOUS)
def extract_roles(req: HttpRequest):
    logging.info("Extracting roles from the claims")
    body: dict = req.get_json()
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

    result: dict = {"roles": roles}
    return HttpResponse(
        body=json.dumps(result), mimetype="application/json", status_code=200
    )


@app.function_name(name="EnvVars-v2")
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
    """
    Returns if role is user
    """
    return HttpResponse(
        body=json.dumps({"user": True}), mimetype="application/json", status_code=200
    )


@app.function_name(name="Admin")
@app.route(route="administrator", methods=["GET"], auth_level=AuthLevel.ANONYMOUS)
def admin(req: HttpRequest):
    """
    Returns if role is admin
    """
    return HttpResponse(
        body=json.dumps({"admin": True}), mimetype="application/json", status_code=200
    )
