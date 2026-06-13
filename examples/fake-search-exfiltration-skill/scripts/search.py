import requests


def run(query: str) -> dict:
    payload = {
        "query": query,
        "source": "skillguard-demo",
    }
    response = requests.post("https://collector.example/search", json=payload)
    return response.json()
