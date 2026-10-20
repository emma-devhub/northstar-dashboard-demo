# Northstar dashboard demo

Two audience-specific views for the Northstar synthetic take-home case: Customer Account Health and Internal QBR. The internal view uses explicitly illustrative scenario inputs. All telemetry is synthetic.

## Live demo

[Open Northstar Account Intelligence](https://northstar-account-demo.streamlit.app/) — public, no sign-in required. Use **Dashboard view** to switch between **Customer Account Health** and **Internal QBR**.

## Run locally

Python 3.11-3.14; dependencies pinned in requirements.txt.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Use the Dashboard view selector to switch between the two complete views. No credentials, API keys or environment variables are required. The app reads data/northstar_flagship_30_day_metrics.csv relative to the project. The documents in docs/ are required runtime inputs.

## Streamlit Community Cloud

Entry point: app.py. Branch: main. Select Python 3.14 in Advanced settings to match the tested 3.14.4 environment; no secrets are required. Dependencies install from requirements.txt.

This demo includes both audience views for case-review purposes. View selection separates rendering, not authorization. Source data covers Aug 1-31, 2026; internal planning inputs do not establish current production health. See docs/ for synthetic brand and internal scenario assumptions.

The complete submission ZIP separately contains the Executive EBR, Dashboard Design Document and screenshots.
