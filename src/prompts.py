def get_scoring_prompt(lead):
    return f"""
You are an expert outbound strategist.

Your goal is to identify high-value leads for an engineer building AI products, agent systems, and automation tools.

Prioritize highly:
- founders
- CEOs
- people actively hiring
- startups building software or AI products
- decision-makers who can directly create opportunities

Lead:
Name: {lead.name}
Company: {lead.company}
Role: {lead.role}
Website: {lead.website}
Hiring Signal: {lead.hiring_signal}
Notes: {lead.notes}

Return ONLY valid JSON in exactly this format:
{{
  "score": 0,
  "reason": "short explanation",
  "angle": "best outreach angle"
}}

Rules:
- founders or CEOs with explicit hiring signals should usually score 80 or above
- weak or unclear leads should score below 50
- reason must be short and specific
- angle must be short and practical
- do not include any text outside the JSON
"""