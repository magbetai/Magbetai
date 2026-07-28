from fastapi import FastAPI
from services.api_football import get_today_fixtures

app = FastAPI(title="Magbet AI")

@app.get("/")
def home():
    return {
        "message": "Welcome to Magbet AI"
    }

@app.get("/fixtures")
def fixtures():
    return get_today_fixtures()
from services.api_football import get_today_fixtures
from services.predictions import build_daily_tips
@app.get("/tips")
def tips():
    fixtures = get_today_fixtures()
    return build_daily_tips(fixtures)
