import json
import logging
import os

from azure.functions import HttpRequest, HttpResponse


def main(req: HttpRequest) -> HttpResponse:
    """
    Returns all the environment variables
    """
    logging.info("Returning all the environment variables")

    result: dict = dict(os.environ)
    return HttpResponse(
        body=json.dumps(result),
        mimetype="application/json",
        status_code=200,
        charset="utf-8",
    )
