import base64
from typing import Dict

import requests


def get_access_token(client_id: str, client_secret: str) -> str:
    # Encode as Base64
    message = f"{client_id}:{client_secret}"
    message_bytes = message.encode("ascii")
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode("ascii")

    url = "https://accounts.spotify.com/api/token"
    headers = {"Authorization": f"Basic {base64_message}"}
    data = {"grant_type": "client_credentials"}

    response = requests.post(url, headers=headers, data=data)
    token = response.json()["access_token"]

    return token


def load_credentials(cfg: dict) -> Dict[str, str]:
    credentials = dict()

    with open(cfg["user_id_path"], "r") as file:
        credentials["user_id"] = file.read().strip("\n")

    with open(cfg["client_id_path"], "r") as file:
        credentials["client_id"] = file.read().strip("\n")

    with open(cfg["client_secret_path"], "r") as file:
        credentials["client_secret"] = file.read().strip("\n")

    return credentials
