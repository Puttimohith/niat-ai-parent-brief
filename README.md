# NIAT AI Parent Decision Brief

An independent AI-powered growth-hack prototype developed
for the NxtWave Jr. Growth Manager challenge.

**Disclaimer:** This is not an official NIAT or NxtWave
application, admission portal, or university service.

## Project Objective

Help prospective students and parents understand NIAT-related
upskilling opportunities, identify important admission and
financial questions, and request further guidance.

The growth hypothesis is that personalized decision-support
briefs can increase the proportion of interested visitors
who request a follow-up.

## Connected System Components

### 1. Parent Information Intake
- Collects student and parent preferences
- Captures institution, budget, language, and concerns
- Requires consent before processing

### 2. AI Decision Brief Generator
- Uses the Google Gemini API
- Incorporates curated NIAT knowledge
- Generates personalized decision-support briefs
- Supports English, Telugu, and Hindi
- Distinguishes NIAT upskilling from university admission
- Avoids unsupported admission and placement guarantees

### 3. Growth Tracking and Analytics
- Stores lead events in SQLite
- Tracks successful AI brief generation
- Tracks follow-up requests
- Calculates funnel conversion metrics
- Separates demonstration and real records
- Provides a password-protected analytics dashboard

## Technology Stack

- Python 3.12
- Streamlit
- Google Gemini API
- SQLite
- Pandas
- pytest

## Project Structure

app/
  main.py
  pages/dashboard.py
  services/ai_service.py
  services/knowledge_service.py
  services/tracking_service.py

data/
  niat_knowledge.json

tests/
  test_workflow.py
  test_application_mode.py

## Local Setup

1. Create and activate a Python virtual environment.

2. Install dependencies:

   pip install -r requirements.txt

3. Copy the environment template:

   cp .env.example .env

4. Configure the environment variables:

   GEMINI_API_KEY=your_api_key
   DASHBOARD_PASSWORD=your_secure_password
   LEAD_RECORD_TYPE=demo

5. Start the application:

   streamlit run app/main.py

6. Open the analytics dashboard through Streamlit navigation.

## Testing

Run:

    python -m pytest -q tests/

The project currently has 23 passing automated tests.

## Growth Experiment

Primary KPI:

Follow-up request rate among successfully generated
AI decision briefs.

Supporting KPIs:

- Submitted leads
- Successful AI brief generations
- Brief generation rate
- Language preferences
- Institution interest

Demo records are separated from records classified as real.
The classification setting alone does not verify user identity.

## Current Limitations

- This is an independent demonstration prototype.
- Admission and university details require verification.
- No admission or placement outcomes are guaranteed.
- Local SQLite storage is not suitable for every
  multi-instance cloud deployment.
- Current analytics do not demonstrate actual growth uplift.
- Production deployment requires additional privacy,
  security, and operational validation.
