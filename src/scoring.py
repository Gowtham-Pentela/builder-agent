import json
import re
import requests

from src.db import SessionLocal
from src.models import Lead
from src.prompts import get_scoring_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:3b"


def call_ollama(prompt: str) -> str:
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=120
    )
    response.raise_for_status()
    result = response.json()
    return result["response"]


def extract_json(text: str) -> dict:
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError(f"Could not parse JSON: {text}")


def score_leads():
    session = SessionLocal()
    leads = session.query(Lead).all()

    for lead in leads:
        prompt = get_scoring_prompt(lead)

        try:
            raw_output = call_ollama(prompt)
            print("RAW OUTPUT:", raw_output)

            parsed = extract_json(raw_output)

            lead.fit_score = int(parsed.get("score", 50))
            lead.fit_reason = parsed.get("reason", "No reason returned.")
            lead.outreach_angle = parsed.get("angle", "")

        except Exception as e:
            print("ERROR:", str(e))
            lead.fit_score = 50
            lead.fit_reason = f"Fallback error: {str(e)}"
            lead.outreach_angle = ""

    session.commit()
    session.close()