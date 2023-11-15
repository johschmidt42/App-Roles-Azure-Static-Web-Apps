import httpx

url: str = "http://localhost:7071/api/headers"
response: httpx.Response = httpx.get(url=url)
if response.status_code == 200:
    print(response.json())
else:
    raise Exception(f"Unexpected status code: {response.status_code}")
