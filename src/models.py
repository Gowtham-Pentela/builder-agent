from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    company = Column(String)
    role = Column(String)
    website = Column(String)
    linkedin_url = Column(String)
    hiring_signal = Column(Text)
    notes = Column(Text)

    fit_score = Column(Integer)
    fit_reason = Column(Text)
    outreach_angle = Column(Text)

    outreach_subject = Column(Text)
    outreach_body = Column(Text)

    status = Column(String, default="new")

    __table_args__ = (
        UniqueConstraint("name", "company", name="uq_lead_name_company"),
    )