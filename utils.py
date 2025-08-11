import requests
import json
import logging
from bs4 import BeautifulSoup

class OlxProductNotFound(BaseException):
    pass

def parse_url(url: str) -> dict:
    response = requests.get(url)
    if "Acest anunț nu mai este disponibil" in response.text:
        raise OlxProductNotFound

    soup = BeautifulSoup(response.text, "html.parser")

    script_tag = soup.find("script", {"type": "text/javascript", "id": "olx-init-config"})
    if not script_tag:
        logging.error("Script tag not found")
        exit()
    script_content = script_tag.string or script_tag.text

    json_str = script_content.split('"{\\"ad\\":{\\"ad\\":')[1].split(',\\"fragments')[0]

    json_str = json_str.replace('\\"', '"')

    try:
        data = json.loads(json_str)
        return data

    except json.JSONDecodeError as e:
        logging.error("Failed to parse JSON:", e)
        exit(110)
