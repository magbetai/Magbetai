import os
from datetime import date

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_FOOTBALL_KEY")
BASE_URL = "https://apiv3.apifootball.com/"


def get_today_fixtures():
    today = date.today().isoformat()

    params = {
        "action": "get_events",
        "from": today,
        "to": today,
        "APIkey": API_KEY,
        "timezone": "Africa/Lagos"
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()
    return response.json()
