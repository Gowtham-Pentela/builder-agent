import pandas as pd
from src.db import SessionLocal
from src.models import Lead


def ingest_csv(file):
    df = pd.read_csv(file)
    session = SessionLocal()

    for _, row in df.iterrows():
        name = row.get("name")
        company = row.get("company")

        existing = (
            session.query(Lead)
            .filter(
                Lead.name == name,
                Lead.company == company
            )
            .first()
        )

        if existing:
            continue

        lead = Lead(
            name=name,
            company=company,
            role=row.get("role"),
            website=row.get("website"),
            linkedin_url=row.get("linkedin_url"),
            hiring_signal=row.get("hiring_signal"),
            notes=row.get("notes"),
            status="new"
        )
        session.add(lead)

    session.commit()
    session.close()