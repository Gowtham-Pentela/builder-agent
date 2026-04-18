from dotenv import load_dotenv
import streamlit as st
import pandas as pd

from src.db import (
    init_db,
    SessionLocal,
    update_lead_status,
    update_lead_email,
    update_lead_subject,
)
from src.models import Lead
from src.ingest import ingest_csv
from src.scoring import score_leads
from src.outreach import generate_outreach, generate_outreach_for_lead_id

load_dotenv()
init_db()

st.set_page_config(page_title="Builder Agent", layout="wide")
st.title("Builder Agent V1")
st.caption("Upload leads, score them, generate outreach, and manage lead workflow.")


def color_status(status: str) -> str:
    if status == "new":
        return "gray"
    if status == "reviewed":
        return "orange"
    if status == "ready":
        return "blue"
    if status == "sent":
        return "green"
    return "gray"


# Sidebar
st.sidebar.header("Lead Operations")
uploaded_file = st.sidebar.file_uploader("Upload CSV", type=["csv"])

if "last_uploaded_file" not in st.session_state:
    st.session_state.last_uploaded_file = None

if uploaded_file is not None and st.session_state.last_uploaded_file != uploaded_file.name:
    ingest_csv(uploaded_file)
    st.session_state.last_uploaded_file = uploaded_file.name
    st.sidebar.success("Leads ingested successfully.")
    st.rerun()

if st.sidebar.button("Score Leads", width="stretch"):
    score_leads()
    st.sidebar.success("Lead scoring complete.")
    st.rerun()

if st.sidebar.button("Generate Outreach", width="stretch"):
    generate_outreach()
    st.sidebar.success("Outreach generation complete.")
    st.rerun()

# Load data
session = SessionLocal()
leads = session.query(Lead).all()

data = []
for lead in leads:
    data.append(
        {
            "ID": lead.id,
            "Name": lead.name,
            "Company": lead.company,
            "Role": lead.role,
            "Status": lead.status,
            "Score": lead.fit_score,
            "Reason": lead.fit_reason,
            "Angle": getattr(lead, "outreach_angle", ""),
            "Subject": lead.outreach_subject,
            "Email": lead.outreach_body,
        }
    )

df = pd.DataFrame(data)

st.subheader("Leads Dashboard")

if df.empty:
    st.info("No leads yet. Upload a CSV to get started.")
    session.close()
    st.stop()

# Top metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Leads", len(df))
col2.metric("Scored Leads", int(df["Score"].notna().sum()) if "Score" in df.columns else 0)
col3.metric("Outreach Generated", int(df["Email"].notna().sum()) if "Email" in df.columns else 0)
# Filters
st.markdown("### Filters")
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    min_score = st.slider("Minimum Score", 0, 100, 0)

with filter_col2:
    companies = ["All"] + sorted(df["Company"].dropna().unique().tolist())
    selected_company = st.selectbox("Company", companies)

filtered_df = df.copy()

if "Score" in filtered_df.columns:
    filtered_df = filtered_df[filtered_df["Score"].fillna(0) >= min_score]

if selected_company != "All":
    filtered_df = filtered_df[filtered_df["Company"] == selected_company]

st.markdown("### Lead List")
table_df = filtered_df[["ID", "Name", "Company", "Role", "Status", "Score"]].copy()
st.dataframe(table_df, width="stretch", hide_index=True)

st.markdown("### Lead Details")

lead_options = filtered_df["ID"].tolist()

if not lead_options:
    st.warning("No leads match the current filters.")
    session.close()
    st.stop()

if "selected_lead_id" not in st.session_state or st.session_state.selected_lead_id not in lead_options:
    st.session_state.selected_lead_id = lead_options[0]

selected_lead_id = st.selectbox(
    "Select a lead",
    lead_options,
    index=lead_options.index(st.session_state.selected_lead_id)
)

st.session_state.selected_lead_id = selected_lead_id

selected_row = filtered_df[filtered_df["ID"] == selected_lead_id].iloc[0]

detail_col1, detail_col2 = st.columns(2)

with detail_col1:
    st.markdown(f"**Name:** {selected_row['Name']}")
    st.markdown(f"**Company:** {selected_row['Company']}")
    st.markdown(f"**Role:** {selected_row['Role']}")
    st.markdown(f"**Score:** {selected_row['Score']}")
    st.markdown(
        f"**Status:** :{color_status(selected_row['Status'])}[{selected_row['Status']}]"
    )

    status_options = ["new", "reviewed", "ready", "sent"]
    current_status = selected_row["Status"] if pd.notna(selected_row["Status"]) else "new"

    new_status = st.selectbox(
        "Update Status",
        status_options,
        index=status_options.index(current_status) if current_status in status_options else 0,
        key="status_selector"
    )

    status_col1, status_col2 = st.columns(2)

    with status_col1:
        if st.button("Save Status", key="save_status_btn"):
            update_lead_status(selected_lead_id, new_status)
            st.success(f"Status updated to '{new_status}'")
            st.rerun()

    with status_col2:
        if st.button("Mark as Sent", key="mark_sent_btn"):
            update_lead_status(selected_lead_id, "sent")
            st.success("Lead marked as sent.")
            st.rerun()

    if st.button("Regenerate Email", key="regen_email_btn"):
        ok = generate_outreach_for_lead_id(selected_lead_id)
        if ok:
            st.success("Email regenerated.")
        else:
            st.error("Failed to regenerate email.")
        st.rerun()

with detail_col2:
    st.markdown("**Reason**")
    st.write(selected_row["Reason"] if pd.notna(selected_row["Reason"]) else "Not scored yet.")

    st.markdown("**Outreach Angle**")
    st.write(selected_row["Angle"] if pd.notna(selected_row["Angle"]) else "No angle yet.")

st.markdown("### Generated Outreach")

current_subject = selected_row["Subject"] if pd.notna(selected_row["Subject"]) else ""
current_email = selected_row["Email"] if pd.notna(selected_row["Email"]) else ""

subject_key = f"subject_editor_{selected_lead_id}"
email_key = f"email_editor_{selected_lead_id}"
saved_subject_key = f"saved_subject_{selected_lead_id}"
saved_email_key = f"saved_email_{selected_lead_id}"

# Initialize saved state for this lead
if saved_subject_key not in st.session_state:
    st.session_state[saved_subject_key] = current_subject

if saved_email_key not in st.session_state:
    st.session_state[saved_email_key] = current_email

# Keep editor in sync when switching leads
if subject_key not in st.session_state:
    st.session_state[subject_key] = current_subject

if email_key not in st.session_state:
    st.session_state[email_key] = current_email

edited_subject = st.text_input(
    "Email Subject",
    key=subject_key,
)

edited_email = st.text_area(
    "Email Body",
    height=220,
    key=email_key,
)

has_unsaved_changes = (
    edited_subject != st.session_state[saved_subject_key]
    or edited_email != st.session_state[saved_email_key]
)

if has_unsaved_changes:
    st.warning("You have unsaved changes.")
else:
    st.success("All changes saved.")

action_col1, action_col2 = st.columns(2)

with action_col1:
    if st.button("Save Changes", key="save_all_btn"):
        update_lead_subject(selected_lead_id, edited_subject)
        update_lead_email(selected_lead_id, edited_email)

        st.session_state[saved_subject_key] = edited_subject
        st.session_state[saved_email_key] = edited_email

        st.success("Subject and email saved.")
        st.rerun()

with action_col2:
    if st.button("Reset Editor", key="reset_editor_btn"):
        st.session_state[subject_key] = st.session_state[saved_subject_key]
        st.session_state[email_key] = st.session_state[saved_email_key]
        st.rerun()

export_df = filtered_df.drop(columns=["ID"], errors="ignore")
csv = export_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Results CSV",
    data=csv,
    file_name="builder_agent_export.csv",
    mime="text/csv",
)

session.close()