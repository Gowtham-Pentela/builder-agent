import json
import re
import requests

from src.db import SessionLocal
from src.models import Lead

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
    return response.json()["response"]


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


def build_outreach_prompt(lead) -> str:
    return f"""
You are writing a high-quality cold outreach email.

Your goal is to help an engineer who builds AI products, agent systems, automation workflows, and internal tools reach out to a relevant lead.

Lead:
Name: {lead.name}
Company: {lead.company}
Role: {lead.role}
Website: {lead.website}
Hiring Signal: {lead.hiring_signal}
Notes: {lead.notes}

Outreach Angle:
{lead.outreach_angle}

Return ONLY valid JSON in exactly this format:
{{
  "subject": "short subject line",
  "body": "email body"
}}

Rules:
- subject must be under 8 words
- body must be 80 to 120 words
- make it personal and relevant
- mention something specific about the company, role, or hiring signal
- clearly show value in one or two sentences
- include one concrete example of what the sender builds
- end with a simple, low-friction ask
- no bullet points
- no generic phrases like 'hope you're doing well'
- sound like a real person, not a template
- do not include any text outside the JSON
"""


def generate_outreach_for_lead_id(lead_id):
    session = SessionLocal()
    lead = session.query(Lead).filter(Lead.id == lead_id).first()

    if not lead:
        session.close()
        return False

    try:
        prompt = build_outreach_prompt(lead)
        raw_output = call_ollama(prompt)
        parsed = extract_json(raw_output)

        lead.outreach_subject = parsed.get("subject", f"Quick idea for {lead.company}")
        lead.outreach_body = parsed.get("body", "").strip()

        session.commit()
        session.close()
        return True

    except Exception as e:
        lead.outreach_subject = f"Quick idea for {lead.company}"
        lead.outreach_body = f"Error: {str(e)}"
        session.commit()
        session.close()
        return False


def generate_outreach():
    session = SessionLocal()
    leads = session.query(Lead).all()

    for lead in leads:
        if not lead.fit_score:
            continue

        try:
            prompt = build_outreach_prompt(lead)
            raw_output = call_ollama(prompt)
            parsed = extract_json(raw_output)

            lead.outreach_subject = parsed.get("subject", f"Quick idea for {lead.company}")
            lead.outreach_body = parsed.get("body", "").strip()

        except Exception as e:
            lead.outreach_subject = f"Quick idea for {lead.company}"
            lead.outreach_body = f"Error: {str(e)}"

    session.commit()
    session.close()