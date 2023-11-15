import json
import logging
from typing import List

from azure.functions import HttpRequest, HttpResponse


def main(req: HttpRequest):
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
        body=json.dumps(result),
        mimetype="application/json",
        status_code=200,
        charset="utf-8",
    )
