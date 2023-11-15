import json
from pathlib import Path

import httpx

DATA: Path = Path(__file__).parent.parent / "data"

with open(DATA / "body.json", "r") as json_file:
    payload: dict = json.load(json_file)

url: str = "http://localhost:7071/api/GetRoles"
response: httpx.Response = httpx.post(url=url, json=payload)
if response.status_code == 200:
    print(response.json())
else:
    raise Exception(f"Unexpected status code: {response.status_code}")
