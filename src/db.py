from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models import Base, Lead

DATABASE_URL = "sqlite:///leads.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def update_lead_status(lead_id, new_status):
    session = SessionLocal()
    lead = session.query(Lead).filter(Lead.id == lead_id).first()

    if lead:
        lead.status = new_status
        session.commit()

    session.close()


def update_lead_email(lead_id, new_email):
    session = SessionLocal()
    lead = session.query(Lead).filter(Lead.id == lead_id).first()

    if lead:
        lead.outreach_body = new_email
        session.commit()

    session.close()


def update_lead_subject(lead_id, new_subject):
    session = SessionLocal()
    lead = session.query(Lead).filter(Lead.id == lead_id).first()

    if lead:
        lead.outreach_subject = new_subject
        session.commit()

    session.close()


def get_lead_by_id(lead_id):
    session = SessionLocal()
    lead = session.query(Lead).filter(Lead.id == lead_id).first()
    session.expunge_all()
    session.close()
    return lead