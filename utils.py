import requests
import json
from bs4 import BeautifulSoup


def parse_url(url: str) -> dict:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    script_tag = soup.find("script", {"type": "text/javascript", "id": "olx-init-config"})
    if not script_tag:
        print("Script tag not found")
        exit()
    script_content = script_tag.string or script_tag.text

    json_str = script_content.split('"{\\"ad\\":{\\"ad\\":')[1].split(',\\"fragments')[0]
    
    json_str = json_str.replace('\\"', '"')

    try:
        data = json.loads(json_str)
        return data

    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        exit(110)
