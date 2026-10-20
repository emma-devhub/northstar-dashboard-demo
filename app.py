"""One application with separate customer and internal rendering branches."""
import streamlit as st
from src.data import DataValidationError, load_data
from src.metrics import calculate_derived_metrics, calculate_summary_metrics
from src.customer_view import render_customer_dashboard

st.set_page_config(page_title='Northstar | Account Health', page_icon='✦', layout='wide')
try:
    data = calculate_derived_metrics(load_data())
except DataValidationError as exc:
    st.error(f'Dataset validation failed. {exc}')
    st.info('Check data/northstar_flagship_30_day_metrics.csv and restart the dashboard.')
    st.stop()

view = st.radio('Dashboard view', ['Customer Account Health', 'Internal QBR'],
                horizontal=True, key='dashboard_view')
summary = calculate_summary_metrics(data)
if view == 'Customer Account Health':
    render_customer_dashboard(data, summary)
else:
    # Lazy import and load: no internal scenario data enters the customer branch.
    from src.internal_view import render_internal_dashboard
    try:
        render_internal_dashboard(data, summary)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        st.error(f'Internal QBR assumptions could not be loaded or validated. {exc}')
        st.info('Check docs/internal_qbr_assumptions.md and docs/expansion_assumptions.md.')
