import os
import time
import requests
import streamlit as st

from carbongpt.core.location_utils import (
    ALL_COUNTRIES, TOOL33_TO_PYCOUNTRY, get_fnrb_for_country, geocode_location,
)
from carbongpt.ui.parameter_ui import render_parameter_dashboard
from carbongpt.ui.er_simulator_ui import render_er_simulator
from carbongpt.ui.lifecycle_ui import render_lifecycle_dashboard, render_monitoring_dashboard
from carbongpt.ui.portfolio_ui import render_portfolio_dashboard
from carbongpt.ui.audit_ui import render_audit_simulation

API_BASE = os.getenv("CARBONGPT_API_URL", "http://localhost:3000")

st.set_page_config(page_title="CarbonGPT", layout="wide", page_icon="C")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {
        --brand-primary: #0d9488;
        --brand-primary-light: #14b8a6;
        --brand-primary-dark: #0f766e;
        --brand-primary-50: #f0fdfa;
        --brand-primary-100: #ccfbf1;
        --brand-primary-200: #99f6e4;
        --brand-gradient: linear-gradient(135deg, #0d9488 0%, #14b8a6 50%, #2dd4bf 100%);
        --brand-glow: 0 0 20px rgba(13, 148, 136, 0.15);

        --surface-base: #f8fafb;
        --surface-raised: #ffffff;
        --surface-sunken: #f1f5f9;
        --surface-overlay: rgba(255,255,255,0.95);

        --border-subtle: #e8ecf1;
        --border-default: #e2e8f0;
        --border-strong: #cbd5e1;

        --text-primary: #0f172a;
        --text-secondary: #475569;
        --text-tertiary: #94a3b8;
        --text-inverse: #ffffff;

        --shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.07), 0 2px 4px -2px rgba(0,0,0,0.05);
        --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);
        --shadow-xl: 0 20px 25px -5px rgba(0,0,0,0.08), 0 8px 10px -6px rgba(0,0,0,0.04);

        --radius-sm: 8px;
        --radius-md: 12px;
        --radius-lg: 16px;
        --radius-xl: 20px;
        --radius-full: 9999px;

        --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
        --transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
        --transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);

        --gold-standard: #b8860b;
        --gold-standard-bg: #fef9ee;
        --verra-blue: #2563eb;
        --verra-blue-bg: #eff6ff;
    }

    * { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }

    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        background: var(--surface-base);
        color: var(--text-primary);
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1a 0%, #111827 40%, #0f172a 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
        box-shadow: 4px 0 24px rgba(0,0,0,0.12);
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] .stMarkdown span {
        color: #cbd5e1;
        font-size: 0.88rem;
    }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #f1f5f9;
    }
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 2px;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #94a3b8 !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        padding: 0.55rem 0.85rem !important;
        border-radius: var(--radius-sm) !important;
        transition: all var(--transition-fast) !important;
        margin: 0 !important;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        color: #f1f5f9 !important;
        background: rgba(255,255,255,0.06) !important;
    }
    section[data-testid="stSidebar"] .stRadio label[data-checked="true"],
    section[data-testid="stSidebar"] .stRadio [aria-checked="true"] + label,
    section[data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {
        color: #f0fdfa !important;
        background: rgba(13,148,136,0.18) !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.06) !important;
        margin: 0.75rem 0 !important;
    }
    section[data-testid="stSidebar"] .stCaption {
        color: #475569 !important;
    }

    /* ── Sidebar Brand ── */
    .brand-header {
        padding: 0.4rem 0 1.4rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        margin-bottom: 0.8rem;
    }
    .brand-logo-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 6px;
    }
    .brand-icon {
        width: 34px;
        height: 34px;
        border-radius: 10px;
        background: var(--brand-gradient);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        font-weight: 800;
        color: white;
        letter-spacing: -0.5px;
        box-shadow: 0 2px 8px rgba(13,148,136,0.3);
        flex-shrink: 0;
    }
    .brand-header h2 {
        font-size: 1.3rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        margin: 0;
        color: #f1f5f9;
    }
    .brand-tagline {
        font-size: 0.68rem;
        color: #64748b;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        font-weight: 500;
        margin-top: 2px;
        padding-left: 44px;
    }

    .sidebar-section-label {
        font-size: 0.65rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #475569;
        padding: 0.6rem 0.85rem 0.3rem;
        margin-top: 0.3rem;
    }
    .sidebar-nav-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 0.55rem 0.85rem;
        border-radius: var(--radius-sm);
        color: #94a3b8;
        font-size: 0.88rem;
        font-weight: 500;
        cursor: pointer;
        transition: all var(--transition-fast);
        text-decoration: none;
        margin: 1px 0;
    }
    .sidebar-nav-item:hover {
        color: #f1f5f9;
        background: rgba(255,255,255,0.06);
    }
    .sidebar-nav-item.active {
        color: #f0fdfa;
        background: rgba(13,148,136,0.18);
        font-weight: 600;
    }
    .sidebar-nav-icon {
        width: 18px;
        height: 18px;
        opacity: 0.7;
        flex-shrink: 0;
    }
    .sidebar-footer {
        padding: 0.8rem 0.85rem;
        border-top: 1px solid rgba(255,255,255,0.06);
        margin-top: 0.5rem;
    }
    .sidebar-footer-text {
        font-size: 0.7rem;
        color: #475569;
        font-weight: 400;
    }
    .sidebar-footer-version {
        font-size: 0.65rem;
        color: #334155;
        font-weight: 400;
        margin-top: 2px;
    }

    /* ── Page Headers ── */
    .page-header {
        padding: 0.25rem 0 1.8rem 0;
        margin-bottom: 0.25rem;
    }
    .page-header h1 {
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: var(--text-primary);
        margin-bottom: 0.3rem;
        line-height: 1.2;
    }
    .page-subtitle {
        font-size: 0.92rem;
        color: var(--text-secondary);
        line-height: 1.5;
        font-weight: 400;
    }

    /* ── Metrics ── */
    div[data-testid="stMetric"] {
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 1.1rem 1.3rem;
        box-shadow: var(--shadow-xs);
        transition: all var(--transition-base);
    }
    div[data-testid="stMetric"]:hover {
        box-shadow: var(--shadow-sm);
        border-color: var(--border-default);
    }
    div[data-testid="stMetric"] label {
        color: var(--text-tertiary);
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-size: 1.7rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.02em;
    }

    /* ── Cards / Containers ── */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: var(--radius-md);
        border-color: var(--border-subtle);
        background: var(--surface-raised);
        box-shadow: var(--shadow-xs);
        transition: all var(--transition-base);
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: var(--border-default);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    /* ── Buttons ── */
    .stButton > button[kind="primary"] {
        background: var(--brand-gradient);
        border: none;
        border-radius: var(--radius-sm);
        font-weight: 600;
        font-size: 0.85rem;
        letter-spacing: 0.01em;
        transition: all var(--transition-base);
        box-shadow: 0 1px 3px rgba(13,148,136,0.2), 0 1px 2px rgba(13,148,136,0.12);
        color: white;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 14px rgba(13,148,136,0.3), 0 2px 4px rgba(13,148,136,0.15);
        transform: translateY(-1px);
        filter: brightness(1.05);
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0);
        filter: brightness(0.97);
    }
    .stButton > button[kind="secondary"] {
        border-radius: var(--radius-sm);
        font-weight: 500;
        font-size: 0.85rem;
        transition: all var(--transition-fast);
        border-color: var(--border-default);
    }
    .stButton > button[kind="secondary"]:hover {
        box-shadow: var(--shadow-sm);
        border-color: var(--border-strong);
        transform: translateY(-1px);
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        border-bottom: 1px solid var(--border-default);
        background: transparent;
        padding: 0;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        font-size: 0.85rem;
        padding: 0.75rem 1.2rem;
        border-radius: 0;
        color: var(--text-tertiary);
        transition: all var(--transition-fast);
        background: transparent;
        border-bottom: 2px solid transparent;
        margin-bottom: -1px;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-secondary);
        background: var(--brand-primary-50);
    }
    .stTabs [aria-selected="true"] {
        color: var(--brand-primary-dark) !important;
        font-weight: 600 !important;
        border-bottom: 2px solid var(--brand-primary) !important;
        background: transparent !important;
    }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 0.88rem;
        color: var(--text-primary);
    }

    /* ── Data Frames ── */
    .stDataFrame {
        border-radius: var(--radius-md);
        overflow: hidden;
        box-shadow: var(--shadow-xs);
    }

    /* ── Status Badges ── */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 0.2rem 0.65rem;
        border-radius: var(--radius-full);
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }
    .status-badge::before {
        content: '';
        width: 6px;
        height: 6px;
        border-radius: 50%;
    }
    .status-draft { background: #f1f5f9; color: #64748b; }
    .status-draft::before { background: #94a3b8; }
    .status-active { background: #ecfdf5; color: #059669; }
    .status-active::before { background: #10b981; }
    .status-review { background: #eff6ff; color: #2563eb; }
    .status-review::before { background: #3b82f6; }
    .status-complete { background: #f0fdf4; color: #16a34a; }
    .status-complete::before { background: #22c55e; }
    .status-inprogress { background: #eff6ff; color: #2563eb; }
    .status-inprogress::before { background: #3b82f6; }

    /* ── Project Type Badges ── */
    .project-type-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.18rem 0.55rem;
        border-radius: 6px;
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .badge-pdd { background: #dbeafe; color: #1d4ed8; }
    .badge-mr { background: #fef3c7; color: #92400e; }
    .badge-poa { background: #ede9fe; color: #6d28d9; }
    .badge-vpa { background: #e0e7ff; color: #4338ca; }
    .badge-valver { background: #fce7f3; color: #be185d; }

    /* ── Project Cards ── */
    .project-card {
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 1.1rem 1.3rem;
        margin-bottom: 0.5rem;
        transition: all var(--transition-base);
        cursor: default;
        position: relative;
    }
    .project-card:hover {
        border-color: var(--border-default);
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    .project-card-gs {
        border-left: 3px solid var(--gold-standard) !important;
    }
    .project-card-verra {
        border-left: 3px solid var(--verra-blue) !important;
    }
    .project-card-inner {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
    }
    .project-card-content {
        flex: 1;
        min-width: 0;
    }
    .project-card-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
        line-height: 1.3;
    }
    .project-card-meta {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
        margin-top: 4px;
    }
    .project-card-meta-item {
        font-size: 0.78rem;
        color: var(--text-tertiary);
        font-weight: 400;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .project-card-meta-sep {
        color: var(--border-strong);
        font-size: 0.6rem;
    }
    .project-card-stats {
        display: flex;
        align-items: center;
        gap: 16px;
        flex-shrink: 0;
    }
    .project-card-stat {
        text-align: center;
        min-width: 50px;
    }
    .project-card-stat-value {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-primary);
    }
    .project-card-stat-label {
        font-size: 0.65rem;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 500;
    }
    .project-card-indent {
        margin-left: 24px;
        border-left-color: var(--border-default) !important;
        opacity: 0.95;
    }
    .project-card-indent::before {
        content: '';
        position: absolute;
        left: -14px;
        top: 50%;
        width: 10px;
        height: 1px;
        background: var(--border-default);
    }

    /* ── Section Status Cards ── */
    .section-card-drafted { border-left: 3px solid #22c55e !important; }
    .section-card-empty { border-left: 3px solid var(--border-default) !important; }
    .section-card-revision { border-left: 3px solid #f59e0b !important; }

    /* ── Step Indicator ── */
    .step-indicator {
        display: flex;
        gap: 0;
        align-items: center;
        padding: 0.5rem 0;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 5px;
        padding: 0.3rem 0.7rem;
        font-size: 0.72rem;
        font-weight: 500;
        color: var(--text-tertiary);
        border-radius: var(--radius-full);
        transition: all var(--transition-fast);
    }
    .step-item.active {
        background: var(--brand-primary-50);
        color: var(--brand-primary-dark);
        font-weight: 600;
    }
    .step-item.done { color: #16a34a; }
    .step-arrow {
        color: var(--border-strong);
        font-size: 0.7rem;
        margin: 0 1px;
    }

    /* ── Document Toggle Cards ── */
    .doc-toggle-card {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-sm);
        margin-bottom: 0.4rem;
        transition: all var(--transition-fast);
    }
    .doc-toggle-card:hover {
        border-color: var(--border-default);
        box-shadow: var(--shadow-sm);
    }

    /* ── Type Selector Cards ── */
    .type-selector-card {
        padding: 1.3rem 1rem;
        border: 2px solid var(--border-default);
        border-radius: var(--radius-md);
        text-align: center;
        cursor: pointer;
        transition: all var(--transition-base);
        background: var(--surface-raised);
    }
    .type-selector-card:hover {
        border-color: var(--brand-primary-light);
        box-shadow: 0 4px 14px rgba(13,148,136,0.12);
        transform: translateY(-2px);
    }
    .type-selector-card.selected {
        border-color: var(--brand-primary);
        background: var(--brand-primary-50);
        box-shadow: 0 4px 14px rgba(13,148,136,0.12);
    }

    /* ── Form Inputs ── */
    .stButton > button, .stSelectbox, .stTextInput input {
        transition: all var(--transition-fast);
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
        border-radius: var(--radius-sm) !important;
        border-color: var(--border-default) !important;
        font-size: 0.88rem;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--brand-primary) !important;
        box-shadow: 0 0 0 3px rgba(13,148,136,0.1) !important;
    }

    /* ── Dividers ── */
    hr {
        border-color: var(--border-subtle) !important;
        margin: 1rem 0 !important;
    }

    /* ── Hide fullscreen button ── */
    div[data-testid="stMetric"] button[title="View fullscreen"] {
        display: none;
    }

    /* ── Empty State ── */
    .empty-state {
        text-align: center;
        padding: 3.5rem 2rem;
        background: var(--surface-raised);
        border-radius: var(--radius-lg);
        border: 1px dashed var(--border-strong);
        margin: 1.5rem 0;
    }
    .empty-state-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        opacity: 0.4;
    }
    .empty-state-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    .empty-state-desc {
        font-size: 0.88rem;
        color: var(--text-secondary);
        line-height: 1.6;
        max-width: 480px;
        margin: 0 auto;
    }

    /* ── Workspace Header ── */
    .workspace-header {
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-xs);
    }
    .workspace-header-top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
    }
    .workspace-header h1 {
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--text-primary);
        margin: 4px 0 6px;
        line-height: 1.2;
    }
    .workspace-header-meta {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 4px;
    }
    .workspace-meta-item {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 0.82rem;
        color: var(--text-secondary);
        font-weight: 400;
    }
    .workspace-meta-dot {
        width: 3px;
        height: 3px;
        border-radius: 50%;
        background: var(--border-strong);
    }
    .workspace-header-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0.35rem 0.75rem;
        border-radius: var(--radius-sm);
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    }
    .workspace-badge-gs {
        background: var(--gold-standard-bg);
        color: var(--gold-standard);
        border: 1px solid rgba(184,134,11,0.15);
    }
    .workspace-badge-verra {
        background: var(--verra-blue-bg);
        color: var(--verra-blue);
        border: 1px solid rgba(37,99,235,0.15);
    }

    /* ── AI Powered Badge ── */
    .ai-badge {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        padding: 0.2rem 0.6rem;
        border-radius: var(--radius-full);
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        background: linear-gradient(135deg, rgba(13,148,136,0.08), rgba(45,212,191,0.08));
        color: var(--brand-primary-dark);
        border: 1px solid rgba(13,148,136,0.12);
    }

    /* ── Stat Cards (used in project list) ── */
    .stat-pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 0.2rem 0.55rem;
        border-radius: var(--radius-full);
        font-size: 0.72rem;
        font-weight: 500;
        background: var(--surface-sunken);
        color: var(--text-secondary);
    }

    /* ── Progress Bar override ── */
    .stProgress > div > div > div {
        background: var(--brand-gradient) !important;
        border-radius: var(--radius-full);
    }
    .stProgress > div > div {
        background: var(--surface-sunken);
        border-radius: var(--radius-full);
    }

    /* ── Toast / Success / Info ── */
    .stAlert {
        border-radius: var(--radius-sm) !important;
    }

    /* ── Overview Metric Cards ── */
    .overview-metrics {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-bottom: 1.5rem;
    }
    .overview-metric-card {
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 1.2rem 1.4rem;
        box-shadow: var(--shadow-xs);
        transition: all var(--transition-base);
        position: relative;
        overflow: hidden;
    }
    .overview-metric-card:hover {
        box-shadow: var(--shadow-md);
        border-color: var(--border-default);
        transform: translateY(-2px);
    }
    .overview-metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
    }
    .overview-metric-card.metric-teal::before { background: var(--brand-gradient); }
    .overview-metric-card.metric-blue::before { background: linear-gradient(90deg, #2563eb, #3b82f6); }
    .overview-metric-card.metric-amber::before { background: linear-gradient(90deg, #d97706, #f59e0b); }
    .overview-metric-card.metric-green::before { background: linear-gradient(90deg, #059669, #10b981); }
    .overview-metric-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-tertiary);
        margin-bottom: 6px;
    }
    .overview-metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    .overview-metric-sub {
        font-size: 0.78rem;
        color: var(--text-secondary);
        margin-top: 4px;
        font-weight: 400;
    }

    /* ── Quick Actions Bar ── */
    .quick-actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 12px;
    }
    .quick-action-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0.4rem 0.85rem;
        border-radius: var(--radius-sm);
        font-size: 0.78rem;
        font-weight: 500;
        color: var(--text-secondary);
        background: var(--surface-sunken);
        border: 1px solid var(--border-subtle);
        cursor: pointer;
        transition: all var(--transition-fast);
        text-decoration: none;
    }
    .quick-action-btn:hover {
        color: var(--brand-primary-dark);
        background: var(--brand-primary-50);
        border-color: rgba(13,148,136,0.2);
    }

    /* ── Activity Feed ── */
    .activity-feed {
        display: block;
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 1.2rem 1.4rem;
        box-shadow: var(--shadow-xs);
    }
    .activity-feed-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .activity-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 8px 0;
        border-bottom: 1px solid var(--border-subtle);
    }
    .activity-item:last-child {
        border-bottom: none;
    }
    .activity-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        flex-shrink: 0;
        margin-top: 5px;
        display: inline-block;
    }
    .activity-dot-green { background: #10b981; }
    .activity-dot-blue { background: #3b82f6; }
    .activity-dot-amber { background: #f59e0b; }
    .activity-dot-teal { background: #0d9488; }
    .activity-dot-purple { background: #8b5cf6; }
    .activity-text {
        font-size: 0.82rem;
        color: var(--text-secondary);
        line-height: 1.4;
    }
    .activity-time {
        font-size: 0.7rem;
        color: var(--text-tertiary);
        margin-top: 2px;
    }

    /* ── Status Indicator Dots ── */
    .status-dot {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 0.78rem;
        font-weight: 500;
    }
    .status-dot::before {
        content: '';
        width: 7px;
        height: 7px;
        border-radius: 50%;
        flex-shrink: 0;
    }
    .status-dot-green::before { background: #10b981; }
    .status-dot-amber::before { background: #f59e0b; }
    .status-dot-red::before { background: #ef4444; }

    /* ── Enhanced Section Headers ── */
    .section-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 0.5rem 0;
        margin-bottom: 0.5rem;
    }
    .section-header-icon {
        width: 28px;
        height: 28px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .section-header-icon-teal { background: rgba(13,148,136,0.1); color: #0d9488; }
    .section-header-icon-blue { background: rgba(37,99,235,0.1); color: #2563eb; }
    .section-header-icon-amber { background: rgba(217,119,6,0.1); color: #d97706; }
    .section-header-icon-green { background: rgba(5,150,105,0.1); color: #059669; }
    .section-header-icon-purple { background: rgba(139,92,246,0.1); color: #8b5cf6; }
    .section-header-text {
        font-size: 0.95rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    /* ── Next Steps Panel ── */
    .next-steps-panel {
        background: linear-gradient(135deg, var(--brand-primary-50) 0%, rgba(255,255,255,0.8) 100%);
        border: 1px solid rgba(13,148,136,0.15);
        border-radius: var(--radius-md);
        padding: 1.2rem 1.4rem;
        margin-bottom: 1rem;
    }
    .next-steps-title {
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--brand-primary-dark);
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .next-step-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 8px 12px;
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-sm);
        margin-bottom: 6px;
        transition: all var(--transition-fast);
    }
    .next-step-item:hover {
        border-color: var(--brand-primary-light);
        box-shadow: var(--shadow-sm);
    }
    .next-step-num {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        background: var(--brand-primary);
        color: white;
        font-size: 0.68rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        margin-top: 1px;
    }
    .next-step-text {
        font-size: 0.82rem;
        color: var(--text-primary);
        font-weight: 500;
        line-height: 1.4;
    }
    .next-step-desc {
        font-size: 0.75rem;
        color: var(--text-secondary);
        font-weight: 400;
        margin-top: 2px;
    }

    /* ── Readiness Banner ── */
    .readiness-banner {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 0.6rem 1rem;
        border-radius: var(--radius-sm);
        font-size: 0.8rem;
        font-weight: 500;
        margin-bottom: 1rem;
    }
    .readiness-banner-ready {
        background: #ecfdf5;
        border: 1px solid rgba(16,185,129,0.2);
        color: #065f46;
    }
    .readiness-banner-warning {
        background: #fffbeb;
        border: 1px solid rgba(245,158,11,0.2);
        color: #92400e;
    }
    .readiness-banner-info {
        background: #eff6ff;
        border: 1px solid rgba(59,130,246,0.2);
        color: #1e40af;
    }
    .readiness-banner-icon {
        flex-shrink: 0;
    }

    /* ── Copilot Action Card ── */
    .copilot-action-card {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 10px 14px;
        background: linear-gradient(135deg, var(--brand-primary-50) 0%, rgba(255,255,255,0.9) 100%);
        border: 1px solid rgba(13,148,136,0.2);
        border-radius: var(--radius-sm);
        margin: 6px 0;
        font-size: 0.8rem;
    }
    .copilot-action-icon {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: var(--brand-primary);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .copilot-action-icon svg { width: 14px; height: 14px; }
    .copilot-action-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--brand-primary-dark);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    .copilot-action-text {
        color: var(--text-primary);
        font-weight: 500;
        line-height: 1.4;
    }
    .copilot-action-error {
        background: #fef2f2;
        border-color: rgba(239,68,68,0.2);
    }
    .copilot-action-error .copilot-action-icon {
        background: #ef4444;
    }
    .copilot-action-error .copilot-action-label {
        color: #b91c1c;
    }
    .copilot-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        padding: 4px 0;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: var(--radius-full); }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }

    /* ── Workspace home hero ── */
    .ws-hero {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        padding: 0.5rem 0 1.6rem 0;
        gap: 1rem;
    }
    .ws-hero-text h1 {
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: var(--text-primary);
        margin: 0 0 0.3rem 0;
        line-height: 1.2;
    }
    .ws-hero-text p {
        font-size: 0.9rem;
        color: var(--text-secondary);
        margin: 0;
        line-height: 1.5;
    }
    .ws-hero-actions {
        display: flex;
        gap: 8px;
        align-items: center;
        flex-shrink: 0;
        padding-top: 6px;
    }
    .ws-hero-btn-secondary {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 0.5rem 0.9rem;
        border: 1px solid var(--border-default);
        border-radius: var(--radius-sm);
        font-size: 0.83rem;
        font-weight: 500;
        color: var(--text-secondary);
        background: var(--surface-raised);
        cursor: pointer;
        text-decoration: none;
        transition: all var(--transition-fast);
        white-space: nowrap;
    }
    .ws-hero-btn-secondary:hover {
        border-color: var(--border-strong);
        color: var(--text-primary);
        box-shadow: var(--shadow-sm);
    }

    /* ── Empty state ── */
    .empty-state-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 4rem 2rem;
        border: 1.5px dashed var(--border-default);
        border-radius: var(--radius-lg);
        background: var(--surface-raised);
        margin: 2rem 0;
    }
    .empty-state-icon {
        width: 56px;
        height: 56px;
        border-radius: var(--radius-md);
        background: var(--brand-primary-50);
        border: 1px solid var(--brand-primary-100);
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1.25rem;
        color: var(--brand-primary);
    }
    .empty-state-card h3 {
        font-size: 1.05rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 0.5rem 0;
    }
    .empty-state-card p {
        font-size: 0.88rem;
        color: var(--text-secondary);
        line-height: 1.55;
        margin: 0 0 1.6rem 0;
        max-width: 380px;
    }

    /* ── Sidebar copilot CTA ── */
    .sidebar-copilot-cta {
        margin: 0.5rem 0 0.75rem 0;
        padding: 0.65rem 0.85rem;
        background: rgba(13,148,136,0.12);
        border: 1px solid rgba(13,148,136,0.22);
        border-radius: var(--radius-sm);
        cursor: pointer;
        transition: all var(--transition-fast);
    }
    .sidebar-copilot-cta:hover {
        background: rgba(13,148,136,0.2);
        border-color: rgba(13,148,136,0.38);
    }
    .sidebar-copilot-cta-label {
        font-size: 0.83rem;
        font-weight: 600;
        color: #5eead4;
        display: flex;
        align-items: center;
        gap: 7px;
    }
    .sidebar-copilot-cta-sub {
        font-size: 0.7rem;
        color: #64748b;
        margin-top: 2px;
        padding-left: 22px;
    }
    .sidebar-copilot-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #10b981;
        flex-shrink: 0;
        box-shadow: 0 0 0 2px rgba(16,185,129,0.25);
    }

    /* ── Project workspace header ── */
    .ws-header-card {
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
        box-shadow: var(--shadow-xs);
    }
    .ws-header-badges {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 0.6rem;
        flex-wrap: wrap;
    }
    .ws-header-title {
        font-size: 1.4rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--text-primary);
        margin: 0 0 0.5rem 0;
        line-height: 1.25;
    }
    .ws-header-meta {
        display: flex;
        align-items: center;
        gap: 0;
        flex-wrap: wrap;
        font-size: 0.82rem;
        color: var(--text-secondary);
    }
    .ws-meta-sep {
        margin: 0 8px;
        color: var(--border-strong);
    }

    /* ── Quick action row ── */
    .qa-copilot-hint {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.78rem;
        color: var(--text-tertiary);
        padding-top: 0.5rem;
    }
    .qa-copilot-hint-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #10b981;
        flex-shrink: 0;
    }

    /* ── Back breadcrumb ── */
    .ws-breadcrumb {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.8rem;
        color: var(--text-tertiary);
        margin-bottom: 1rem;
        font-weight: 500;
    }

    /* ── Project card hover elevation ── */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] > div {
        transition: box-shadow var(--transition-base), transform var(--transition-base);
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    /* ══════════════════════════════════════════════
       Wave 2 — Premium dashboard components
       ══════════════════════════════════════════════ */

    /* ── Stat cards (replace st.metric) ── */
    .stat-card {
        background: var(--surface-raised);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-md);
        padding: 1.4rem 1.5rem 1.2rem 1.5rem;
        box-shadow: var(--shadow-xs);
        transition: all var(--transition-base);
        position: relative;
        overflow: hidden;
        height: 100%;
    }
    .stat-card::after {
        content: '';
        position: absolute;
        bottom: 0; left: 0; right: 0;
        height: 2px;
        background: var(--brand-gradient);
        opacity: 0;
        transition: opacity var(--transition-base);
    }
    .stat-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
        border-color: var(--border-default);
    }
    .stat-card:hover::after {
        opacity: 1;
    }
    .stat-card-icon {
        width: 34px;
        height: 34px;
        border-radius: var(--radius-sm);
        background: var(--brand-primary-50);
        border: 1px solid var(--brand-primary-100);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
        color: var(--brand-primary);
    }
    .stat-card-value {
        font-size: 2.1rem;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.035em;
        line-height: 1;
        margin-bottom: 0.3rem;
    }
    .stat-card-label {
        font-size: 0.76rem;
        font-weight: 600;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }
    .stat-card-desc {
        font-size: 0.72rem;
        color: var(--text-tertiary);
        margin-top: 0.25rem;
        font-weight: 400;
    }

    /* ── Project card interior (improved) ── */
    .pc-inner {
        display: flex;
        flex-direction: column;
        gap: 0;
    }
    .pc-header-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 0.3rem;
        flex-wrap: wrap;
    }
    .pc-title {
        font-size: 0.97rem;
        font-weight: 600;
        color: var(--text-primary);
        letter-spacing: -0.01em;
        line-height: 1.3;
    }
    .pc-meta-row {
        display: flex;
        align-items: center;
        gap: 0;
        flex-wrap: wrap;
        font-size: 0.79rem;
        color: var(--text-tertiary);
        margin-top: 0.1rem;
        margin-bottom: 0.55rem;
        line-height: 1.5;
    }
    .pc-meta-sep {
        margin: 0 6px;
        color: var(--border-strong);
        font-size: 0.6rem;
    }
    .pc-footer-row {
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .pc-doc-count {
        font-size: 0.75rem;
        color: var(--text-tertiary);
        font-weight: 500;
    }
    .pc-child-pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        color: var(--text-secondary);
        background: var(--surface-sunken);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-full);
        padding: 0.1rem 0.55rem;
    }

    /* ── Better container padding ── */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] > div[data-testid="stVerticalBlock"] {
        padding: 0.5rem 0.6rem;
    }

    /* ── Projects section header ── */
    .projects-section-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.5rem 0 0.75rem 0;
        margin-bottom: 0.25rem;
    }
    .projects-section-title {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-tertiary);
    }

    /* ── Chat Widget ── */
    .chat-container {
        border: 1px solid var(--border-default, #e5e7eb);
        border-radius: var(--radius-lg, 12px);
        background: var(--surface-primary, #ffffff);
        box-shadow: var(--shadow-md, 0 4px 12px rgba(0,0,0,0.08));
        overflow: hidden;
    }
    .chat-header {
        background: linear-gradient(135deg, #0d9488, #0f766e);
        color: #ffffff;
        padding: 12px 16px;
        font-weight: 600;
        font-size: 0.9rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .chat-header-icon {
        width: 24px; height: 24px;
        background: rgba(255,255,255,0.2);
        border-radius: 6px;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.75rem;
    }
    .chat-messages {
        max-height: 400px;
        overflow-y: auto;
        padding: 12px 16px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .chat-msg {
        padding: 10px 14px;
        border-radius: 12px;
        font-size: 0.85rem;
        line-height: 1.5;
        max-width: 85%;
        word-wrap: break-word;
    }
    .chat-msg-user {
        background: linear-gradient(135deg, #0d9488, #0f766e);
        color: #ffffff;
        align-self: flex-end;
        border-bottom-right-radius: 4px;
    }
    .chat-msg-assistant {
        background: var(--surface-secondary, #f8fafc);
        color: var(--text-primary, #1a1a2e);
        border: 1px solid var(--border-default, #e5e7eb);
        align-self: flex-start;
        border-bottom-left-radius: 4px;
    }
    .chat-msg-assistant p { margin: 0 0 6px 0; }
    .chat-msg-assistant p:last-child { margin-bottom: 0; }
    .chat-context-badge {
        display: inline-block;
        background: rgba(13,148,136,0.1);
        color: #0d9488;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 10px;
        margin-left: 8px;
    }
</style>
""", unsafe_allow_html=True)

PAGES = ["Workspace", "Portfolio", "Admin"]

SVG_ICONS = {
    "projects": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>',
    "intelligence": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>',
    "admin": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',
    "docs": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>',
    "globe": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>',
    "methodology": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
    "setup": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',
    "parameters": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/><line x1="2" x2="6" y1="14" y2="14"/><line x1="10" x2="14" y1="8" y2="8"/><line x1="18" x2="22" y1="16" y2="16"/></svg>',
    "er_model": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>',
    "write": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>',
    "review": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    "audit": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
    "findings": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    "lifecycle": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "monitoring": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
    "export": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>',
    "activity": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>',
}

with st.sidebar:
    st.markdown("""
    <div class="brand-header">
        <div class="brand-logo-row">
            <div class="brand-icon">C</div>
            <div>
                <div style="font-size:1.15rem;font-weight:700;color:#f1f5f9;letter-spacing:-0.02em;line-height:1.1;">CarbonGPT</div>
            </div>
        </div>
        <div class="brand-tagline">AI Carbon Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">Navigation</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", PAGES, key="nav_page", label_visibility="collapsed")

    st.markdown('<div style="flex:1;min-height:2rem;"></div>', unsafe_allow_html=True)
    st.markdown('<hr style="border-color:rgba(255,255,255,0.06);margin:0.5rem 0;"/>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-copilot-cta">
        <div class="sidebar-copilot-cta-label">
            <span class="sidebar-copilot-dot"></span>
            AI Copilot
        </div>
        <div class="sidebar-copilot-cta-sub">Ask anything about your project</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Open Copilot", key="sidebar_copilot_btn", use_container_width=True):
        st.session_state.chat_open = True
        st.rerun()
    st.markdown('<div class="sidebar-footer"><div class="sidebar-footer-version">CarbonGPT v1.0</div></div>', unsafe_allow_html=True)


def _render_ai_result(ai_result):
    global_summary = ai_result.get("global_summary", {})
    risk = global_summary.get("overall_risk", "UNKNOWN")
    risk_colors = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}
    risk_color = risk_colors.get(risk, "red")

    st.markdown(f"### Overall Risk: :{risk_color}[**{risk}**]")

    compliance_alerts = ai_result.get("compliance_alerts", [])
    if compliance_alerts:
        st.markdown("### Compliance Alerts")
        for alert in compliance_alerts:
            sev = alert.get("severity", "info")
            meth = f" (methodology: {alert['methodology']})" if alert.get("methodology") else ""
            if sev == "error":
                st.error(f"**{alert['title']}**{meth}: {alert['description']}")
            elif sev == "warning":
                st.warning(f"**{alert['title']}**{meth}: {alert['description']}")
            else:
                st.info(f"{alert['title']}{meth}: {alert['description']}")
            if alert.get("source_url"):
                st.markdown(f"  Source: [{alert.get('source_description', 'Link')}]({alert['source_url']})")
        st.divider()

    if global_summary.get("top_issues"):
        st.markdown("**Top Issues:**")
        for issue in global_summary["top_issues"]:
            st.markdown(f"- {issue}")

    if global_summary.get("top_actions"):
        st.markdown("**Priority Actions:**")
        for action in global_summary["top_actions"]:
            st.markdown(f"- {action}")

    if global_summary.get("coherence_flags"):
        st.markdown("**Coherence Flags:**")
        for flag in global_summary["coherence_flags"]:
            st.markdown(f"- {flag}")

    st.divider()
    st.markdown("### Section-by-Section Review")

    for review in ai_result.get("per_section_reviews", []):
        sec_id = review["section_id"]
        sec_title = review["section_title"]
        sec_score = review["completeness_score"]

        if sec_score >= 80:
            sec_label = "PASS"
        elif sec_score >= 50:
            sec_label = "REVIEW"
        else:
            sec_label = "FAIL"

        with st.expander(f"[{sec_label}] {sec_id}: {sec_title} -- Score: {sec_score}/100"):
            if review.get("issues"):
                st.markdown("**Issues:**")
                for issue in review["issues"]:
                    st.markdown(f"- {issue}")

            if review.get("suggested_fixes"):
                st.markdown("**Suggested Fixes:**")
                for fix in review["suggested_fixes"]:
                    st.markdown(f"- {fix}")

            if review.get("questions_for_user"):
                st.markdown("**Questions for You:**")
                for q in review["questions_for_user"]:
                    st.markdown(f"- {q}")

            if not review.get("issues") and not review.get("suggested_fixes") and not review.get("questions_for_user"):
                st.info("No issues found for this subsection.")


@st.fragment(run_every=5)
def _poll_ai_review():
    ai_task_id = st.session_state.get("ai_task_id")
    if not ai_task_id:
        return

    elapsed = time.time() - st.session_state.get("ai_task_start", time.time())
    if elapsed > 180:
        st.warning("AI Review timed out after 3 minutes. Please re-analyze to try again.")
        st.session_state.pop("ai_task_id", None)
        return

    progress = min(elapsed / 180, 0.95)
    st.progress(progress, text=f"AI review in progress... ({int(elapsed)}s)")

    try:
        poll_resp = requests.get(f"{API_BASE}/ai-review/{ai_task_id}", timeout=5)
        if poll_resp.status_code == 200:
            poll_data = poll_resp.json()
            if poll_data["status"] == "complete":
                st.session_state["ai_result"] = poll_data["result"]
                st.session_state.pop("ai_task_id", None)
                st.rerun()
            elif poll_data["status"] == "failed":
                st.error(f"AI Review failed: {poll_data.get('error', 'Unknown error')}")
                st.session_state.pop("ai_task_id", None)
    except requests.exceptions.RequestException:
        pass


def _fetch(endpoint, method="GET", timeout=None, **kwargs):
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=timeout or 10, **kwargs)
        elif method == "POST":
            resp = requests.post(url, timeout=timeout or 120, **kwargs)
        elif method == "PATCH":
            resp = requests.patch(url, timeout=timeout or 10, **kwargs)
        elif method == "DELETE":
            resp = requests.delete(url, timeout=timeout or 10, **kwargs)
        else:
            return None
        if resp.status_code >= 400:
            st.error(f"API Error: {resp.text}")
            return None
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {e}")
        return None


CATEGORY_LABELS = {
    "standard_text": "Standard Document",
    "methodology": "Methodology",
    "guidance": "Guidance Document",
    "tool": "Calculation Tool",
    "template": "Template",
    "example_pdd": "Example PDD",
    "example_mr": "Example Monitoring Report",
    "example_fvr": "Example Final Verification Report",
    "example_valver": "Example Validation/Verification Report",
    "example_other": "Example (Other)",
    "rule_update": "Rule Update",
    "other": "Other",
}
CATEGORY_OPTIONS = list(CATEGORY_LABELS.keys())


def render_repository():
    st.markdown("## Administration")
    st.caption("Document repository, compliance rules, knowledge base, and sync tools")
    st.markdown(
        "Manage your carbon standards library. Upload standards, methodologies, guidance documents, "
        "templates, and example project documentation. Documents are automatically parsed, indexed, "
        "and classified by AI."
    )

    stats = _fetch("/admin/stats")
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", stats.get("total_documents", 0), help="Total documents in the repository")
        with col2:
            st.metric("Ingested", stats.get("ingested", 0), help="Documents fully processed")
        with col3:
            st.metric("Total Words", f"{stats.get('total_words', 0):,}", help="Total words extracted")
        with col4:
            st.metric("Vector Chunks", stats.get("total_chunks", 0), help="Searchable text chunks with embeddings")

        pending = stats.get("pending", 0)
        processing = stats.get("processing", 0)
        failed = stats.get("failed", 0)
        if pending > 0 or processing > 0:
            st.info(f"Pending: {pending} | Processing: {processing}")
        if failed > 0:
            st.warning(f"Failed ingestions: {failed}")

    st.divider()

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Upload Documents",
        "Document Library",
        "Semantic Search",
        "Compliance Rules",
        "Web Intelligence",
        "Methodology Sync",
        "Manage Standards",
    ])

    with tab1:
        _render_upload()
    with tab2:
        _render_library()
    with tab3:
        _render_search()
    with tab4:
        _render_compliance_rules()
    with tab5:
        _render_web_intelligence()
    with tab6:
        _render_methodology_sync()
    with tab7:
        _render_manage_standards()


def _render_upload():
    st.subheader("Upload Documents")
    st.markdown("Upload PDF, DOCX, XLSX, or CSV files. Documents are automatically parsed, classified, and indexed.")

    standards = _fetch("/admin/standards") or []
    versions = _fetch("/admin/standard-versions") or []

    version_options = {}
    for v in versions:
        label = f"{v['standard_name']} — {v['version']} ({v['status']})"
        version_options[label] = v["id"]

    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox(
            "Document Category",
            CATEGORY_OPTIONS,
            format_func=lambda x: CATEGORY_LABELS[x],
            key="upload_category",
        )
    with col2:
        version_labels = ["Auto-detect / Not specified"] + list(version_options.keys())
        selected_version = st.selectbox("Standard & Version", version_labels, key="upload_version")

    col3, col4 = st.columns(2)
    with col3:
        reference_id = st.text_input("Reference ID (optional)", placeholder="e.g., VM0007, AMS-II.G", key="upload_ref_id")
    with col4:
        doc_version = st.text_input("Document Version (optional)", placeholder="e.g., v6.0, v09", key="upload_doc_version")

    uploaded_files = st.file_uploader(
        "Drop files here",
        type=["pdf", "docx", "xlsx", "csv"],
        accept_multiple_files=True,
        key="repo_upload_files",
    )

    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected**")

    upload_btn = st.button("Upload & Ingest", type="primary", disabled=not uploaded_files, key="repo_upload_btn")

    if upload_btn and uploaded_files:
        sv_id = version_options.get(selected_version) if selected_version != "Auto-detect / Not specified" else None
        progress = st.progress(0, text="Uploading...")

        for i, f in enumerate(uploaded_files):
            progress.progress((i + 1) / len(uploaded_files), text=f"Uploading {f.name}...")
            files_data = {"file": (f.name, f.getvalue(), "application/octet-stream")}
            form_data = {
                "category": category,
                "title": f.name.rsplit(".", 1)[0],
            }
            if sv_id:
                form_data["standard_version_id"] = str(sv_id)
            if reference_id:
                form_data["reference_id"] = reference_id
            if doc_version:
                form_data["doc_version"] = doc_version

            result = _fetch("/admin/documents/upload", method="POST", files=files_data, data=form_data)
            if result:
                st.success(f"Uploaded: {f.name} (ID: {result['id']})")
            else:
                st.error(f"Failed to upload: {f.name}")

        progress.empty()
        time.sleep(1)
        st.rerun()


def _render_library():
    st.subheader("Document Library")

    col1, col2, col3 = st.columns(3)
    with col1:
        filter_category = st.selectbox(
            "Filter by Category",
            ["All"] + CATEGORY_OPTIONS,
            format_func=lambda x: "All Categories" if x == "All" else CATEGORY_LABELS.get(x, x),
            key="filter_category",
        )
    with col2:
        versions = _fetch("/admin/standard-versions") or []
        version_options = {"All": None}
        for v in versions:
            label = f"{v['standard_name']} — {v['version']}"
            version_options[label] = v["id"]
        filter_version = st.selectbox("Filter by Standard", list(version_options.keys()), key="filter_version")
    with col3:
        st.button("Refresh", key="refresh_library")

    params = {}
    if filter_category != "All":
        params["category"] = filter_category
    sv_id = version_options.get(filter_version)
    if sv_id:
        params["standard_version_id"] = sv_id

    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    endpoint = f"/admin/documents?{query_string}" if query_string else "/admin/documents"
    documents = _fetch(endpoint) or []

    if not documents:
        st.info("No documents found. Upload some documents to get started.")
        return

    for doc in documents:
        status_icons = {
            "completed": "white_check_mark",
            "processing": "hourglass_flowing_sand",
            "pending": "clock3",
            "failed": "x",
        }
        ing_status = doc.get("ingestion_status", "pending")
        icon = status_icons.get(ing_status, "question")

        standard_info = ""
        if doc.get("standard_name"):
            standard_info = f" | {doc['standard_name']} {doc.get('standard_version', '')}"

        title = doc.get("title", "Untitled")
        cat_label = CATEGORY_LABELS.get(doc.get("category", ""), doc.get("category", ""))
        size_kb = (doc.get("file_size_bytes") or 0) / 1024

        with st.expander(f":{icon}: **{title}** — {cat_label}{standard_info}"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**Category:** {cat_label}")
                st.markdown(f"**File Type:** {doc.get('file_type', '').upper()}")
                st.markdown(f"**Size:** {size_kb:.1f} KB")
                st.markdown(f"**Ingestion:** {ing_status}")
                if doc.get("word_count"):
                    st.markdown(f"**Words:** {doc['word_count']:,}")
                if doc.get("page_count"):
                    st.markdown(f"**Pages:** {doc['page_count']}")
            with col_b:
                if doc.get("auto_detected_standard"):
                    st.markdown(f"**Detected Standard:** {doc['auto_detected_standard']}")
                if doc.get("auto_detected_version"):
                    st.markdown(f"**Detected Version:** {doc['auto_detected_version']}")
                if doc.get("auto_detected_category"):
                    st.markdown(f"**Detected Type:** {doc['auto_detected_category']}")
                if doc.get("auto_detected_applicability"):
                    st.markdown(f"**Applicability:** {doc['auto_detected_applicability']}")
                if doc.get("reference_id"):
                    st.markdown(f"**Reference ID:** {doc['reference_id']}")

            btn_col1, _, btn_col3 = st.columns(3)
            with btn_col1:
                if ing_status in ("failed", "completed"):
                    if st.button("Re-ingest", key=f"reingest_{doc['id']}"):
                        result = _fetch(f"/admin/documents/{doc['id']}/reingest", method="POST")
                        if result:
                            st.success("Re-ingestion started.")
                            time.sleep(1)
                            st.rerun()
            with btn_col3:
                if st.button("Delete", key=f"delete_{doc['id']}", type="secondary"):
                    result = _fetch(f"/admin/documents/{doc['id']}", method="DELETE")
                    if result:
                        st.success("Document deleted.")
                        time.sleep(0.5)
                        st.rerun()


def _render_search():
    st.subheader("Semantic Search")
    st.markdown("Search across all ingested documents using natural language.")

    query = st.text_input(
        "Search query",
        placeholder="e.g., additionality requirements for REDD+ projects",
        key="search_query",
    )
    col1, col2 = st.columns(2)
    with col1:
        limit = st.slider("Results", 3, 20, 5, key="search_limit")
    with col2:
        search_btn = st.button("Search", type="primary", disabled=not query, key="search_btn")

    if search_btn and query:
        with st.spinner("Searching..."):
            results = _fetch(f"/admin/search?q={query}&limit={limit}")

        if results is None:
            return
        if not results:
            st.info("No results found. Make sure documents have been ingested with embeddings.")
            return

        st.markdown(f"**{len(results)} results found:**")
        for i, r in enumerate(results):
            distance = r.get("distance", 0)
            similarity = max(0, 1 - distance)
            doc_title = r.get("document_title", "Unknown")
            standard = r.get("standard_name", "")
            version = r.get("standard_version", "")
            category = r.get("document_category", "")

            with st.expander(
                f"**{i+1}.** {doc_title} ({category}) — "
                f"{standard} {version} — Relevance: {similarity:.0%}"
            ):
                st.markdown(r.get("content", ""))


RULE_TYPE_LABELS = {
    "methodology_status": "Methodology Status",
    "methodology_transition": "Methodology Transition",
    "crediting_period": "Crediting Period",
    "eligibility": "Eligibility Requirement",
    "regulatory": "Regulatory Change",
    "default_value": "Default Value Update",
    "fee_structure": "Fee Structure",
    "general": "General Rule",
}

SEVERITY_LABELS = {
    "error": "Critical",
    "warning": "Warning",
    "info": "Info",
}


def _render_compliance_rules():
    st.subheader("Compliance Rules")
    st.markdown(
        "Manage compliance intelligence rules. These rules are automatically checked "
        "during AI review to catch issues like deprecated methodologies, regulatory changes, "
        "and eligibility requirements. Rules can be added manually or proposed by the AI."
    )

    rules = _fetch("/admin/compliance-rules") or []
    standards = _fetch("/admin/standards") or []

    active_rules = [r for r in rules if r["status"] == "active"]
    proposed_rules = [r for r in rules if r["status"] == "proposed"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Active Rules", len(active_rules))
    with col2:
        st.metric("Pending Review", len(proposed_rules))
    with col3:
        st.metric("Total Rules", len(rules))

    if proposed_rules:
        st.divider()
        st.markdown("#### Proposed Rules (Pending Admin Review)")
        st.markdown("These rules were discovered by AI during reviews. Approve or reject them.")
        for rule in proposed_rules:
            severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(rule["severity"], "⚪")
            with st.expander(f"{severity_icon} {rule['title']} — {RULE_TYPE_LABELS.get(rule['rule_type'], rule['rule_type'])}"):
                st.markdown(f"**Description:** {rule['description']}")
                if rule.get("source_url"):
                    st.markdown(f"**Source:** [{rule['source_description'] or rule['source_url']}]({rule['source_url']})")
                if rule.get("conditions"):
                    st.json(rule["conditions"])
                st.markdown(f"**Discovered by:** {rule['discovered_by']}")

                acol1, acol2 = st.columns(2)
                with acol1:
                    if st.button("Approve", key=f"approve_{rule['id']}", type="primary"):
                        _fetch(f"/admin/compliance-rules/{rule['id']}", method="PATCH",
                               json={"status": "active"})
                        st.success("Rule approved!")
                        time.sleep(0.5)
                        st.rerun()
                with acol2:
                    if st.button("Reject", key=f"reject_{rule['id']}"):
                        _fetch(f"/admin/compliance-rules/{rule['id']}", method="PATCH",
                               json={"status": "rejected"})
                        st.info("Rule rejected.")
                        time.sleep(0.5)
                        st.rerun()

    st.divider()
    st.markdown("#### Active Rules")
    if not active_rules:
        st.info("No active compliance rules yet. Add rules below or let the AI discover them during reviews.")
    else:
        for rule in active_rules:
            severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(rule["severity"], "⚪")
            std_name = rule.get("standard_name") or "All Standards"
            with st.expander(f"{severity_icon} {rule['title']} — {std_name} — {RULE_TYPE_LABELS.get(rule['rule_type'], rule['rule_type'])}"):
                st.markdown(f"**Description:** {rule['description']}")
                st.markdown(f"**Severity:** {SEVERITY_LABELS.get(rule['severity'], rule['severity'])}")
                if rule.get("effective_date"):
                    st.markdown(f"**Effective:** {rule['effective_date']}")
                if rule.get("expiry_date"):
                    st.markdown(f"**Expires:** {rule['expiry_date']}")
                if rule.get("source_url"):
                    st.markdown(f"**Source:** [{rule.get('source_description') or 'Link'}]({rule['source_url']})")
                if rule.get("conditions"):
                    st.json(rule["conditions"])
                if st.button("Delete", key=f"del_rule_{rule['id']}"):
                    _fetch(f"/admin/compliance-rules/{rule['id']}", method="DELETE")
                    st.rerun()

    st.divider()
    with st.expander("Add New Compliance Rule"):
        std_options = {"All Standards": None}
        for s in standards:
            std_options[s["name"]] = s["id"]

        r_col1, r_col2 = st.columns(2)
        with r_col1:
            new_rule_type = st.selectbox(
                "Rule Type",
                list(RULE_TYPE_LABELS.keys()),
                format_func=lambda x: RULE_TYPE_LABELS[x],
                key="new_rule_type"
            )
        with r_col2:
            new_severity = st.selectbox(
                "Severity",
                list(SEVERITY_LABELS.keys()),
                format_func=lambda x: SEVERITY_LABELS[x],
                key="new_rule_severity"
            )

        new_rule_std = st.selectbox("Standard", list(std_options.keys()), key="new_rule_std")
        new_rule_title = st.text_input("Title", key="new_rule_title",
                                       placeholder="e.g., AMS-II.G deprecated for VCS projects")
        new_rule_desc = st.text_area("Description", key="new_rule_desc",
                                     placeholder="e.g., AMS-II.G is no longer accepted as a standalone methodology under VCS. Projects must use VMR0006 v1.2 instead.")
        new_rule_source = st.text_input("Source URL (optional)", key="new_rule_source",
                                        placeholder="e.g., https://verra.org/...")
        new_rule_source_desc = st.text_input("Source Description (optional)", key="new_rule_source_desc",
                                             placeholder="e.g., Verra announcement, July 2023")

        st.markdown("**Conditions (JSON)** — Define matching criteria:")
        st.markdown("- `affected_methodologies`: list of methodology IDs to match (e.g., `[\"AMS-II.G\", \"AMS-IIG\"]`)")
        st.markdown("- `keywords`: list of keywords to search in document text")
        st.markdown("- `check_in_document`: list of keywords that trigger this rule when found")
        new_rule_conditions = st.text_area(
            "Conditions JSON",
            value='{"affected_methodologies": [], "keywords": []}',
            key="new_rule_conditions"
        )

        r_col3, r_col4 = st.columns(2)
        with r_col3:
            new_rule_eff = st.text_input("Effective Date (YYYY-MM-DD, optional)", key="new_rule_eff")
        with r_col4:
            new_rule_exp = st.text_input("Expiry Date (YYYY-MM-DD, optional)", key="new_rule_exp")

        if st.button("Create Rule", key="create_rule_btn", type="primary"):
            if new_rule_title and new_rule_desc:
                import json as _json
                try:
                    conditions = _json.loads(new_rule_conditions)
                except Exception:
                    st.error("Invalid JSON in conditions field.")
                    conditions = None

                if conditions is not None:
                    result = _fetch("/admin/compliance-rules", method="POST",
                                    json={
                                        "standard_id": std_options[new_rule_std],
                                        "rule_type": new_rule_type,
                                        "severity": new_severity,
                                        "title": new_rule_title,
                                        "description": new_rule_desc,
                                        "conditions": conditions,
                                        "source_url": new_rule_source or None,
                                        "source_description": new_rule_source_desc or None,
                                        "effective_date": new_rule_eff or None,
                                        "expiry_date": new_rule_exp or None,
                                        "status": "active",
                                        "discovered_by": "admin",
                                    })
                    if result:
                        st.success("Compliance rule created!")
                        time.sleep(0.5)
                        st.rerun()
            else:
                st.warning("Title and description are required.")


def _render_methodology_sync():
    st.subheader("Document Sync")
    st.markdown(
        "Download program standards, methodologies, guides, templates, and project "
        "documents from Verra, CDM/UNFCCC, and Gold Standard public catalogs and registries. "
        "Documents are stored in the repository, parsed, and embedded for AI-powered reviews."
    )

    status = _fetch("/admin/methodology-sync/status")
    if status:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Documents", status.get("total_documents", 0))
        with col2:
            by_source = status.get("by_source", {})
            st.metric("Verra", by_source.get("verra", 0))
        with col3:
            st.metric("CDM", by_source.get("cdm", 0))
        with col4:
            st.metric("Gold Standard", by_source.get("goldstandard", 0))
        with col5:
            st.metric("Manual", by_source.get("manual", 0))

        by_category = status.get("by_category", {})
        if by_category:
            cat_parts = []
            for cat, count in sorted(by_category.items()):
                cat_parts.append(f"{cat}: {count}")
            st.markdown(f"**By category:** {' | '.join(cat_parts)}")

        scheduler_status = "Active" if status.get("scheduler_active") else "Inactive"
        interval = status.get("sync_interval_hours", 168)
        st.markdown(
            f"**Auto-sync scheduler:** {scheduler_status} "
            f"(interval: {interval} hours / {interval // 24} days). "
            f"Set `CARBONGPT_AUTO_SYNC=true` to enable."
        )

    st.divider()

    col_sync, col_config = st.columns(2)

    with col_sync:
        st.markdown("#### Run Sync Now")

        source_options = {
            "Verra VCS": "verra",
            "CDM/UNFCCC": "cdm",
            "Gold Standard": "goldstandard",
        }
        selected_sources = st.multiselect(
            "Sources to sync",
            options=list(source_options.keys()),
            default=list(source_options.keys()),
            key="sync_sources",
        )

        max_per_source = st.slider(
            "Max documents per source",
            min_value=5,
            max_value=200,
            value=50,
            step=5,
            key="sync_max",
        )

        include_program = st.checkbox(
            "Include program standards, guides, and templates",
            value=True,
            key="sync_program_docs",
        )

        include_registry = st.checkbox(
            "Include real project documents from registries (PDs, MRs, validation/verification reports)",
            value=False,
            key="sync_registry",
        )

        if include_registry:
            max_projects = st.slider(
                "Max registry projects to scan",
                min_value=1,
                max_value=500,
                value=10,
                step=5,
                key="sync_max_projects",
            )
            discover_projects = st.checkbox(
                "Auto-discover projects (search Verra registry API for all VCS projects instead of using seed list)",
                value=max_projects > 10,
                key="sync_discover",
            )
            st.caption(
                "Verra: direct PDF download via registry API (PDs, MRs, validation/verification reports, ~30-80 docs/project). "
                "Gold Standard: project metadata via public API (document downloads require auth). "
                "CDM/UNFCCC: project documents not available (bot protection)."
            )
        else:
            max_projects = 5
            discover_projects = False

        dry_run = st.checkbox("Dry run (preview only, no downloads)", value=True, key="sync_dry_run")

        if st.button("Start Sync", key="sync_start_btn"):
            sources = [source_options[s] for s in selected_sources]
            with st.spinner("Syncing documents (this may take several minutes)..."):
                result = _fetch(
                    "/admin/methodology-sync",
                    method="POST",
                    json={
                        "sources": sources,
                        "max_per_source": max_per_source,
                        "dry_run": dry_run,
                        "include_program_docs": include_program,
                        "include_registry_projects": include_registry,
                        "max_registry_projects": max_projects,
                        "discover_projects": discover_projects,
                    },
                )

            if result:
                skipped = result.get('skipped_no_download', 0)
                skipped_msg = f", {skipped} metadata-only" if skipped else ""
                st.success(
                    f"Sync complete: {result.get('total_found', 0)} found, "
                    f"{result.get('already_stored', 0)} already stored, "
                    f"{result.get('newly_downloaded', 0)} newly downloaded, "
                    f"{result.get('ingestion_started', 0)} ingestion started, "
                    f"{result.get('errors', 0)} errors{skipped_msg}"
                )

                details = result.get("details", [])
                if details:
                    status_counts = {}
                    category_counts = {}
                    for d in details:
                        s = d.get("status", "unknown")
                        status_counts[s] = status_counts.get(s, 0) + 1
                        cat = d.get("category", "unknown")
                        category_counts[cat] = category_counts.get(cat, 0) + 1

                    st.markdown("**By status:**")
                    for s, count in sorted(status_counts.items()):
                        st.markdown(f"- {s}: {count}")

                    st.markdown("**By type:**")
                    for cat, count in sorted(category_counts.items()):
                        st.markdown(f"- {cat}: {count}")

                    with st.expander("Details", expanded=False):
                        for d in details[:80]:
                            status_label = d.get("status", "unknown")
                            code = d.get("code", "?")
                            source = d.get("source", "?")
                            cat = d.get("category", "")
                            title = d.get("title", "")
                            line = f"[{source}/{cat}] {code}: {status_label}"
                            if title:
                                line += f" - {title[:60]}"
                            if d.get("doc_id"):
                                line += f" (doc #{d['doc_id']})"
                            st.text(line)
                        if len(details) > 80:
                            st.text(f"... and {len(details) - 80} more")
            else:
                st.error("Sync failed.")

    with col_config:
        st.markdown("#### What Gets Downloaded")
        st.markdown(
            "**Methodologies** - Active VM/VMR methodologies (Verra), CDM tools and "
            "methodology booklet, Gold Standard sector methodologies\n\n"
            "**Program Standards & Guides** - VCS Standard, Program Guide, Registration "
            "Process, Methodology Requirements, AFOLU Non-Permanence Risk Tool, "
            "GS Principles & Requirements, Safeguarding, Stakeholder Consultation, "
            "VVB Requirements, CDM Glossary, Validation Standard\n\n"
            "**Templates** - PD, MR, and ValVer report templates (Verra), "
            "MR/PDD/Validation/Verification guides (Gold Standard), CDM PDD form\n\n"
            "**Registry Projects** (optional) - Real project descriptions, monitoring reports, "
            "and validation/verification reports from the Verra public registry\n\n"
            "**Rate limiting:** 2-second delay between requests. "
            "Run dry-run first to preview."
        )


def _render_web_intelligence():
    st.subheader("Web Intelligence")
    st.markdown(
        "Search the web for methodology status updates, regulatory changes, "
        "and compliance-relevant information. Findings can be saved as proposed "
        "compliance rules for admin review."
    )

    col_verify, col_refresh = st.columns(2)

    with col_verify:
        st.markdown("#### Verify Methodology")
        meth_input = st.text_input(
            "Methodology ID",
            placeholder="e.g. AMS-II.G, VM0050, VMR0006",
            key="wi_meth_input",
        )
        standard_choice = st.selectbox(
            "Standard",
            ["Verra VCS", "Gold Standard", "CDM/UNFCCC"],
            key="wi_standard",
        )

        standards = _fetch("/admin/standards") or []
        std_id = None
        for s in standards:
            if standard_choice == "Verra VCS" and s.get("slug") == "verra":
                std_id = s["id"]
            elif standard_choice == "Gold Standard" and s.get("slug") == "goldstandard":
                std_id = s["id"]

        if st.button("Verify Status", key="wi_verify_btn", disabled=not meth_input):
            with st.spinner("Searching web and analyzing..."):
                result = _fetch(
                    "/admin/web-intelligence/verify-methodology",
                    method="POST",
                    json={"methodology": meth_input, "standard": standard_choice, "standard_id": std_id},
                )
            if result and result.get("result"):
                r = result["result"]
                status = r.get("status", "unknown")
                confidence = r.get("confidence", "unknown")

                status_colors = {
                    "approved": "green",
                    "deprecated": "red",
                    "transitioning": "orange",
                    "conditional": "yellow",
                    "unknown": "gray",
                }
                color = status_colors.get(status, "gray")
                st.markdown(f"**Status:** :{color}[{status.upper()}] (confidence: {confidence})")
                st.markdown(f"**Summary:** {r.get('summary', 'N/A')}")
                if r.get("replacement"):
                    st.info(f"Replacement: {r['replacement']}")
                if r.get("deadline"):
                    st.warning(f"Deadline: {r['deadline']}")
                if r.get("source_url"):
                    st.markdown(f"[Source]({r['source_url']})")

                if r.get("proposed_rule_title"):
                    st.divider()
                    st.markdown("**Proposed compliance rule:**")
                    st.markdown(f"- **{r['proposed_rule_title']}**")
                    st.markdown(f"  {r.get('proposed_rule_description', '')}")
                    if st.button("Save as Proposed Rule", key="wi_save_rule"):
                        save_result = _fetch(
                            "/admin/web-intelligence/propose-rule",
                            method="POST",
                            json={"methodology": meth_input, "standard": standard_choice, "standard_id": std_id},
                        )
                        if save_result and save_result.get("proposed_rule"):
                            rule_data = save_result["proposed_rule"]
                            create_result = _fetch("/admin/compliance-rules", method="POST", json=rule_data)
                            if create_result and create_result.get("id"):
                                st.success(f"Rule saved as proposed (ID: {create_result['id']}). Review it in the Compliance Rules tab.")
                            else:
                                st.error("Failed to save rule.")
                        else:
                            msg = save_result.get("message", "No rule to propose.") if save_result else "Request failed."
                            st.info(msg)
            else:
                st.error("Verification failed. Check that OPENAI_API_KEY is set.")

    with col_refresh:
        st.markdown("#### Knowledge Refresh")
        st.markdown(
            "Search for recent regulatory updates across a standard. "
            "Findings are saved as proposed rules for your review."
        )
        refresh_standard = st.selectbox(
            "Standard to research",
            ["Verra VCS", "Gold Standard", "CDM/UNFCCC"],
            key="wi_refresh_standard",
        )
        custom_topics = st.text_area(
            "Custom search topics (one per line, optional)",
            placeholder="e.g.\nVCS buffer pool update 2025\nNew cookstove methodology M0174",
            key="wi_custom_topics",
            height=100,
        )

        refresh_std_id = None
        for s in standards:
            if refresh_standard == "Verra VCS" and s.get("slug") == "verra":
                refresh_std_id = s["id"]
            elif refresh_standard == "Gold Standard" and s.get("slug") == "goldstandard":
                refresh_std_id = s["id"]

        auto_save = st.checkbox("Auto-save findings as proposed rules", value=True, key="wi_auto_save")

        if st.button("Run Knowledge Refresh", key="wi_refresh_btn"):
            topics = None
            if custom_topics.strip():
                topics = [t.strip() for t in custom_topics.strip().split("\n") if t.strip()]

            with st.spinner("Researching standard updates (this may take 30-60 seconds)..."):
                result = _fetch(
                    "/admin/web-intelligence/knowledge-refresh",
                    method="POST",
                    json={
                        "standard": refresh_standard,
                        "standard_id": refresh_std_id,
                        "topics": topics,
                        "auto_save": auto_save,
                    },
                )

            if result:
                total = result.get("total_found", 0)
                saved = result.get("saved_count", 0)

                if total == 0:
                    st.info("No new compliance-relevant findings discovered.")
                else:
                    st.success(f"Found {total} potential update(s). {saved} saved as proposed rules.")
                    for i, rule in enumerate(result.get("proposed_rules", [])):
                        sev = rule.get("severity", "info").upper()
                        with st.expander(f"[{sev}] {rule.get('title', 'Untitled')}", expanded=(i < 3)):
                            st.markdown(f"**Type:** {rule.get('rule_type', 'general')}")
                            st.markdown(f"**Description:** {rule.get('description', 'N/A')}")
                            if rule.get("source_url"):
                                st.markdown(f"**Source:** [{rule['source_url']}]({rule['source_url']})")
                            if rule.get("source_description"):
                                st.markdown(f"**Source info:** {rule['source_description']}")
            else:
                st.error("Knowledge refresh failed. Check that OPENAI_API_KEY is set.")

    st.divider()
    st.markdown("#### Web Search Configuration")
    serper_status = "Configured" if os.environ.get("SERPER_API_KEY") else "Not configured"
    openai_status = "Configured" if os.environ.get("OPENAI_API_KEY") else "Not configured"
    web_search_enabled = os.environ.get("CARBONGPT_WEB_SEARCH", "").lower() in ("1", "true", "yes")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("OpenAI API", openai_status)
    with col2:
        st.metric("Serper Search API", serper_status)
    with col3:
        st.metric("Auto Web Search in Reviews", "Enabled" if web_search_enabled else "Disabled")

    st.markdown(
        "**Setup:** Set `SERPER_API_KEY` for web search (get one at [serper.dev](https://serper.dev)). "
        "Set `CARBONGPT_WEB_SEARCH=true` to enable automatic web search during AI reviews for "
        "methodologies not found in the compliance rules database."
    )


def _render_manage_standards():
    st.subheader("Manage Standards & Versions")

    standards = _fetch("/admin/standards") or []
    versions = _fetch("/admin/standard-versions") or []

    st.markdown("**Existing Standards:**")
    for s in standards:
        s_versions = [v for v in versions if v["standard_id"] == s["id"]]
        version_str = ", ".join(f"{v['version']} ({v['status']})" for v in s_versions) or "No versions"
        st.markdown(f"- **{s['name']}** (`{s['slug']}`) — Versions: {version_str}")

    st.divider()

    with st.expander("Add New Standard"):
        new_name = st.text_input("Standard Name", key="new_std_name")
        new_slug = st.text_input("Slug", key="new_std_slug")
        new_desc = st.text_area("Description", key="new_std_desc")
        if st.button("Create Standard", key="create_std_btn"):
            if new_name and new_slug:
                result = _fetch("/admin/standards", method="POST",
                                json={"name": new_name, "slug": new_slug, "description": new_desc})
                if result:
                    st.success(f"Standard '{new_name}' created.")
                    time.sleep(0.5)
                    st.rerun()

    with st.expander("Add New Version"):
        std_options = {s["name"]: s["id"] for s in standards}
        if std_options:
            selected_std = st.selectbox("Standard", list(std_options.keys()), key="new_ver_std")
            new_ver = st.text_input("Version", key="new_ver_version")
            new_date = st.text_input("Effective Date (YYYY-MM-DD)", key="new_ver_date")
            new_status = st.selectbox("Status", ["active", "superseded", "draft"], key="new_ver_status")
            if st.button("Create Version", key="create_ver_btn"):
                if new_ver:
                    result = _fetch("/admin/standard-versions", method="POST",
                                    json={
                                        "standard_id": std_options[selected_std],
                                        "version": new_ver,
                                        "effective_date": new_date or None,
                                        "status": new_status,
                                    })
                    if result:
                        st.success(f"Version '{new_ver}' created.")
                        time.sleep(0.5)
                        st.rerun()
        else:
            st.info("Create a standard first.")


def render_intelligence():
    analytics = _fetch("/admin/projects/analytics")
    if not analytics or not analytics.get("summary"):
        st.warning("No project data available. Use the Sync tab to import projects from registries.")
        if st.button("Sync Projects Now", key="sync_empty_btn", type="primary"):
            with st.spinner("Syncing projects from registries..."):
                result = _fetch("/admin/sync-projects", method="POST")
                if result:
                    total = result.get("total_synced", 0)
                    st.success(f"Synced {total:,} projects.")
                    time.sleep(1)
                    st.rerun()
        return

    summary = analytics["summary"]

    tabs = st.tabs(["Global Overview", "Country Explorer", "Methodology Analysis",
                     "Project Browser", "Sync"])

    with tabs[0]:
        _render_global_overview(analytics, summary)

    with tabs[1]:
        _render_country_explorer(analytics)

    with tabs[2]:
        _render_methodology_analysis()

    with tabs[3]:
        _render_project_browser()

    with tabs[4]:
        _render_sync_controls(summary)


def _render_global_overview(analytics, summary):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Projects", f"{summary['total_projects']:,}",
                   help="Total carbon projects across all registries")
    with col2:
        credits = summary.get("total_estimated_credits", 0) or 0
        if credits >= 1_000_000_000:
            credits_str = f"{credits / 1_000_000_000:.1f}B"
        elif credits >= 1_000_000:
            credits_str = f"{credits / 1_000_000:.0f}M"
        else:
            credits_str = f"{credits:,}"
        st.metric("Est. Annual Credits", credits_str,
                   help="Total estimated annual emission reductions (tCO2e)")
    with col3:
        st.metric("Countries", f"{summary['total_countries']}")
    with col4:
        st.metric("Registries", f"{summary['total_registries']}")

    st.divider()

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Top 15 Countries by Project Count")
        countries = analytics.get("by_country", [])[:15]
        if countries:
            import pandas as pd
            df = pd.DataFrame(countries)
            df = df.rename(columns={"country": "Country", "project_count": "Projects", "total_credits": "Est. Credits"})
            st.bar_chart(df.set_index("Country")["Projects"])

    with col_right:
        st.subheader("Projects by Region")
        regions = analytics.get("by_region", [])
        if regions:
            import pandas as pd
            df = pd.DataFrame(regions)
            df = df.rename(columns={"region": "Region", "project_count": "Projects", "total_credits": "Est. Credits"})
            st.bar_chart(df.set_index("Region")["Projects"])

    st.divider()

    col_left2, col_right2 = st.columns(2)

    with col_left2:
        st.subheader("Project Status Distribution")
        statuses = analytics.get("by_status", [])
        if statuses:
            import pandas as pd
            df = pd.DataFrame(statuses)
            df = df.rename(columns={"status": "Status", "project_count": "Projects"})
            st.bar_chart(df.set_index("Status")["Projects"])

    with col_right2:
        st.subheader("Project Types")
        types = analytics.get("by_project_type", [])[:10]
        if types:
            import pandas as pd
            df = pd.DataFrame(types)
            df["project_type"] = df["project_type"].str[:40]
            df = df.rename(columns={"project_type": "Type", "project_count": "Projects", "total_credits": "Est. Credits"})
            st.bar_chart(df.set_index("Type")["Projects"])

    by_registry = analytics.get("by_registry", [])
    if by_registry:
        st.divider()
        st.subheader("By Registry")
        cols = st.columns(len(by_registry))
        for i, reg in enumerate(by_registry):
            with cols[i]:
                label = "Verra VCS" if reg["registry"] == "verra" else "Gold Standard"
                st.metric(label, f"{reg['project_count']:,} projects")


def _render_country_explorer(analytics):
    countries = analytics.get("by_country", [])
    if not countries:
        st.info("No country data available.")
        return

    country_names = [c["country"] for c in countries]
    selected = st.selectbox("Select a country", country_names,
                            key="country_select",
                            help="Choose a country to explore its carbon projects")

    if selected:
        detail = _fetch(f"/admin/projects/country/{selected}")
        if not detail:
            st.warning("Could not load country details.")
            return

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Projects", f"{detail['total']}")
        with col2:
            total_credits = sum(
                (p.get("estimated_annual_credits") or 0) for p in detail.get("projects", [])
            )
            st.metric("Est. Annual Credits", f"{total_credits:,}")
        with col3:
            st.metric("Developers", f"{len(detail.get('developers', []))}")

        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("Methodologies")
            meths = detail.get("methodologies", [])
            if meths:
                import pandas as pd
                df = pd.DataFrame(meths)
                df = df.rename(columns={"methodology": "Methodology", "count": "Projects", "credits": "Est. Credits"})
                st.dataframe(df, width="stretch", hide_index=True)

        with col_right:
            st.subheader("Top Developers")
            devs = detail.get("developers", [])
            if devs:
                import pandas as pd
                df = pd.DataFrame(devs)
                df = df.rename(columns={"proponent": "Developer", "count": "Projects"})
                st.dataframe(df, width="stretch", hide_index=True)

        statuses = detail.get("statuses", [])
        if statuses:
            st.subheader("Status Breakdown")
            import pandas as pd
            df = pd.DataFrame(statuses)
            df = df.rename(columns={"status": "Status", "count": "Projects"})
            st.bar_chart(df.set_index("Status")["Projects"])

        st.subheader(f"All Projects in {selected}")
        projects = detail.get("projects", [])
        if projects:
            import pandas as pd
            df = pd.DataFrame(projects)
            display_cols = ["name", "status", "methodology", "proponent", "estimated_annual_credits", "registry"]
            display_cols = [c for c in display_cols if c in df.columns]
            df_display = df[display_cols].copy()
            df_display.columns = [c.replace("_", " ").title() for c in display_cols]
            st.dataframe(df_display, width="stretch", hide_index=True)


def _render_methodology_analysis():
    st.subheader("Top Methodologies")
    meths = _fetch("/admin/projects/methodologies?limit=30")
    if not meths:
        st.info("No methodology data available.")
        return

    import pandas as pd
    df = pd.DataFrame(meths)
    df = df.rename(columns={
        "methodology": "Methodology",
        "project_count": "Projects",
        "total_credits": "Est. Annual Credits"
    })

    st.dataframe(df, width="stretch", hide_index=True)

    st.subheader("Projects per Methodology")
    top_10 = df.head(15)
    st.bar_chart(top_10.set_index("Methodology")["Projects"])

    st.subheader("Credits per Methodology")
    top_credits = df.sort_values("Est. Annual Credits", ascending=False).head(15)
    st.bar_chart(top_credits.set_index("Methodology")["Est. Annual Credits"])


def _render_project_browser():
    col1, col2, col3 = st.columns(3)
    with col1:
        search_q = st.text_input("Search projects", key="proj_search",
                                  placeholder="Project name, country, methodology...")
    with col2:
        registry_filter = st.selectbox("Registry", ["All", "verra", "goldstandard"],
                                        key="proj_registry")
    with col3:
        status_filter = st.selectbox("Status", ["All", "Registered", "Under development",
                                                  "Under validation", "Late to verify"],
                                      key="proj_status")

    if search_q:
        projects = _fetch(f"/admin/projects/search?q={search_q}&limit=100")
    else:
        params = []
        if registry_filter != "All":
            params.append(f"registry={registry_filter}")
        if status_filter != "All":
            params.append(f"status={status_filter}")
        params.append("limit=100")
        query_str = "&".join(params)
        projects = _fetch(f"/admin/projects?{query_str}")

    if not projects:
        st.info("No projects found matching your criteria.")
        return

    st.write(f"Showing {len(projects)} projects")

    import pandas as pd
    df = pd.DataFrame(projects)
    display_cols = ["registry", "registry_id", "name", "country", "status", "methodology",
                    "project_type", "proponent", "estimated_annual_credits"]
    display_cols = [c for c in display_cols if c in df.columns]
    df_display = df[display_cols].copy()
    df_display.columns = [c.replace("_", " ").title() for c in display_cols]
    st.dataframe(df_display, width="stretch", hide_index=True)


def _render_sync_controls(summary):
    st.subheader("Project Data Sync")

    sync_status = _fetch("/admin/sync-projects/status")

    st.write(f"Total projects in database: {summary.get('total_projects', 0):,}")
    st.write(f"Countries covered: {summary.get('total_countries', 0)}")

    if sync_status and sync_status.get("running"):
        st.info("A sync is currently running in the background. Refresh this page to check progress.")
        current_count = sync_status.get("total_projects_in_db", 0)
        st.write(f"Current project count: {current_count:,}")
    else:
        last_result = sync_status.get("last_result") if sync_status else None
        if last_result and not last_result.get("error"):
            verra = last_result.get("verra", {})
            gs = last_result.get("goldstandard", {})
            st.write(
                f"Last sync: Verra {verra.get('synced', 0):,} projects, "
                f"Gold Standard {gs.get('synced', 0):,} projects"
            )

    st.divider()

    if st.button("Sync All Projects", key="sync_all_btn", type="primary",
                  help="Fetch latest project data from Verra and Gold Standard registries"):
        result = _fetch("/admin/sync-projects", method="POST")
        if result:
            status = result.get("status", "")
            if status == "started":
                st.success("Sync started in the background. Refresh this page in a few minutes to see results.")
            elif status == "already_running":
                st.warning("A sync is already running. Please wait for it to finish.")
            else:
                verra = result.get("verra", {})
                gs = result.get("goldstandard", {})
                st.success(
                    f"Sync complete. "
                    f"Verra: {verra.get('synced', 0):,} projects. "
                    f"Gold Standard: {gs.get('synced', 0):,} projects."
                )
                time.sleep(1)
                st.rerun()


@st.cache_data(ttl=300)
def _load_methodologies(standard=None):
    params = f"?limit=300"
    if standard:
        std_map = {"GoldStandard": "GoldStandard", "Verra": "Verra"}
        mapped = std_map.get(standard)
        if mapped:
            params += f"&standard={mapped}"
    result = _fetch(f"/projects/methodologies{params}")
    return result or []


PRIORITY_METHODOLOGIES = {
    "GS-TPDDTEC": "GS TPDDTEC v4.0 - Technologies and Practices to Displace Decentralized Thermal Energy Consumption",
    "VM0050": "VCS VM0050 v1.0 - Energy Efficiency and Fuel-Switch Measures in Cookstoves",
    "ACM0002": "CDM ACM0002 - Grid-Connected Electricity Generation from Renewable Sources",
    "AMS-I.D.": "CDM AMS-I.D. - Grid-Connected Renewable Electricity Generation (small-scale)",
}

def _render_country_selector(key_prefix: str, current_value: str = "") -> str:
    display_value = TOOL33_TO_PYCOUNTRY.get(current_value, current_value)
    search = st.text_input(
        "Country (type to search)",
        value=display_value,
        key=f"{key_prefix}_country_search",
        placeholder="Type to filter countries...",
    )
    filtered = [c for c in ALL_COUNTRIES if search.strip().lower() in c.lower()] if search.strip() else ALL_COUNTRIES
    if not filtered:
        filtered = ALL_COUNTRIES
    try:
        idx = filtered.index(search.strip()) if search.strip() in filtered else 0
    except ValueError:
        idx = 0
    selected = st.selectbox(
        "Country",
        filtered,
        index=idx,
        key=f"{key_prefix}_country_select",
        label_visibility="collapsed",
    )
    return selected


def _render_location_section(key_prefix: str, project: dict = None) -> dict:
    project = project or {}
    country = _render_country_selector(key_prefix, project.get("country", "") or "")
    fnrb = get_fnrb_for_country(country)
    if fnrb is not None:
        st.caption(f"CDM TOOL33 v3 default fNRB for {country}: {fnrb:.0%}")

    region = st.text_input(
        "Region / Province",
        value=project.get("region", "") or "",
        key=f"{key_prefix}_region",
        placeholder="e.g., Ashanti Region, Northern Region",
    )

    # Seed geojson from the project's database record on first load (so polygon
    # survives app restarts without needing a fresh "Look up" click each session)
    _geojson_key = f"{key_prefix}_geojson"
    if _geojson_key not in st.session_state:
        _saved_bj = project.get("boundary_geojson")
        if _saved_bj:
            import json as _bj_json
            try:
                st.session_state[_geojson_key] = _bj_json.loads(_saved_bj) if isinstance(_saved_bj, str) else _saved_bj
            except Exception:
                pass

    # Consume any pending geocoded values BEFORE rendering coordinate widgets
    _pending_lat = f"{key_prefix}_pending_lat"
    _pending_lon = f"{key_prefix}_pending_lon"
    _pending_geojson = f"{key_prefix}_pending_geojson"
    _geo_lat = st.session_state.pop(_pending_lat, None)
    _geo_lon = st.session_state.pop(_pending_lon, None)
    _geo_geojson = st.session_state.pop(_pending_geojson, None)
    if _geo_lat is not None:
        st.session_state[f"{key_prefix}_lat"] = _geo_lat
    if _geo_lon is not None:
        st.session_state[f"{key_prefix}_lon"] = _geo_lon
    if _geo_geojson is not None:
        st.session_state[f"{key_prefix}_geojson"] = _geo_geojson

    gc1, gc2, gc3 = st.columns([2, 2, 1])
    lat_val = project.get("latitude")
    lon_val = project.get("longitude")
    with gc1:
        lat = st.number_input(
            "Latitude",
            value=float(lat_val) if lat_val is not None else None,
            min_value=-90.0, max_value=90.0,
            format="%.6f",
            key=f"{key_prefix}_lat",
            placeholder="e.g., 6.6885",
        )
    with gc2:
        lon = st.number_input(
            "Longitude",
            value=float(lon_val) if lon_val is not None else None,
            min_value=-180.0, max_value=180.0,
            format="%.6f",
            key=f"{key_prefix}_lon",
            placeholder="e.g., -1.6244",
        )
    with gc3:
        st.write("")
        st.write("")
        if st.button("Look up", key=f"{key_prefix}_geocode",
                     help="Auto-fill coordinates and boundary from region name"):
            if region:
                geo = geocode_location(region, country)
                if geo:
                    st.session_state[_pending_lat] = geo["latitude"]
                    st.session_state[_pending_lon] = geo["longitude"]
                    if geo.get("geojson"):
                        st.session_state[_pending_geojson] = geo["geojson"]
                    else:
                        st.session_state.pop(f"{key_prefix}_geojson", None)
                    st.rerun()
                else:
                    st.warning("Could not auto-fill coordinates. Enter them manually.")
            else:
                st.info("Enter a region / province first.")

    if lat is not None and lon is not None:
        try:
            import folium
            from streamlit_folium import st_folium
            popup_text = region or country or "Project location"
            stored_geojson = st.session_state.get(f"{key_prefix}_geojson")
            m = folium.Map(location=[lat, lon], zoom_start=7, tiles="OpenStreetMap")
            if stored_geojson:
                folium.GeoJson(
                    {"type": "Feature", "geometry": stored_geojson, "properties": {"name": popup_text}},
                    name=popup_text,
                    style_function=lambda _: {
                        "fillColor": "#2d6a4f",
                        "color": "#1b4332",
                        "weight": 2,
                        "fillOpacity": 0.15,
                    },
                    tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Location:"]),
                ).add_to(m)
                folium.Marker(
                    [lat, lon],
                    popup=popup_text,
                    tooltip=popup_text,
                    icon=folium.Icon(color="green", icon="leaf"),
                ).add_to(m)
                m.fit_bounds(m.get_bounds())
            else:
                folium.Marker(
                    [lat, lon],
                    popup=popup_text,
                    tooltip=popup_text,
                    icon=folium.Icon(color="green", icon="leaf"),
                ).add_to(m)
            st_folium(m, height=280, use_container_width=True, returned_objects=[])
        except Exception:
            st.caption(f"Map preview unavailable. Coordinates: {lat:.4f}, {lon:.4f}")

    import json as _ret_json
    _current_geojson = st.session_state.get(f"{key_prefix}_geojson")
    _geojson_str = _ret_json.dumps(_current_geojson) if _current_geojson and not isinstance(_current_geojson, str) else _current_geojson
    return {
        "country": country,
        "location_name": None,
        "region": region or None,
        "district": None,
        "latitude": lat,
        "longitude": lon,
        "geojson": _current_geojson,
        "boundary_geojson": _geojson_str,
    }


def _methodology_selector(key_prefix, standard=None, current_value=None):
    meths = _load_methodologies()

    priority_meths = [m for m in meths if m["code"] in PRIORITY_METHODOLOGIES]
    if standard and standard != "CDM":
        if standard == "GoldStandard":
            priority_meths = [m for m in priority_meths if m.get("standard") in ("GoldStandard", "CDM")]
        elif standard == "Verra":
            priority_meths = [m for m in priority_meths if m.get("standard") in ("Verra", "CDM")]

    shown = list(priority_meths)
    shown_codes = {m["code"] for m in shown}

    if current_value and current_value not in shown_codes:
        current_meth = next((m for m in meths if m["code"] == current_value), None)
        if current_meth:
            meth_std = current_meth.get("standard", "")
            compatible = True
            if standard == "GoldStandard" and meth_std not in ("GoldStandard", "CDM"):
                compatible = False
            elif standard == "Verra" and meth_std not in ("Verra", "CDM"):
                compatible = False
            if compatible:
                shown.append(current_meth)
                shown_codes.add(current_value)

    options = ["(none)"] + [m["code"] for m in shown]
    labels = {
        "(none)": "-- Select methodology --",
    }
    std_short = {"CDM": "CDM", "Verra": "VCS", "GoldStandard": "GS"}
    for m in shown:
        code = m["code"]
        if code in PRIORITY_METHODOLOGIES:
            labels[code] = PRIORITY_METHODOLOGIES[code]
        else:
            name = (m.get("name") or "").strip()
            version = (m.get("version") or "").strip()
            ms = std_short.get(m.get("standard", ""), "")
            label = f"[{ms}] {code}" if ms else code
            if version:
                label += f" v{version}"
            if name:
                label += f" - {name[:60]}"
            labels[code] = label

    default_idx = 0
    if current_value and current_value in options:
        default_idx = options.index(current_value)

    st.caption("Supported methodologies (AI-trained with full parameter and equation extraction)")
    selected = st.selectbox(
        "Methodology",
        options,
        index=default_idx,
        format_func=lambda x: labels.get(x, x),
        key=f"{key_prefix}_meth_select",
    )
    if selected and selected != "(none)" and selected not in PRIORITY_METHODOLOGIES:
        st.info("This methodology is not yet fully AI-trained. The AI writer and reviewer will have limited knowledge of its specific parameters, equations, and requirements. Priority methodologies have deeper AI support.")
    return selected if selected != "(none)" else None


STANDARD_OPTIONS = ["GoldStandard", "Verra"]
DOC_TYPES_FOR_STANDARD = {
    "GoldStandard": {"pdd": "PDD", "mr": "Monitoring Report", "poa_dd": "PoA-DD", "vpa_dd": "VPA-DD"},
    "Verra": {"pdd": "Project Description (VCS-PD)", "mr": "Monitoring Report (VCS-MR)", "valver": "Validation/Verification Report"},
}
PROJECT_DOC_TYPES = {
    "pdd": "Project Description (PDD)",
    "mr": "Monitoring Report (MR)",
    "valver": "Validation/Verification Report",
    "poa_dd": "PoA-DD",
    "vpa_dd": "VPA-DD",
    "reference": "Reference Document",
    "research": "Research / Study",
    "field_data": "Field Data / Test Results",
    "template": "Template",
    "other": "Other",
}
PROJECT_TYPE_INFO = {
    "standalone_pdd": {
        "label": "Standalone PDD",
        "short": "PDD",
        "badge_class": "badge-pdd",
        "description": "Write a new Project Design Document for a single project activity",
        "default_doc_type": "pdd",
        "standards": ["GoldStandard", "Verra"],
    },
    "poa_programme": {
        "label": "Programme of Activities (PoA-DD)",
        "short": "PoA-DD",
        "badge_class": "badge-poa",
        "description": "Create a PoA-DD programme envelope. You can add VPA-DDs under it later.",
        "default_doc_type": "poa_dd",
        "standards": ["GoldStandard"],
    },
    "vpa_component": {
        "label": "VPA Design Document",
        "short": "VPA-DD",
        "badge_class": "badge-vpa",
        "description": "Write a VPA-DD component linked to an existing PoA-DD programme",
        "default_doc_type": "vpa_dd",
        "standards": ["GoldStandard"],
        "needs_parent": True,
        "parent_type": "poa_programme",
    },
    "monitoring_report": {
        "label": "Monitoring Report",
        "short": "MR",
        "badge_class": "badge-mr",
        "description": "Write a Monitoring Report for an existing project",
        "default_doc_type": "mr",
        "standards": ["GoldStandard", "Verra"],
        "needs_parent": True,
        "parent_type": None,
    },
    "valver_report": {
        "label": "Validation / Verification Report",
        "short": "ValVer",
        "badge_class": "badge-valver",
        "description": "Write a Validation or Verification Report",
        "default_doc_type": "valver",
        "standards": ["Verra"],
    },
}
STATUS_LABELS = {
    "draft": "Draft",
    "in_progress": "In Progress",
    "under_review": "Under Review",
    "submitted": "Submitted",
    "registered": "Registered",
    "archived": "Archived",
}
STATUS_COLORS = {
    "draft": "gray",
    "in_progress": "blue",
    "under_review": "orange",
    "submitted": "violet",
    "registered": "green",
    "archived": "red",
}


_STAT_ICONS = {
    "projects": '<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>',
    "active":   '<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
    "drafts":   '<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>',
    "docs":     '<svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 13h4"/><path d="M10 17h4"/></svg>',
}


def _stat_card(icon_key, value, label, desc=""):
    icon = _STAT_ICONS.get(icon_key, "")
    desc_html = f'<div class="stat-card-desc">{desc}</div>' if desc else ""
    return (
        f'<div class="stat-card">'
        f'  <div class="stat-card-icon">{icon}</div>'
        f'  <div class="stat-card-value">{value}</div>'
        f'  <div class="stat-card-label">{label}</div>'
        f'  {desc_html}'
        f'</div>'
    )


def _render_home():
    all_projects = _fetch("/projects") or []
    active_count = sum(1 for p in all_projects if p.get("status") in ("in_progress", "under_review"))
    draft_count  = sum(1 for p in all_projects if p.get("status") == "draft")
    total_docs   = sum(p.get("doc_count", 0) for p in all_projects)

    st.markdown("""
    <div class="ws-hero">
        <div class="ws-hero-text">
            <h1>Workspace</h1>
            <p>Manage carbon projects, track progress, and explore market intelligence</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    wc1, wc2, wc3, wc4 = st.columns(4)
    with wc1:
        st.markdown(_stat_card("projects", len(all_projects), "Total Projects", "Across all standards"), unsafe_allow_html=True)
    with wc2:
        st.markdown(_stat_card("active", active_count, "Active", "In progress or review"), unsafe_allow_html=True)
    with wc3:
        st.markdown(_stat_card("drafts", draft_count, "Drafts", "Pending completion"), unsafe_allow_html=True)
    with wc4:
        st.markdown(_stat_card("docs", total_docs, "Documents", "Across all projects"), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:0.5rem;'></div>", unsafe_allow_html=True)
    home_tabs = st.tabs(["Projects", "Carbon Intelligence"])
    with home_tabs[0]:
        _render_project_list()
    with home_tabs[1]:
        render_intelligence()


def _render_project_list():

    projects = _fetch("/projects") or []

    list_col_left, list_col_actions = st.columns([3, 1.6])
    with list_col_left:
        pass
    with list_col_actions:
        btn_a, btn_b = st.columns([1, 1.15])
        with btn_a:
            if st.button("Import", key="import_doc_btn", use_container_width=True):
                st.session_state["show_new_project"] = True
                st.session_state["wizard_path"] = "import"
                st.session_state.pop("new_proj_step", None)
        with btn_b:
            if st.button("New Project", key="new_proj_btn", type="primary", use_container_width=True):
                st.session_state["show_new_project"] = True
                st.session_state.pop("wizard_path", None)
                st.session_state.pop("new_proj_step", None)

    if st.session_state.get("show_new_project"):
        _render_new_project_wizard(projects)
        return

    if not projects:
        st.markdown("""
        <div class="empty-state-card">
            <div class="empty-state-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" fill="none"
                     stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/>
                    <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
                    <path d="M10 13h4"/><path d="M10 17h4"/>
                </svg>
            </div>
            <h3>No projects yet</h3>
            <p>Create your first carbon project to start drafting PDDs, Monitoring Reports,
               and other documents with AI assistance.</p>
        </div>
        """, unsafe_allow_html=True)
        col_e1, col_e2, col_e3 = st.columns([1, 1.5, 1])
        with col_e2:
            if st.button("Create your first project", key="empty_new_proj_btn", type="primary", use_container_width=True):
                st.session_state["show_new_project"] = True
                st.session_state.pop("wizard_path", None)
                st.session_state.pop("new_proj_step", None)
                st.rerun()
            st.markdown('<div style="text-align:center;margin:0.4rem 0;font-size:0.78rem;color:var(--text-tertiary);">or</div>', unsafe_allow_html=True)
            if st.button("Import an existing document", key="empty_import_btn", use_container_width=True):
                st.session_state["show_new_project"] = True
                st.session_state["wizard_path"] = "import"
                st.session_state.pop("new_proj_step", None)
                st.rerun()
        return

    st.markdown(
        f'<div class="projects-section-header">'
        f'  <span class="projects-section-title">{len(projects)} project{"s" if len(projects) != 1 else ""}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    proj_by_parent = {}
    top_level = []
    for proj in projects:
        parent_id = proj.get("parent_project_id")
        if parent_id:
            proj_by_parent.setdefault(parent_id, []).append(proj)
        else:
            top_level.append(proj)

    for proj in top_level:
        children = proj_by_parent.get(proj["id"], [])
        _render_project_card(proj, child_count=len(children))
        if children:
            for child in children:
                _render_project_card(child, indent=True)

    orphaned_parents = set(proj_by_parent.keys()) - {p["id"] for p in top_level}
    for parent_id in orphaned_parents:
        for child in proj_by_parent[parent_id]:
            _render_project_card(child)


def _render_project_card(proj, indent=False, child_count=0):
    pid = proj["id"]
    status = proj.get("status", "draft")
    status_label = STATUS_LABELS.get(status, status)
    doc_count = proj.get("doc_count", 0)
    project_type = proj.get("project_type", "standalone_pdd")
    type_info = PROJECT_TYPE_INFO.get(project_type, PROJECT_TYPE_INFO["standalone_pdd"])
    badge_class = type_info.get("badge_class", "badge-pdd")

    std_raw = proj.get("standard", "")
    std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(std_raw, std_raw)

    meta_parts = []
    if std_display:
        meta_parts.append(f'<span class="project-card-meta-item">{SVG_ICONS.get("globe", "")} {std_display}</span>')
    if proj.get("methodology"):
        meta_parts.append(f'<span class="project-card-meta-item">{SVG_ICONS.get("methodology", "")} {proj["methodology"]}</span>')
    if proj.get("country"):
        meta_parts.append(f'<span class="project-card-meta-item">{proj["country"]}</span>')
    meta_html = '<span class="pc-meta-sep">&bull;</span>'.join(meta_parts)

    status_class = f"status-{status.replace('_', '')}"

    child_pill = ""
    if child_count > 0:
        child_pill = f'<span class="pc-child-pill">{child_count} VPA{"s" if child_count != 1 else ""}</span>'

    doc_label = f'{doc_count} document{"s" if doc_count != 1 else ""}'
    indent_style = 'style="margin-left:24px;"' if indent else ""

    with st.container(border=True):
        col_main, col_action = st.columns([5.5, 0.9])
        with col_main:
            st.markdown(
                f'<div class="pc-inner" {indent_style}>'
                f'  <div class="pc-header-row">'
                f'    <span class="project-type-badge {badge_class}">{type_info["short"]}</span>'
                f'    <span class="pc-title">{proj["name"]}</span>'
                f'    {child_pill}'
                f'  </div>'
                f'  <div class="pc-meta-row">{meta_html}</div>'
                f'  <div class="pc-footer-row">'
                f'    <span class="status-badge {status_class}">{status_label}</span>'
                f'    <span class="pc-doc-count">{doc_label}</span>'
                f'  </div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_action:
            st.markdown('<div style="padding-top:0.6rem;"></div>', unsafe_allow_html=True)
            if st.button("Open", key=f"open_proj_{pid}", type="primary", use_container_width=True):
                st.session_state.selected_project_id = pid
                st.rerun()


def _render_import_document_wizard(existing_projects, step_key):
    st.markdown("**Import: Upload an existing document**")
    st.caption("Upload a PDD, PoA-DD, Monitoring Report, or similar carbon project document. The system will extract the key project details and pre-fill the wizard for you.")

    import_key = "import_extracted"
    uploaded = st.file_uploader(
        "Choose file (PDF or DOCX)",
        type=["pdf", "docx"],
        key="import_file_upload",
    )

    if uploaded is not None and import_key not in st.session_state:
        with st.spinner("Extracting project details from document..."):
            try:
                import requests as _req
                resp = _req.post(
                    "http://localhost:3000/projects/import-document",
                    files={"file": (uploaded.name, uploaded.getvalue(), uploaded.type)},
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state[import_key] = data.get("extracted", {})
                    st.session_state["import_text_len"] = data.get("text_length", 0)
                else:
                    st.error("The document could not be parsed. Try a different file.")
            except Exception as e:
                st.error(f"Extraction failed: {e}")

    extracted = st.session_state.get(import_key)

    if extracted:
        st.success(f"Document parsed ({st.session_state.get('import_text_len', 0):,} characters extracted). Review the detected fields below and edit any that are wrong.")
        with st.container(border=True):
            col_a, col_b = st.columns(2)
            with col_a:
                imp_name = st.text_input("Project name", value=extracted.get("project_name") or "", key="imp_name")
                imp_country = st.text_input("Country", value=extracted.get("country") or "", key="imp_country")
                imp_std_raw = extracted.get("standard") or "GoldStandard"
                imp_std_options = ["GoldStandard", "Verra"]
                imp_std_idx = imp_std_options.index(imp_std_raw) if imp_std_raw in imp_std_options else 0
                imp_standard = st.selectbox(
                    "Standard",
                    imp_std_options,
                    index=imp_std_idx,
                    format_func=lambda x: {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(x, x),
                    key="imp_standard",
                )
            with col_b:
                imp_methodology = st.text_input("Methodology", value=extracted.get("methodology") or "", key="imp_methodology")
                imp_type_raw = extracted.get("project_type") or "standalone_pdd"
                imp_type_options = list(PROJECT_TYPE_INFO.keys())
                imp_type_labels = [PROJECT_TYPE_INFO[k]["label"] for k in imp_type_options]
                imp_type_idx = imp_type_options.index(imp_type_raw) if imp_type_raw in imp_type_options else 0
                imp_type_label = st.selectbox("Project type", imp_type_labels, index=imp_type_idx, key="imp_type_label")
                imp_proj_type = imp_type_options[imp_type_labels.index(imp_type_label)]
                imp_desc = st.text_area("Description", value=extracted.get("description") or "", key="imp_desc", height=68)

        c_back, c_spacer, c_next = st.columns([1, 2, 1])
        with c_back:
            if st.button("Back", key="imp_back"):
                st.session_state.pop("wizard_path", None)
                st.session_state.pop(import_key, None)
                st.session_state.pop("import_text_len", None)
                st.rerun()
        with c_next:
            if st.button("Use these details", key="imp_continue", type="primary"):
                if not imp_name:
                    st.warning("Please provide a project name.")
                else:
                    st.session_state["new_proj_type"] = imp_proj_type
                    st.session_state["wizard_name_saved"] = imp_name
                    st.session_state["wizard_standard_saved"] = imp_standard
                    st.session_state["wizard_country_saved"] = imp_country
                    st.session_state["wizard_desc_saved"] = imp_desc
                    st.session_state["wizard_methodology_step2"] = imp_methodology
                    mon_start = extracted.get("monitoring_period_start")
                    mon_end = extracted.get("monitoring_period_end")
                    if mon_start:
                        st.session_state["wizard_mon_start_saved"] = mon_start
                    if mon_end:
                        st.session_state["wizard_mon_end_saved"] = mon_end
                    # Clear widget keys so seeds below take effect on first render
                    for _wk in ["wizard_name", "wizard_desc", "wizard_standard"]:
                        st.session_state.pop(_wk, None)
                    st.session_state.pop(import_key, None)
                    st.session_state.pop("import_text_len", None)
                    st.session_state[step_key] = 2
                    st.rerun()
    else:
        if st.button("Back", key="imp_back_empty"):
            st.session_state.pop("wizard_path", None)
            st.session_state.pop(import_key, None)
            st.rerun()


def _render_new_project_wizard(existing_projects):
    st.markdown("### Create New Project")

    if st.button("Cancel", key="cancel_new_proj"):
        st.session_state["show_new_project"] = False
        st.session_state.pop("new_proj_step", None)
        st.session_state.pop("new_proj_type", None)
        st.session_state.pop("wizard_path", None)
        for _k in ["wizard_name_saved", "wizard_standard_saved", "wizard_country_saved",
                   "wizard_desc_saved", "wizard_parent_saved", "wizard_loc_saved",
                   "wizard_mon_start_saved", "wizard_mon_end_saved", "import_extracted"]:
            st.session_state.pop(_k, None)
        st.rerun()

    step_key = "new_proj_step"
    if step_key not in st.session_state:
        st.session_state[step_key] = 1

    step = st.session_state[step_key]

    if step == 1:
        wizard_path = st.session_state.get("wizard_path")

        if wizard_path is None:
            st.markdown("**Step 1: What would you like to do?**")
            p1, p2, p3 = st.columns(3)
            with p1:
                with st.container(border=True):
                    st.markdown("**Start a new project**")
                    st.caption("Register a Standalone project or Programme of Activities from scratch.")
                    if st.button("New project", key="path_new_proj", use_container_width=True, type="primary"):
                        st.session_state["wizard_path"] = "new"
                        st.rerun()
            with p2:
                with st.container(border=True):
                    st.markdown("**Add to existing project**")
                    st.caption("Add a Monitoring Report, VPA-DD, or Validation Report to a project you already have.")
                    if st.button("Add to existing", key="path_add_existing", use_container_width=True):
                        st.session_state["wizard_path"] = "add_existing"
                        st.rerun()
            with p3:
                with st.container(border=True):
                    st.markdown("**Import existing document**")
                    st.caption("Upload a PDD, Monitoring Report, or PoA-DD — the system extracts the project details for you.")
                    if st.button("Import document", key="path_import_doc", use_container_width=True):
                        st.session_state["wizard_path"] = "import"
                        st.rerun()

        elif wizard_path == "new":
            st.markdown("**Step 1: What type of project?**")
            NEW_TYPES = {k: v for k, v in PROJECT_TYPE_INFO.items() if k in ("standalone_pdd", "poa_programme")}
            type_cols = st.columns(len(NEW_TYPES))
            for i, (ptype, info) in enumerate(NEW_TYPES.items()):
                with type_cols[i]:
                    with st.container(border=True):
                        badge_class = info.get("badge_class", "badge-pdd")
                        st.markdown(
                            f"<span class='project-type-badge {badge_class}'>{info['short']}</span>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"**{info['label']}**")
                        st.caption(info["description"])
                        standards_str = ", ".join(
                            {"GoldStandard": "GS", "Verra": "Verra"}.get(s, s) for s in info["standards"]
                        )
                        st.caption(f"Standards: {standards_str}")
                        if st.button("Select", key=f"select_type_{ptype}", use_container_width=True):
                            st.session_state["new_proj_type"] = ptype
                            st.session_state[step_key] = 2
                            st.rerun()
            if st.button("Back", key="path_back_new"):
                st.session_state.pop("wizard_path", None)
                st.rerun()

        elif wizard_path == "add_existing":
            st.markdown("**Step 1: Add to existing project**")
            parents = [p for p in existing_projects if p.get("project_type") in ("standalone_pdd", "poa_programme", "vpa_component")]
            if not parents:
                st.warning("No existing projects found. Create a project first.")
                if st.button("Back", key="path_back_existing_empty"):
                    st.session_state.pop("wizard_path", None)
                    st.rerun()
            else:
                parent_opts = {
                    p["id"]: f"{p['name']} ({PROJECT_TYPE_INFO.get(p.get('project_type', ''), {}).get('short', p.get('project_type', ''))})"
                    for p in parents
                }
                chosen_parent_id = st.selectbox(
                    "Select the parent project",
                    list(parent_opts.keys()),
                    format_func=lambda x: parent_opts.get(x, str(x)),
                    key="wizard_add_parent_pick",
                )
                chosen_parent = next((p for p in parents if p["id"] == chosen_parent_id), None)

                if chosen_parent and chosen_parent.get("project_type") == "poa_programme":
                    avail_child_types = {"vpa_component": PROJECT_TYPE_INFO["vpa_component"]}
                else:
                    avail_child_types = {
                        "monitoring_report": PROJECT_TYPE_INFO["monitoring_report"],
                        "valver_report": PROJECT_TYPE_INFO["valver_report"],
                    }

                child_type_keys = list(avail_child_types.keys())
                child_type_labels = [avail_child_types[k]["label"] for k in child_type_keys]
                chosen_child_label = st.radio(
                    "What do you want to add?",
                    child_type_labels,
                    key="wizard_add_child_type",
                    horizontal=True,
                )
                chosen_child_type = child_type_keys[child_type_labels.index(chosen_child_label)]
                st.caption(avail_child_types[chosen_child_type]["description"])

                c_back, c_next = st.columns([1, 3])
                with c_back:
                    if st.button("Back", key="path_back_existing"):
                        st.session_state.pop("wizard_path", None)
                        st.rerun()
                with c_next:
                    if st.button("Continue", key="path_continue_existing", type="primary"):
                        st.session_state["new_proj_type"] = chosen_child_type
                        st.session_state["wizard_parent_saved"] = chosen_parent_id
                        if chosen_parent:
                            st.session_state["wizard_standard_saved"] = chosen_parent.get("standard", "GoldStandard")
                            st.session_state["wizard_country_saved"] = chosen_parent.get("country", "")
                        st.session_state[step_key] = 2
                        st.rerun()

        elif wizard_path == "import":
            _render_import_document_wizard(existing_projects, step_key)

    elif step == 2:
        selected_type = st.session_state.get("new_proj_type", "standalone_pdd")
        type_info = PROJECT_TYPE_INFO[selected_type]
        badge_class = type_info.get("badge_class", "badge-pdd")
        wizard_path = st.session_state.get("wizard_path")
        st.markdown(
            f"<span class='project-type-badge {badge_class}'>{type_info['short']}</span> "
            f"**{type_info['label']}**",
            unsafe_allow_html=True,
        )

        # When coming from "add_existing" path, standard is pre-set from parent
        prefilled_standard = st.session_state.get("wizard_standard_saved")
        prefilled_parent_id = st.session_state.get("wizard_parent_saved")
        parent_from_step1 = wizard_path == "add_existing" and prefilled_parent_id is not None

        available_standards = type_info.get("standards", STANDARD_OPTIONS)
        if parent_from_step1 and prefilled_standard:
            new_standard = prefilled_standard
            std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(new_standard, new_standard)
            st.info(f"Standard: {std_display} (inherited from parent project)")
        elif len(available_standards) == 1:
            new_standard = available_standards[0]
            std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(new_standard, new_standard)
            st.info(f"Standard: {std_display}")
        else:
            new_standard = st.selectbox("Standard", available_standards, key="wizard_standard",
                                         format_func=lambda x: {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(x, x))

        needs_parent = type_info.get("needs_parent", False)
        parent_id = None
        if needs_parent:
            if parent_from_step1:
                # Parent was selected in step 1 — show as read-only info
                parent_proj = next((p for p in existing_projects if p["id"] == prefilled_parent_id), None)
                parent_display = parent_proj["name"] if parent_proj else f"Project #{prefilled_parent_id}"
                st.info(f"Linked to: {parent_display}")
                parent_id = prefilled_parent_id
            else:
                parent_filter_type = type_info.get("parent_type")
                if parent_filter_type:
                    linkable = [p for p in existing_projects
                                if p.get("project_type") == parent_filter_type
                                and p.get("standard") == new_standard]
                    parent_label = "Select parent PoA-DD programme"
                else:
                    linkable = [p for p in existing_projects
                                if p.get("project_type") in ("standalone_pdd", "vpa_component", "poa_programme")
                                and p.get("standard") == new_standard]
                    parent_label = "Link to existing project (optional)"

                if linkable:
                    parent_options = {p["id"]: f"{p['name']} ({p.get('methodology', 'N/A')})" for p in linkable}
                    parent_id = st.selectbox(
                        parent_label,
                        [None] + list(parent_options.keys()),
                        format_func=lambda x: parent_options[x] if x else "(none)",
                        key="wizard_parent",
                    )
                else:
                    if parent_filter_type == "poa_programme":
                        st.warning("No PoA-DD programmes found. Create a PoA-DD first, or proceed without linking.")
                    else:
                        st.info("No existing projects to link. You can proceed without linking.")

        # Pre-fill name from import path (canonical pattern: seed session state before rendering widget)
        if "wizard_name" not in st.session_state and st.session_state.get("wizard_name_saved"):
            st.session_state["wizard_name"] = st.session_state["wizard_name_saved"]
        new_name = st.text_input("Project name", key="wizard_name",
                                  placeholder="e.g., Ghana Improved Cookstoves")
        if "wizard_desc" not in st.session_state and st.session_state.get("wizard_desc_saved"):
            st.session_state["wizard_desc"] = st.session_state["wizard_desc_saved"]
        new_desc = st.text_area("Description (optional)", key="wizard_desc",
                                 placeholder="Brief description...", height=68)
        st.markdown("---")
        loc_data = _render_location_section("wizard", {})
        new_country = loc_data["country"]

        monitoring_start = None
        monitoring_end = None
        if selected_type == "monitoring_report":
            st.markdown("**Monitoring Period**")
            mc1, mc2 = st.columns(2)
            with mc1:
                monitoring_start = st.date_input("Period start", key="wizard_mon_start", value=None, format="YYYY-MM-DD")
            with mc2:
                monitoring_end = st.date_input("Period end", key="wizard_mon_end", value=None, format="YYYY-MM-DD")
            if monitoring_start and monitoring_end and monitoring_end <= monitoring_start:
                st.warning("Monitoring period end date must be after the start date.")

        supports_cookstove_wizard = selected_type in (
            "standalone_pdd", "poa_programme", "vpa_component", "monitoring_report"
        ) and new_standard in ("GoldStandard", "Verra")

        if supports_cookstove_wizard:
            st.caption("The methodology will be automatically derived in the next step based on activity type and fuel choices.")
        else:
            new_methodology_step2 = _methodology_selector("wizard", standard=new_standard)
            st.session_state["wizard_methodology_step2"] = new_methodology_step2

        if parent_id:
            parent_proj = next((p for p in existing_projects if p["id"] == parent_id), None)
            if parent_proj:
                inherited = []
                if parent_proj.get("country") and not new_country:
                    inherited.append(f"Country: {parent_proj['country']}")
                if inherited:
                    st.info(f"Inherited from parent: {', '.join(inherited)}")

        bc1, bc2 = st.columns([1, 3])
        with bc1:
            if st.button("Back", key="wizard_back"):
                st.session_state[step_key] = 1
                st.rerun()
        with bc2:
            if supports_cookstove_wizard:
                if st.button("Continue", key="wizard_to_step3", type="primary"):
                    if not new_name:
                        st.warning("Please enter a project name.")
                    else:
                        st.session_state["wizard_name_saved"] = new_name
                        st.session_state["wizard_standard_saved"] = new_standard
                        st.session_state["wizard_country_saved"] = new_country
                        st.session_state["wizard_desc_saved"] = new_desc
                        st.session_state["wizard_parent_saved"] = parent_id
                        st.session_state["wizard_loc_saved"] = loc_data
                        if monitoring_start:
                            st.session_state["wizard_mon_start_saved"] = monitoring_start.isoformat()
                        if monitoring_end:
                            st.session_state["wizard_mon_end_saved"] = monitoring_end.isoformat()
                        st.session_state[step_key] = 3
                        st.rerun()
            else:
                if st.button("Create Project", key="wizard_create", type="primary"):
                    if not new_name:
                        st.warning("Please enter a project name.")
                    else:
                        final_methodology = st.session_state.get("wizard_methodology_step2")
                        final_country = new_country
                        if parent_id:
                            parent_proj = next((p for p in existing_projects if p["id"] == parent_id), None)
                            if parent_proj:
                                if not final_methodology:
                                    final_methodology = parent_proj.get("methodology")
                                if not final_country:
                                    final_country = parent_proj.get("country")

                        payload = {
                            "name": new_name,
                            "standard": new_standard,
                            "methodology": final_methodology,
                            "country": final_country or None,
                            "description": new_desc or None,
                            "project_type": selected_type,
                            "parent_project_id": parent_id,
                            "location_name": loc_data.get("location_name"),
                            "region": loc_data.get("region"),
                            "district": loc_data.get("district"),
                            "latitude": loc_data.get("latitude"),
                            "longitude": loc_data.get("longitude"),
                        }
                        if monitoring_start:
                            payload["monitoring_period_start"] = monitoring_start.isoformat()
                        if monitoring_end:
                            payload["monitoring_period_end"] = monitoring_end.isoformat()

                        result = _fetch("/projects", method="POST", json=payload)
                        if result:
                            st.success("Project created!")
                            st.session_state["show_new_project"] = False
                            st.session_state.pop(step_key, None)
                            time.sleep(0.5)
                            st.session_state.selected_project_id = result["id"]
                            st.rerun()

    elif step == 3:
        from carbongpt.core.methodology_rules import (
            derive_tpddtec_method,
            derive_methodology_from_fuels,
            get_tpddtec_method_badge_info,
            TPDDTEC_FUEL_DISPLAY,
            TPDDTEC_BASELINE_FUEL_OPTIONS,
            TPDDTEC_PROJECT_FUEL_OPTIONS,
            TPDDTEC_SCALE_OPTIONS,
            TPDDTEC_SCALE_DESCRIPTIONS,
            MECD_DEVICE_OPTIONS,
            MECD_DEVICE_DISPLAY,
            MECD_DEVICE_FUEL_TYPE,
            MECD_DEVICE_CASE,
            MECD_DEVICE_ER_ELIGIBILITY,
            MECD_BASELINE_FUEL_OPTIONS,
            MECD_BASELINE_FUEL_DISPLAY,
            MECD_REGION_OPTIONS,
            MECD_REGION_DISPLAY,
            derive_vm0050_method,
            vm0050_hierarchy_html,
            VM0050_DEVICE_OPTIONS,
            VM0050_DEVICE_DISPLAY,
            VM0050_EC_OPTIONS,
            VM0050_EC_OPTION_DISPLAY,
            VM0050_FNRB_OPTIONS,
            VM0050_FNRB_DISPLAY,
        )
        from carbongpt.core.mecd_simulator import (
            MECD_BASELINE_FUEL_LIBRARY,
            MECD_SC_DEFAULTS,
            MECD_SC_P_EPC_DEFAULTS,
            compute_mecd_baseline_ef,
        )

        saved_name = st.session_state.get("wizard_name_saved", "")
        saved_standard = st.session_state.get("wizard_standard_saved", "GoldStandard")
        saved_country = st.session_state.get("wizard_country_saved", "")
        saved_desc = st.session_state.get("wizard_desc_saved", "")
        saved_parent = st.session_state.get("wizard_parent_saved")
        selected_type = st.session_state.get("new_proj_type", "standalone_pdd")

        std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(saved_standard, saved_standard)
        st.caption(f"Project: **{saved_name}** | Standard: **{std_display}**" + (f" | Country: **{saved_country}**" if saved_country else ""))

        st.markdown("**Step 3: Activity type**")
        activity_category = st.radio(
            "What kind of activity does this project cover?",
            ["Cooking devices", "Renewable electricity", "Other (manual methodology)"],
            key="wizard_activity_type",
            horizontal=False,
        )

        _detected = None
        bl_fuel_top = None
        pj_fuel_top = None
        if activity_category == "Cooking devices":
            # Verra always uses VM0050 — skip generic fuel selector to avoid duplication
            # (VM0050 branch has its own biomass-only baseline fuel + device selectors)
            if saved_standard == "Verra":
                _detected = "VM0050"
                bl_fuel_top = "wood"
                pj_fuel_top = "wood"
                st.info("Methodology auto-detected: **VM0050 v1.0** – Energy Efficiency and Fuel-Switch Measures in Cookstoves")
            else:
                st.markdown("---")
                st.markdown("**Fuel selection**")
                st.caption("Select baseline and project fuels. The applicable methodology is determined automatically from your selection.")
                _BL_FUELS = ["wood", "charcoal", "lpg", "kerosene", "mixed_biomass", "other"]
                _BL_FUEL_DISP = {
                    "wood": "Wood / Firewood", "charcoal": "Charcoal", "lpg": "LPG",
                    "kerosene": "Kerosene", "mixed_biomass": "Mixed biomass", "other": "Other",
                }
                _PJ_FUELS = ["wood", "charcoal", "lpg", "electricity", "biogas", "bioethanol", "other"]
                _PJ_FUEL_DISP = {
                    "wood": "Wood / Firewood (improved)", "charcoal": "Charcoal (improved)",
                    "lpg": "LPG", "electricity": "Electricity (grid)",
                    "biogas": "Biogas", "bioethanol": "Bio-ethanol", "other": "Other",
                }
                fuel_col1, fuel_col2 = st.columns(2)
                with fuel_col1:
                    bl_fuel_top = st.radio(
                        "Baseline fuel (what households currently use)",
                        _BL_FUELS,
                        key="wizard_cookstove_bl_fuel",
                        format_func=lambda x: _BL_FUEL_DISP.get(x, x),
                    )
                with fuel_col2:
                    pj_fuel_top = st.radio(
                        "Project fuel (what the project device will use)",
                        _PJ_FUELS,
                        key="wizard_cookstove_pj_fuel",
                        format_func=lambda x: _PJ_FUEL_DISP.get(x, x),
                    )
                if pj_fuel_top in ("electricity", "lpg", "biogas", "bioethanol"):
                    _detected = "GS-MECD"
                elif pj_fuel_top in ("wood", "charcoal"):
                    _detected = "TPDDTEC"
                else:
                    _detected = None
                if _detected is None:
                    st.warning("Project fuel 'Other' requires manual methodology confirmation. Please contact your standard body.")
                elif _detected == "GS-MECD":
                    st.info("Methodology auto-detected: **GS-MECD v1.2** – Metered & Measured Energy Cooking Devices")
                else:
                    st.info("Methodology auto-detected: **TPDDTEC v4.0**")

        if activity_category == "Cooking devices" and _detected == "VM0050":
            _compat_activity = "VM0050"
        elif activity_category == "Cooking devices" and _detected == "TPDDTEC":
            _compat_activity = "Cookstoves / Thermal energy"
        elif activity_category == "Cooking devices" and _detected == "GS-MECD":
            _compat_activity = "Metered & Measured cooking device (MECD)"
        else:
            _compat_activity = activity_category

        if _compat_activity == "Cookstoves / Thermal energy":
            bl_fuel_choice = bl_fuel_top if (bl_fuel_top in TPDDTEC_BASELINE_FUEL_OPTIONS) else "wood"
            pj_fuel_choice = pj_fuel_top if (pj_fuel_top in TPDDTEC_PROJECT_FUEL_OPTIONS) else "wood"
            st.markdown("---")
            st.markdown("**Scale**")
            scale_labels = [f"{s} ({TPDDTEC_SCALE_DESCRIPTIONS[s]})" for s in TPDDTEC_SCALE_OPTIONS]
            scale_choice_label = st.radio(
                "Expected scale of the project",
                scale_labels,
                key="wizard_scale_label",
            )
            scale_choice = TPDDTEC_SCALE_OPTIONS[scale_labels.index(scale_choice_label)]

            meth_info = derive_methodology_from_fuels(saved_standard, bl_fuel_choice, pj_fuel_choice)
            method_result = derive_tpddtec_method(bl_fuel_choice, pj_fuel_choice, scale_choice, "measured")

            baseline_approach = "measured"
            if method_result["method2_available"]:
                st.markdown("---")
                st.markdown("**Baseline fuel consumption approach**")
                approach_labels = [
                    "Use methodology default  (0.5 t/capita/year fuelwood — no field test needed)",
                    "Use measured field data  (Baseline Performance Field Test required)",
                ]
                approach_choice = st.radio(
                    "How will you determine baseline fuel consumption?",
                    approach_labels,
                    key="wizard_baseline_approach",
                )
                baseline_approach = "default" if "default" in approach_choice else "measured"
                method_result = derive_tpddtec_method(bl_fuel_choice, pj_fuel_choice, scale_choice, baseline_approach)
            elif method_result["baseline_approach_locked"]:
                st.caption(f"Baseline approach: {method_result['approach_lock_reason']}")

            st.markdown("---")
            st.markdown("**Leakage**")
            leakage_labels = [
                "Standard 5% deduction  (Option 1 — recommended, no additional inputs needed)",
                "Project-specific leakage calculation  (Option 2 — requires additional field measurements)",
            ]
            leakage_choice = st.radio(
                "How will you handle leakage?",
                leakage_labels,
                key="wizard_leakage_approach",
            )
            leakage_option = "option_1" if "Option 1" in leakage_choice else "option_2"

            st.markdown("---")
            badge_info = get_tpddtec_method_badge_info(method_result["method_id"])

            if meth_info.get("blocked"):
                st.warning(f"Note: {meth_info['note']}")
            else:
                with st.container(border=True):
                    st.markdown("**Your project will use:**")
                    s1, s2, s3 = st.columns(3)
                    with s1:
                        st.markdown(f"Methodology: **{meth_info['methodology_display']}**")
                        st.caption(meth_info["note"])
                    with s2:
                        st.markdown(f"Method: **{method_result['method_label']}**")
                        st.caption(method_result["reason"])
                    with s3:
                        bl_label = TPDDTEC_FUEL_DISPLAY.get(bl_fuel_choice, bl_fuel_choice)
                        pj_label = TPDDTEC_FUEL_DISPLAY.get(pj_fuel_choice, pj_fuel_choice)
                        st.markdown(f"Fuel: **{bl_label} → {pj_label}**")
                        st.markdown(f"Scale: **{scale_choice}**")
                        leakage_label = "5% standard deduction" if leakage_option == "option_1" else "Project-specific"
                        st.caption(f"Leakage: {leakage_label}")

            wizard_num_devices = st.number_input(
                "Number of cookstoves / devices to be deployed",
                min_value=0, max_value=10_000_000,
                value=int(st.session_state.get("wizard_num_devices", 0)),
                step=1,
                key="wizard_num_devices",
                help="Structured activity data — used by the calculation engine. Enter 0 to set later in the Parameters tab.",
            )

            bk1, cr2 = st.columns([1, 3])
            with bk1:
                if st.button("Back", key="wizard_back_step3"):
                    st.session_state[step_key] = 2
                    st.rerun()
            with cr2:
                if st.button("Create Project", key="wizard_create_step3", type="primary",
                             disabled=meth_info.get("blocked", False)):
                    final_country = saved_country
                    if saved_parent:
                        parent_proj = next((p for p in existing_projects if p["id"] == saved_parent), None)
                        if parent_proj and not final_country:
                            final_country = parent_proj.get("country")

                    meth_settings = {
                        "baseline_fuel": bl_fuel_choice,
                        "project_fuel": pj_fuel_choice,
                        "scale_classification": scale_choice,
                        "baseline_approach": baseline_approach,
                        "leakage_option": leakage_option,
                        "method_selection": method_result["method_label"],
                        "calculation_method": method_result["method_id"],
                    }

                    saved_loc = st.session_state.get("wizard_loc_saved") or {}
                    _wiz_devices = int(st.session_state.get("wizard_num_devices", 0)) or None
                    payload = {
                        "name": saved_name,
                        "standard": saved_standard,
                        "methodology": meth_info.get("methodology") or "",
                        "country": final_country or None,
                        "description": saved_desc or None,
                        "project_type": selected_type,
                        "parent_project_id": saved_parent,
                        "methodology_settings": meth_settings,
                        "location_name": saved_loc.get("location_name"),
                        "region": saved_loc.get("region"),
                        "district": saved_loc.get("district"),
                        "latitude": saved_loc.get("latitude"),
                        "longitude": saved_loc.get("longitude"),
                        "boundary_geojson": saved_loc.get("boundary_geojson"),
                        "project_intake": {"project_overview": {"num_devices": _wiz_devices}} if _wiz_devices else None,
                    }
                    mon_start = st.session_state.get("wizard_mon_start_saved")
                    mon_end = st.session_state.get("wizard_mon_end_saved")
                    if mon_start:
                        payload["monitoring_period_start"] = mon_start
                    if mon_end:
                        payload["monitoring_period_end"] = mon_end

                    result = _fetch("/projects", method="POST", json=payload)
                    if result:
                        st.success(f"Project created with {meth_info['methodology_display']} — {method_result['method_label']}!")
                        st.session_state["show_new_project"] = False
                        st.session_state.pop(step_key, None)
                        for k in ["wizard_name_saved", "wizard_standard_saved", "wizard_country_saved",
                                  "wizard_desc_saved", "wizard_parent_saved",
                                  "wizard_mon_start_saved", "wizard_mon_end_saved"]:
                            st.session_state.pop(k, None)
                        time.sleep(0.5)
                        st.session_state.selected_project_id = result["id"]
                        st.rerun()

        elif _compat_activity == "VM0050":
            # ── VM0050 v1.0 Wizard Branch ────────────────────────────────────
            # Baseline is always biomass for VM0050 (§4 cond. 1)
            vm_bl_fuel = bl_fuel_top if bl_fuel_top in ("wood", "charcoal") else "wood"

            st.markdown("---")
            st.markdown("**Baseline fuel**")
            vm_bl_choice = st.radio(
                "What fuel do households currently burn for cooking?",
                ["wood", "charcoal"],
                index=0 if vm_bl_fuel == "wood" else 1,
                format_func=lambda x: "Wood (firewood)" if x == "wood" else "Charcoal",
                key="vm0050_bl_fuel",
                horizontal=True,
            )

            st.markdown("---")
            st.markdown("**Project device**")
            vm_device = st.radio(
                "What device will the project distribute?",
                VM0050_DEVICE_OPTIONS,
                key="vm0050_device",
                format_func=lambda x: VM0050_DEVICE_DISPLAY.get(x, x),
            )

            # ECi,y determination — show only options valid for the selected device
            st.markdown("---")
            st.markdown("**Baseline energy consumption (ECi,y) determination**")
            _ec_opts_available = [
                k for k in VM0050_EC_OPTIONS
                if not (k == "eq3_efficiency" and vm_device not in ("biomass_ee",))
                and not (k == "eq5_cct" and vm_device not in ("electric_grid", "electric_self"))
            ]
            vm_ec_option = st.radio(
                "How will baseline fuel consumption be determined?",
                _ec_opts_available,
                key="vm0050_ec_option",
                format_func=lambda x: VM0050_EC_OPTION_DISPLAY.get(x, x),
            )

            # fNRB source
            st.markdown("---")
            st.markdown("**Fraction of non-renewable biomass (fNRB) source**")
            st.caption(
                "VM0050 §9.2 requires using the highest-priority source available. "
                "If using CDM TOOL30, the 26% uncertainty discount (×0.74) is mandatory."
            )
            vm_fnrb_source = st.radio(
                "fNRB source for this project region",
                VM0050_FNRB_OPTIONS,
                key="vm0050_fnrb_source",
                format_func=lambda x: VM0050_FNRB_DISPLAY.get(x, x),
            )

            # Derive the calculation route
            vm_method = derive_vm0050_method(
                baseline_fuel=vm_bl_choice,
                project_device=vm_device,
                baseline_ec_option=vm_ec_option,
                fnrb_source=vm_fnrb_source,
            )

            # Show any auto-corrections from the derive function
            for w in vm_method.get("warnings", []):
                st.warning(w)

            st.markdown("---")

            # ── Visual hierarchy ──────────────────────────────────────────────
            st.markdown("**Calculation route for your project**")
            st.markdown(vm0050_hierarchy_html(vm_method), unsafe_allow_html=True)

            # ── Leakage note ──────────────────────────────────────────────────
            st.markdown("---")
            st.info(
                "Leakage: VM0050 §8.3 applies a standard 5% deduction — no additional leakage "
                "measurements are required. Net ER = (BEy − PEy) × 0.95 − LERB,y. "
                "Renewable biomass leakage (LERB,y) is calculated via CDM TOOL16 if applicable."
            )

            # ── LPG sunset warning ────────────────────────────────────────────
            if vm_device == "lpg":
                st.warning(
                    "LPG sunset clause (VM0050 §4 cond. 11c): carbon credits cannot be issued for "
                    "monitoring periods ending after 31 December 2045."
                )

            # ── Electric device efficiency thresholds ─────────────────────────
            if vm_device == "electric_grid":
                st.info(
                    "Electric device minimum efficiency thresholds (VM0050 §4): "
                    "hot plates and electric hobs >= 40%; induction stoves and other electric >= 70%. "
                    "Source: WBT or manufacturer certification submitted at validation."
                )

            # ── Summary card ──────────────────────────────────────────────────
            meth_info_vm = {
                "methodology": "VM0050",
                "methodology_display": "VM0050 v1.0",
                "note": "Verra VCS VM0050 v1.0 — Energy Efficiency and Fuel-Switch Measures in Cookstoves",
                "blocked": False,
            }
            with st.container(border=True):
                st.markdown("**Your project will use:**")
                v1, v2, v3 = st.columns(3)
                with v1:
                    st.markdown("Methodology: **VM0050 v1.0**")
                    fuel_disp = "Wood (firewood)" if vm_bl_choice == "wood" else "Charcoal"
                    st.caption(f"Baseline fuel: {fuel_disp}")
                with v2:
                    st.markdown(f"Baseline: **{vm_method['baseline_eq']} + {vm_method['baseline_ec_eq']}**")
                    st.caption(f"Project: **{vm_method['project_eq']}**")
                with v3:
                    st.markdown(f"Leakage: **Eq. 11 — 0.95 factor**")
                    st.caption(f"fNRB: {VM0050_FNRB_DISPLAY.get(vm_fnrb_source, vm_fnrb_source)[:50]}")

            bk1, cr2 = st.columns([1, 3])
            with bk1:
                if st.button("Back", key="wizard_vm0050_back"):
                    st.session_state[step_key] = 2
                    st.rerun()
            with cr2:
                if st.button("Create Project", key="wizard_vm0050_create", type="primary"):
                    vm_meth_settings = {
                        "baseline_fuel": vm_bl_choice,
                        "project_device": vm_device,
                        "baseline_ec_option": vm_ec_option,
                        "fnrb_source": vm_fnrb_source,
                        "baseline_eq": vm_method["baseline_eq"],
                        "baseline_ec_eq": vm_method["baseline_ec_eq"],
                        "project_eq": vm_method["project_eq"],
                        "leakage_option": "standard_0.95",
                        "method_id": vm_method["method_id"],
                        "requires_kpt": vm_method["requires_kpt"],
                        "requires_cct": vm_method["requires_cct"],
                        "requires_tool07": vm_method["requires_tool07"],
                        "requires_tool05": vm_method["requires_tool05"],
                    }
                    saved_loc = st.session_state.get("wizard_loc_saved") or {}
                    payload = {
                        "name": saved_name,
                        "standard": saved_standard,
                        "methodology": "VM0050",
                        "country": saved_country or None,
                        "description": saved_desc or None,
                        "project_type": selected_type,
                        "parent_project_id": saved_parent,
                        "methodology_settings": vm_meth_settings,
                        "location_name": saved_loc.get("location_name"),
                        "region": saved_loc.get("region"),
                        "district": saved_loc.get("district"),
                        "latitude": saved_loc.get("latitude"),
                        "longitude": saved_loc.get("longitude"),
                        "boundary_geojson": saved_loc.get("boundary_geojson"),
                    }
                    mon_start = st.session_state.get("wizard_mon_start_saved")
                    mon_end = st.session_state.get("wizard_mon_end_saved")
                    if mon_start:
                        payload["monitoring_period_start"] = mon_start
                    if mon_end:
                        payload["monitoring_period_end"] = mon_end

                    result = _fetch("/projects", method="POST", json=payload)
                    if result:
                        st.success(
                            f"Project created — VM0050 v1.0 "
                            f"({vm_method['baseline_eq']} / {vm_method['project_eq']})!"
                        )
                        st.session_state["show_new_project"] = False
                        st.session_state.pop(step_key, None)
                        for k in ["wizard_name_saved", "wizard_standard_saved", "wizard_country_saved",
                                  "wizard_desc_saved", "wizard_parent_saved",
                                  "wizard_mon_start_saved", "wizard_mon_end_saved"]:
                            st.session_state.pop(k, None)
                        time.sleep(0.5)
                        st.session_state.selected_project_id = result["id"]
                        st.rerun()

        elif _compat_activity == "Metered & Measured cooking device (MECD)":
            st.markdown("---")
            st.markdown("**Device type**")
            device_key = st.radio(
                "Project cooking device",
                MECD_DEVICE_OPTIONS,
                key="mecd_device_type",
                format_func=lambda x: MECD_DEVICE_DISPLAY.get(x, x),
            )
            mecd_case = MECD_DEVICE_CASE[device_key]
            fuel_type = MECD_DEVICE_FUEL_TYPE[device_key]
            er_mode = MECD_DEVICE_ER_ELIGIBILITY[device_key]

            if mecd_case == "1":
                st.info(
                    "Case 1: thermal efficiency determinable by Water Boiling Test (WBT). "
                    "Baseline emission factor is expressed per unit of useful cooking energy (Eq. 1 / Eq. 3)."
                )
            else:
                st.info(
                    "Case 2: WBT cannot determine thermal efficiency for this device type (e.g. EPC). "
                    "An SC_b/SC_p energy equivalence ratio is used instead (Eq. 2 / Eq. 4)."
                )

            if er_mode == "efficiency_only":
                st.warning(
                    "Fossil fuel project device — under MECD v1.2 §2.2.1(g), only efficiency improvement "
                    "ER is eligible. Fuel-switch ER cannot be claimed for LPG project devices."
                )

            st.markdown("---")
            st.markdown("**Region**")
            st.caption("Used to select SC_b/SC_p defaults (Case 2) and for contextual reference data.")
            region = st.selectbox(
                "Project region",
                MECD_REGION_OPTIONS,
                key="mecd_region",
                format_func=lambda x: MECD_REGION_DISPLAY.get(x, x),
            )

            st.markdown("---")
            st.markdown("**Baseline fuel mix**")
            st.caption("Add all fuels currently used by target households. Shares must sum to 100%.")

            n_fuels = st.selectbox(
                "Number of baseline fuel types",
                [1, 2, 3, 4],
                key="mecd_n_fuels",
            )

            baseline_fuels_data = []
            has_woody_baseline = False
            total_share = 0.0

            for i in range(n_fuels):
                st.markdown(f"**Baseline fuel {i + 1}**")
                rc1, rc2, rc3 = st.columns([2, 1, 1])
                with rc1:
                    fk = st.selectbox(
                        "Fuel type",
                        MECD_BASELINE_FUEL_OPTIONS,
                        key=f"mecd_bl_fk_{i}",
                        format_func=lambda x: MECD_BASELINE_FUEL_DISPLAY.get(x, x),
                    )
                lib_row = MECD_BASELINE_FUEL_LIBRARY.get(fk, MECD_BASELINE_FUEL_LIBRARY["wood_three_stone"])
                with rc2:
                    default_share = round(100.0 / n_fuels, 1)
                    share_pct = st.number_input(
                        "Share (%)",
                        min_value=0.1,
                        max_value=100.0,
                        value=default_share,
                        step=0.1,
                        key=f"mecd_bl_share_{i}",
                    )
                with rc3:
                    eta_default = lib_row["eta_b_default"] or 0.20
                    eta_b = st.number_input(
                        "Efficiency (0-1)",
                        min_value=0.01,
                        max_value=1.0,
                        value=float(eta_default),
                        step=0.01,
                        key=f"mecd_bl_eta_{i}",
                    )

                fnrb_val = 0.0
                if lib_row["uses_fnrb"]:
                    has_woody_baseline = True
                    fnrb_val = st.slider(
                        f"fNRB – fraction non-renewable biomass (fuel {i + 1})",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.50,
                        step=0.01,
                        key=f"mecd_bl_fnrb_{i}",
                    )

                total_share += share_pct
                baseline_fuels_data.append({
                    "fuel_key": fk,
                    "share_pct": share_pct,
                    "eta_b": eta_b,
                    "fnrb": fnrb_val,
                })

            if abs(total_share - 100.0) > 0.5:
                st.warning(f"Baseline fuel shares sum to {total_share:.1f}% — must equal 100%.")
            else:
                st.success(f"Baseline shares: {total_share:.1f}% — OK")

            if has_woody_baseline:
                st.markdown("---")
                st.markdown("**fNRB approach (MECD 13)**")
                st.caption(
                    "fNRB enters the baseline emission factor. "
                    "Choose whether to fix it ex-ante for the full crediting period or update it biennially."
                )
                fnrb_approach_choice = st.radio(
                    "fNRB determination method",
                    [
                        "Fixed ex-ante for the full crediting period",
                        "Updated biennially at each monitoring and verification",
                    ],
                    key="mecd_fnrb_approach",
                )
                fnrb_approach = "fixed" if "Fixed" in fnrb_approach_choice else "biennial"
            else:
                fnrb_approach = "not_applicable"

            is_electric = fuel_type == "electric"
            n_persons = None
            eta_p = None

            if is_electric:
                eg_mwh = None
                ef_el = None
                tdl = None
                p_kg = None
                ncv_p = None
                ef_p = None
                st.info(
                    "Electric project device: EG (MWh/device/yr), EF_el, T&D losses, and n_persons "
                    "are measurement inputs — enter them in the Parameters tab after project creation."
                )
            else:
                st.markdown("---")
                st.markdown("**Project fuel parameters**")
                st.caption(
                    "Enter default values for the project fuel. "
                    "These can be refined in the Parameters tab after project creation."
                )
                fp1, fp2, fp3 = st.columns(3)
                with fp1:
                    p_kg = st.number_input(
                        "Annual fuel per device (kg/yr) — MECD 14",
                        min_value=0.1,
                        value=120.0,
                        step=1.0,
                        key="mecd_p_kg_annual",
                    )
                with fp2:
                    ncv_p = st.number_input(
                        "Project fuel NCV (TJ/tonne)",
                        min_value=0.001,
                        value=0.04713,
                        step=0.0001,
                        format="%.5f",
                        key="mecd_ncv_p",
                    )
                with fp3:
                    ef_p = st.number_input(
                        "Project fuel emission factor (tCO2e/TJ)",
                        min_value=0.0,
                        value=63.1,
                        step=0.1,
                        key="mecd_ef_p",
                    )
                eg_mwh = None
                ef_el = None
                tdl = None

            if mecd_case == "2":
                st.markdown("---")
                st.markdown("**Case 2: Specific energy consumption parameters (MECD 7 / 8)**")
                st.caption(
                    "SC_b and SC_p in MJ/person/event. The ratio SC_b/SC_p is dimensionless — "
                    "it acts as an energy equivalence factor in Eq. 4. "
                    "Always store both in the same unit."
                )
                dominant_fk = max(baseline_fuels_data, key=lambda f: f["share_pct"])["fuel_key"] if baseline_fuels_data else "charcoal"
                dominant_family = MECD_BASELINE_FUEL_LIBRARY.get(dominant_fk, {}).get("fuel_family", "charcoal")
                sc_b_raw = MECD_SC_DEFAULTS.get(region, {}).get(dominant_family)
                sc_b_default = float(sc_b_raw) if sc_b_raw is not None else 3.92
                sc_p_default = float(MECD_SC_P_EPC_DEFAULTS.get(region, 0.258))
                sc_col1, sc_col2 = st.columns(2)
                with sc_col1:
                    sc_b_mj = st.number_input(
                        "SC_b – baseline specific consumption (MJ/person/event)",
                        min_value=0.01,
                        value=sc_b_default,
                        step=0.01,
                        format="%.4f",
                        key="mecd_sc_b",
                    )
                with sc_col2:
                    sc_p_mj = st.number_input(
                        "SC_p – project device specific consumption (MJ/person/event)",
                        min_value=0.001,
                        value=sc_p_default,
                        step=0.001,
                        format="%.4f",
                        key="mecd_sc_p",
                    )
                if sc_p_mj > 0:
                    st.caption(f"SC_b/SC_p ratio: {sc_b_mj / sc_p_mj:.4f}")
            else:
                sc_b_mj = None
                sc_p_mj = None

            st.markdown("---")
            st.markdown("**Leakage**")
            leakage_labels_m = [
                "Option 1 – Standard 5% deduction (recommended, no additional inputs needed)",
                "Option 2 – Project-specific calculation (RECH V4.0 §3.11, requires additional field measurements)",
            ]
            leakage_choice_m = st.radio(
                "Leakage approach",
                leakage_labels_m,
                key="mecd_leakage_option",
            )
            leakage_option = "option_1" if "Option 1" in leakage_choice_m else "option_2"

            st.markdown("---")

            shares_ok = abs(total_share - 100.0) <= 0.5
            ef_preview = None
            ef_label_preview = ""
            if shares_ok and baseline_fuels_data:
                try:
                    bf = compute_mecd_baseline_ef(mecd_case, baseline_fuels_data)
                    ef_preview = bf["ef_b"]
                    ef_label_preview = bf["label"]
                except Exception:
                    ef_preview = None

            with st.container(border=True):
                st.markdown("**Project configuration summary**")
                s1, s2, s3 = st.columns(3)
                with s1:
                    st.markdown("Methodology: **MECD v1.2**")
                    st.caption("Gold Standard – Metered & Measured Energy Cooking Devices")
                with s2:
                    st.markdown(f"Device: **{MECD_DEVICE_DISPLAY.get(device_key, device_key)}**")
                    er_disp = "Efficiency improvement only" if er_mode == "efficiency_only" else "Fuel-switch + efficiency ER"
                    st.caption(f"Case {mecd_case} | {fuel_type.upper()} | {er_disp}")
                with s3:
                    if ef_preview is not None:
                        st.markdown(f"{ef_label_preview} (ex-ante): **{ef_preview:.2f} tCO2e/TJ**")
                    else:
                        st.caption("Baseline EF: fix fuel shares to preview.")
                    leakage_disp = "5% standard deduction" if leakage_option == "option_1" else "Project-specific (RECH §3.11)"
                    st.caption(f"Leakage: {leakage_disp}")

            bk1_m, cr2_m = st.columns([1, 3])
            with bk1_m:
                if st.button("Back", key="mecd_wizard_back"):
                    st.session_state[step_key] = 2
                    st.rerun()
            with cr2_m:
                if st.button(
                    "Create Project",
                    key="mecd_wizard_create",
                    type="primary",
                    disabled=not shares_ok,
                ):
                    final_country = saved_country
                    if saved_parent:
                        parent_proj = next((p for p in existing_projects if p["id"] == saved_parent), None)
                        if parent_proj and not final_country:
                            final_country = parent_proj.get("country")

                    meth_settings = {
                        "mecd_case": mecd_case,
                        "project_fuel_type": fuel_type,
                        "device_type": device_key,
                        "device_label": MECD_DEVICE_DISPLAY.get(device_key, device_key),
                        "er_eligibility": er_mode,
                        "baseline_fuels": baseline_fuels_data,
                        "region": region,
                        "fnrb_approach": fnrb_approach,
                        "leakage_option": leakage_option,
                        "n_persons": n_persons,
                    }
                    if mecd_case == "1" and eta_p is not None:
                        meth_settings["eta_p"] = eta_p
                    if is_electric:
                        meth_settings["eg_p_mwh_annual"] = eg_mwh
                        meth_settings["ef_el"] = ef_el
                        meth_settings["tdl"] = tdl
                    else:
                        meth_settings["p_p_kg_annual"] = p_kg
                        meth_settings["ncv_p"] = ncv_p
                        meth_settings["ef_p"] = ef_p
                    if mecd_case == "2":
                        meth_settings["sc_b_mj"] = sc_b_mj
                        meth_settings["sc_p_mj"] = sc_p_mj
                    if ef_preview is not None:
                        meth_settings["baseline_ef_exante"] = round(ef_preview, 4)

                    saved_loc = st.session_state.get("wizard_loc_saved") or {}
                    payload = {
                        "name": saved_name,
                        "standard": saved_standard,
                        "methodology": "GS-MECD",
                        "country": final_country or None,
                        "description": saved_desc or None,
                        "project_type": selected_type,
                        "parent_project_id": saved_parent,
                        "methodology_settings": meth_settings,
                        "location_name": saved_loc.get("location_name"),
                        "region": saved_loc.get("region"),
                        "district": saved_loc.get("district"),
                        "latitude": saved_loc.get("latitude"),
                        "longitude": saved_loc.get("longitude"),
                        "boundary_geojson": saved_loc.get("boundary_geojson"),
                    }
                    mon_start = st.session_state.get("wizard_mon_start_saved")
                    mon_end = st.session_state.get("wizard_mon_end_saved")
                    if mon_start:
                        payload["monitoring_period_start"] = mon_start
                    if mon_end:
                        payload["monitoring_period_end"] = mon_end

                    result = _fetch("/projects", method="POST", json=payload)
                    if result:
                        st.success("Project created with MECD v1.2 (Metered & Measured Energy Cooking Devices)!")
                        st.session_state["show_new_project"] = False
                        st.session_state.pop(step_key, None)
                        for k in ["wizard_name_saved", "wizard_standard_saved", "wizard_country_saved",
                                  "wizard_desc_saved", "wizard_parent_saved",
                                  "wizard_mon_start_saved", "wizard_mon_end_saved"]:
                            st.session_state.pop(k, None)
                        time.sleep(0.5)
                        st.session_state.selected_project_id = result["id"]
                        st.rerun()

        else:
            st.markdown("---")
            if activity_category == "Other (manual methodology)":
                new_methodology_s3 = _methodology_selector("wizard_s3", standard=saved_standard)
            else:
                new_methodology_s3 = _methodology_selector("wizard_s3", standard=saved_standard)

            bk1, cr2 = st.columns([1, 3])
            with bk1:
                if st.button("Back", key="wizard_back_other"):
                    st.session_state[step_key] = 2
                    st.rerun()
            with cr2:
                if st.button("Create Project", key="wizard_create_other", type="primary"):
                    if not saved_name:
                        st.warning("Please go back and enter a project name.")
                    else:
                        final_country = saved_country
                        if saved_parent:
                            parent_proj = next((p for p in existing_projects if p["id"] == saved_parent), None)
                            if parent_proj and not final_country:
                                final_country = parent_proj.get("country")

                        payload = {
                            "name": saved_name,
                            "standard": saved_standard,
                            "methodology": new_methodology_s3 or None,
                            "country": final_country or None,
                            "description": saved_desc or None,
                            "project_type": selected_type,
                            "parent_project_id": saved_parent,
                        }
                        mon_start = st.session_state.get("wizard_mon_start_saved")
                        mon_end = st.session_state.get("wizard_mon_end_saved")
                        if mon_start:
                            payload["monitoring_period_start"] = mon_start
                        if mon_end:
                            payload["monitoring_period_end"] = mon_end

                        result = _fetch("/projects", method="POST", json=payload)
                        if result:
                            st.success("Project created!")
                            st.session_state["show_new_project"] = False
                            st.session_state.pop(step_key, None)
                            for k in ["wizard_name_saved", "wizard_standard_saved", "wizard_country_saved",
                                      "wizard_desc_saved", "wizard_parent_saved",
                                      "wizard_mon_start_saved", "wizard_mon_end_saved"]:
                                st.session_state.pop(k, None)
                            time.sleep(0.5)
                            st.session_state.selected_project_id = result["id"]
                            st.rerun()


def _get_project_readiness(project, project_id):
    readiness = {
        "has_methodology": bool(project.get("methodology")),
        "has_country": bool(project.get("country")),
        "params_total": 0,
        "params_configured": 0,
        "params_pending": 0,
        "doc_count": len(project.get("documents", [])),
        "has_drafts": False,
        "has_sim": False,
        "has_selected_scenario": bool(project.get("selected_scenario_id")),
        "selected_scenario_name": None,
        "selected_scenario_er": None,
        "has_audit": False,
        "audit_score": None,
    }

    params_data = _fetch(f"/projects/{project_id}/parameters")
    param_list = params_data if isinstance(params_data, list) else (params_data.get("parameters", []) if isinstance(params_data, dict) else [])
    readiness["params_total"] = len(param_list)
    readiness["params_configured"] = sum(1 for p in param_list if p.get("value") is not None)
    readiness["params_pending"] = readiness["params_total"] - readiness["params_configured"]

    sessions_data = _fetch(f"/projects/{project_id}/write-sessions?doc_type={PROJECT_TYPE_INFO.get(project.get('project_type', 'standalone_pdd'), {}).get('default_doc_type', 'pdd')}")
    if sessions_data and isinstance(sessions_data, list) and len(sessions_data) > 0:
        readiness["has_drafts"] = True

    if f"sim_result_{project_id}" in st.session_state and st.session_state[f"sim_result_{project_id}"]:
        readiness["has_sim"] = True
    else:
        scenarios_resp = _fetch(f"/projects/{project_id}/er-scenarios")
        scenarios_list = scenarios_resp if isinstance(scenarios_resp, list) else (scenarios_resp.get("scenarios", []) if isinstance(scenarios_resp, dict) else [])
        if len(scenarios_list) > 0:
            readiness["has_sim"] = True

    if f"audit_result_{project_id}" in st.session_state and st.session_state[f"audit_result_{project_id}"]:
        readiness["has_audit"] = True
        cached = st.session_state[f"audit_result_{project_id}"]
        readiness["audit_score"] = cached.get("overall_score")
    else:
        audit_history = _fetch(f"/projects/{project_id}/audit-simulation/history")
        if audit_history and isinstance(audit_history, list) and len(audit_history) > 0:
            readiness["has_audit"] = True
            readiness["audit_score"] = audit_history[0].get("overall_score")

    return readiness


def _build_next_steps(readiness):
    steps = []
    if not readiness["has_methodology"]:
        steps.append({
            "text": "Select a methodology",
            "desc": "Go to Setup and choose a carbon standard and methodology for your project.",
            "tab": "Setup",
        })
        return steps

    if not readiness["has_country"]:
        steps.append({
            "text": "Set the project country",
            "desc": "The country determines default emission factors and regulatory requirements.",
            "tab": "Setup",
        })

    if readiness["params_total"] == 0:
        steps.append({
            "text": "Initialize parameters from methodology",
            "desc": "Parameters define the technical inputs for your emission reduction calculations.",
            "tab": "Parameters",
        })
    elif readiness["params_pending"] > 0:
        steps.append({
            "text": f"Configure {readiness['params_pending']} missing parameter{'s' if readiness['params_pending'] != 1 else ''}",
            "desc": "Set measured or estimated values so the ER Simulator can run accurate calculations.",
            "tab": "Parameters",
        })

    if readiness["params_total"] > 0 and readiness["params_pending"] == 0 and not readiness["has_sim"]:
        steps.append({
            "text": "Run the ER Simulator",
            "desc": "All parameters are configured. Estimate your project's annual emission reductions.",
            "tab": "ER Simulator",
        })

    if readiness["has_sim"] and not readiness["has_selected_scenario"]:
        steps.append({
            "text": "Select a scenario for PDD drafting",
            "desc": "Choose which ER scenario the AI writer should reference when drafting document sections.",
            "tab": "ER Simulator",
        })

    if readiness["doc_count"] == 0:
        steps.append({
            "text": "Upload supporting documents",
            "desc": "Upload KPT reports, feasibility studies, or existing documents as AI context.",
            "tab": "Documents",
        })

    if not readiness["has_drafts"] and readiness["has_methodology"]:
        steps.append({
            "text": "Draft your first document section",
            "desc": "Use the AI writer to generate PDD or MR sections based on your project data.",
            "tab": "Write / Draft",
        })

    if readiness["has_drafts"] and not readiness["has_audit"]:
        steps.append({
            "text": "Run an audit simulation",
            "desc": "Check your project's readiness for VVB review before submission.",
            "tab": "Audit",
        })

    if readiness["has_sim"] and readiness["has_drafts"]:
        steps.append({
            "text": "Review your draft",
            "desc": "Run an AI compliance review to identify gaps in your document.",
            "tab": "Review",
        })

    return steps[:3]


def _render_next_steps_panel(project, project_id):
    from carbongpt.core.project_state import evaluate_project_state, SEVERITY_BLOCKER, SEVERITY_WARNING, SEVERITY_SUGGESTION, SEVERITY_INSIGHT

    state = evaluate_project_state(project_id)
    if "error" in state:
        readiness = _get_project_readiness(project, project_id)
        steps = _build_next_steps(readiness)
        if not steps:
            return
        _render_next_steps_fallback(project_id, steps)
        return

    TAB_LABEL_TO_INDEX = {
        "Setup": 0, "Documents": 1, "Parameters": 2, "ER Simulator": 3,
        "Write / Draft": 4, "Review": 5, "Audit": 6, "Findings": 7,
        "Lifecycle": 8, "Monitoring": 9, "Export": 10,
    }

    def _go_to_tab(pid, idx):
        st.session_state[f"ws_tab_{pid}"] = idx

    readiness_score = state.get("readiness_score", 0)
    score_color = "#ef4444" if readiness_score < 30 else "#f59e0b" if readiness_score < 60 else "#10b981" if readiness_score < 85 else "#059669"

    st.markdown(
        f'<span style="font-size:0.85rem;font-weight:600;color:var(--text-secondary);">'
        f'Project Readiness: <span style="color:{score_color};font-size:1.1rem;">{readiness_score}%</span>'
        f'</span>',
        unsafe_allow_html=True,
    )
    st.progress(readiness_score / 100)

    _render_state_dashboard(state, project_id)

    items = state.get("items", [])
    blockers = [i for i in items if i["severity"] == SEVERITY_BLOCKER]
    warnings = [i for i in items if i["severity"] == SEVERITY_WARNING]
    suggestions = [i for i in items if i["severity"] == SEVERITY_SUGGESTION]
    insights = [i for i in items if i["severity"] == SEVERITY_INSIGHT]

    if blockers:
        for item in blockers:
            st.error(f"**{item['message']}** -- {item['detail']}")

    actions = state.get("next_actions", [])
    if actions:
        st.markdown("**Next Actions**")
        for i, action in enumerate(actions, 1):
            priority_marker = {
                "high": "!!",
                "medium": "!",
                "low": "",
            }.get(action.get("priority", ""), "")

            cols = st.columns([0.4, 4, 1.2])
            with cols[0]:
                bg = "#ef4444" if action["priority"] == "high" else "#f59e0b" if action["priority"] == "medium" else "var(--brand-primary)"
                st.markdown(f'<span style="display:inline-block;width:24px;height:24px;border-radius:50%;background:{bg};color:white;font-size:0.72rem;font-weight:700;text-align:center;line-height:24px;">{i}</span>', unsafe_allow_html=True)
            with cols[1]:
                st.markdown(f"**{action['text']}**")
                st.caption(action["detail"])
            with cols[2]:
                tab_name = action.get("tab", "")
                if tab_name and tab_name in TAB_LABEL_TO_INDEX:
                    target_idx = TAB_LABEL_TO_INDEX[tab_name]
                    st.button("Go", key=f"nextstep_{project_id}_{i}", use_container_width=True,
                              on_click=_go_to_tab, args=(project_id, target_idx))

    if insights:
        with st.expander("Insights", expanded=False):
            for item in insights:
                st.info(f"**{item['message']}** -- {item['detail']}")


def _render_state_dashboard(state, project_id):
    params = state.get("parameters", {})
    scenario = state.get("scenario", {})
    drafts = state.get("drafts", {})
    audit = state.get("audit", {})
    stage = state.get("stage", {})
    evidence = state.get("evidence", {})

    sc1, sc2, sc3 = st.columns(3)

    with sc1:
        with st.container(border=True):
            st.markdown("**Project Stage**")
            stage_display = stage.get("display", "Not Initialized")
            st.markdown(f'<span style="font-size:1.1rem;font-weight:600;">{stage_display}</span>', unsafe_allow_html=True)

            st.markdown("**Parameter Health**")
            if params.get("initialized"):
                pct = params.get("pct_complete", 0)
                st.progress(pct / 100)
                status_parts = []
                if params.get("confirmed", 0) > 0:
                    status_parts.append(f"{params['confirmed']} confirmed")
                if params.get("default", 0) > 0:
                    status_parts.append(f"{params['default']} default")
                if params.get("estimated", 0) > 0:
                    status_parts.append(f"{params['estimated']} estimated")
                if params.get("missing", 0) > 0:
                    status_parts.append(f"{params['missing']} missing")
                st.caption(f"{params['configured']}/{params['total']} configured -- " + ", ".join(status_parts))
            else:
                st.caption("Parameters not initialized")

    with sc2:
        with st.container(border=True):
            st.markdown("**Selected Scenario**")
            if scenario.get("has_selected"):
                st.markdown(f'<span style="font-size:0.95rem;font-weight:600;">{scenario["selected_name"]}</span>', unsafe_allow_html=True)
                if scenario.get("selected_annual_er"):
                    st.metric("Annual ER", f"{scenario['selected_annual_er']:,.0f} tCO2e/yr")
                if scenario.get("selected_total_er"):
                    st.caption(f"Total: {scenario['selected_total_er']:,.0f} tCO2e")
            else:
                st.caption(f"No scenario selected ({scenario.get('total_saved', 0)} saved)")

            st.markdown("**Documents**")
            doc_count = state.get("documents", {}).get("count", 0)
            st.caption(f"{doc_count} supporting document{'s' if doc_count != 1 else ''} uploaded")

    with sc3:
        with st.container(border=True):
            st.markdown("**Draft Status**")
            if drafts.get("has_drafts"):
                st.caption(f"{drafts['total_sections']} section{'s' if drafts['total_sections'] != 1 else ''} -- {drafts['approved']} approved, {drafts['drafted']} in draft")
            else:
                st.caption("No sections drafted yet")

            st.markdown("**Audit Readiness**")
            if audit.get("has_audit"):
                score = audit.get("score", 0)
                risk = audit.get("risk_level", "")
                color = "#ef4444" if score < 60 else "#f59e0b" if score < 80 else "#10b981"
                st.markdown(f'<span style="font-size:1.2rem;font-weight:700;color:{color};">{score}%</span> <span style="font-size:0.8rem;color:var(--text-secondary);">({risk})</span>', unsafe_allow_html=True)
                st.caption(f"{audit.get('cars', 0)} CARs, {audit.get('cls', 0)} CLs, {audit.get('fwds', 0)} FWDs")
            else:
                st.caption("No audit simulation run")

            st.markdown("**Evidence**")
            if evidence.get("has_evidence"):
                st.caption(f"{evidence['verified']}/{evidence['total_links']} links verified")
            else:
                st.caption("No evidence links")


def _render_next_steps_fallback(project_id, steps):
    TAB_LABEL_TO_INDEX = {
        "Setup": 0, "Documents": 1, "Parameters": 2, "ER Simulator": 3,
        "Write / Draft": 4, "Review": 5, "Audit": 6, "Findings": 7,
        "Lifecycle": 8, "Monitoring": 9, "Export": 10,
    }

    def _go_to_tab(pid, idx):
        st.session_state[f"ws_tab_{pid}"] = idx

    st.markdown("**Suggested Next Steps**")
    for i, step in enumerate(steps, 1):
        cols = st.columns([0.4, 4, 1.2])
        with cols[0]:
            st.markdown(f'<span style="display:inline-block;width:24px;height:24px;border-radius:50%;background:var(--brand-primary);color:white;font-size:0.72rem;font-weight:700;text-align:center;line-height:24px;">{i}</span>', unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"**{step['text']}**")
            st.caption(step['desc'])
        with cols[2]:
            tab_name = step.get("tab", "")
            if tab_name in TAB_LABEL_TO_INDEX:
                target_idx = TAB_LABEL_TO_INDEX[tab_name]
                st.button("Go", key=f"nextstep_{project_id}_{i}", use_container_width=True,
                          on_click=_go_to_tab, args=(project_id, target_idx))


def _render_readiness_banner(banner_type, message):
    icon_map = {
        "ready": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>',
        "warning": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
        "info": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
    }
    css_class = f"readiness-banner readiness-banner-{banner_type}"
    icon = icon_map.get(banner_type, icon_map["info"])
    st.markdown(
        f'<span class="{css_class}" data-testid="readiness-banner"><span class="readiness-banner-icon">{icon}</span> {message}</span>',
        unsafe_allow_html=True,
    )


def _get_recommended_tab_index(project, project_id, total_params, missing_params, doc_count, projected_er, audit_score):
    if not project.get("methodology"):
        return 0
    if total_params == 0:
        return 2
    if missing_params > 0:
        return 2
    if projected_er == "--":
        return 3
    sessions_data = _fetch(f"/projects/{project_id}/write-sessions?doc_type={PROJECT_TYPE_INFO.get(project.get('project_type', 'standalone_pdd'), {}).get('default_doc_type', 'pdd')}")
    has_drafts = bool(sessions_data and isinstance(sessions_data, list) and len(sessions_data) > 0)
    if not has_drafts:
        return 4
    if audit_score == "--":
        return 6
    return 5


def _build_activity_feed(project):
    items = []
    documents = project.get("documents", [])
    for doc in documents:
        items.append({
            "text": f"Document uploaded: {doc.get('file_name', 'file')}",
            "dot": "green",
            "time": doc.get("uploaded_at", ""),
        })
    status = project.get("status", "draft")
    if status != "draft":
        items.append({
            "text": f"Project status changed to {STATUS_LABELS.get(status, status)}",
            "dot": "blue",
            "time": "",
        })
    if project.get("methodology"):
        items.append({
            "text": f"Methodology set: {project['methodology']}",
            "dot": "teal",
            "time": "",
        })
    if not items:
        items.append({
            "text": "Project created",
            "dot": "teal",
            "time": "",
        })
    return items[:8]


def _render_project_workspace(project_id):
    project = _fetch(f"/projects/{project_id}")
    if not project:
        st.error("Project not found.")
        st.session_state.selected_project_id = None
        st.rerun()
        return

    back_col, _ = st.columns([1.5, 6])
    with back_col:
        if st.button("← Back to Projects", key="back_to_projects"):
            st.session_state.selected_project_id = None
            st.rerun()

    status = project.get("status", "draft")
    status_label = STATUS_LABELS.get(status, status)
    project_type = project.get("project_type", "standalone_pdd")
    type_info = PROJECT_TYPE_INFO.get(project_type, PROJECT_TYPE_INFO["standalone_pdd"])
    badge_class = type_info.get("badge_class", "badge-pdd")
    status_class = f"status-{status.replace('_', '')}"

    std_raw = project.get("standard", "")
    std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(std_raw, std_raw)
    std_badge_class = "workspace-badge-gs" if std_raw == "GoldStandard" else "workspace-badge-verra"

    meta_items = []
    if project.get("methodology"):
        meta_items.append(f'<span class="workspace-meta-item">{SVG_ICONS.get("methodology", "")} {project["methodology"]}</span>')
    if project.get("country"):
        meta_items.append(f'<span class="workspace-meta-item">{SVG_ICONS.get("globe", "")} {project["country"]}</span>')
    meta_html = '<span class="ws-meta-sep">&bull;</span>'.join(meta_items)

    parent_html = ""
    if project.get("parent_project_id"):
        parent = _fetch(f"/projects/{project['parent_project_id']}")
        if parent:
            parent_type_info = PROJECT_TYPE_INFO.get(parent.get("project_type", ""), {})
            parent_short = parent_type_info.get("short", "Project")
            parent_html = f'<div style="margin-top:8px;"><span class="stat-pill">Linked to {parent_short}: {parent["name"]}</span></div>'

    desc_html = ""
    if project.get("description"):
        desc_html = f'<div style="margin-top:10px;font-size:0.85rem;color:var(--text-secondary);line-height:1.55;">{project["description"]}</div>'

    st.markdown(
        f'''<div class="ws-header-card">
            <div class="ws-header-badges">
                <span class="project-type-badge {badge_class}">{type_info["short"]}</span>
                <span class="workspace-header-badge {std_badge_class}">{std_display}</span>
                <span class="status-badge {status_class}">{status_label}</span>
            </div>
            <div class="ws-header-title">{project["name"]}</div>
            <div class="ws-header-meta">{meta_html}</div>
            {parent_html}{desc_html}
        </div>''',
        unsafe_allow_html=True,
    )

    def _nav_to_tab(pid, idx):
        st.session_state[f"ws_tab_{pid}"] = idx

    qa_col1, qa_col2, qa_col3, qa_divider, qa_col4 = st.columns([1, 1, 1, 0.05, 1])
    with qa_col1:
        st.button("Write Section", key=f"qa_write_{project_id}", use_container_width=True,
                  on_click=_nav_to_tab, args=(project_id, 4))
    with qa_col2:
        st.button("Run Audit", key=f"qa_audit_{project_id}", use_container_width=True,
                  on_click=_nav_to_tab, args=(project_id, 6))
    with qa_col3:
        st.button("ER Simulator", key=f"qa_er_{project_id}", use_container_width=True,
                  on_click=_nav_to_tab, args=(project_id, 3))
    with qa_col4:
        if st.button("AI Copilot", key=f"qa_chat_{project_id}", type="primary", use_container_width=True):
            st.session_state.chat_open = True
            st.rerun()

    documents = project.get("documents", [])
    doc_count = len(documents)

    params_data = _fetch(f"/projects/{project_id}/parameters")
    param_list = params_data if isinstance(params_data, list) else (params_data.get("parameters", []) if isinstance(params_data, dict) else [])
    total_params = len(param_list)
    configured_params = sum(1 for p in param_list if p.get("value") is not None)
    missing_params = total_params - configured_params

    projected_er = "--"
    er_cache_key = f"sim_result_{project_id}"
    if er_cache_key in st.session_state and st.session_state[er_cache_key]:
        cached_er = st.session_state[er_cache_key]
        yr_results = cached_er.get("year_by_year", [])
        if yr_results:
            total_er_val = sum(y.get("net_er", 0) for y in yr_results)
            avg_er = total_er_val / len(yr_results) if yr_results else 0
            projected_er = f"{avg_er:,.0f}"

    if projected_er == "--" and project.get("selected_scenario_id"):
        try:
            from carbongpt.core.er_simulator import get_selected_scenario
            sel = get_selected_scenario(project_id)
            if sel:
                summary = sel["scenario"].get("results_summary") or {}
                if isinstance(summary, str):
                    import json as _j
                    try:
                        summary = _j.loads(summary)
                    except Exception:
                        summary = {}
                if summary.get("average_annual_er"):
                    projected_er = f"{summary['average_annual_er']:,.0f}"
        except Exception:
            pass

    audit_score = "--"
    audit_cache_key = f"audit_result_{project_id}"
    if audit_cache_key in st.session_state and st.session_state[audit_cache_key]:
        cached_audit = st.session_state[audit_cache_key]
        score = cached_audit.get("overall_score")
        if score is not None:
            audit_score = f"{score}%"

    if audit_score == "--":
        try:
            from carbongpt.repository.db import get_cursor as _gc
            with _gc() as _cur:
                _cur.execute("""
                    SELECT overall_score FROM audit_simulation_results
                    WHERE project_id = %s ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                _audit_row = _cur.fetchone()
                if _audit_row and _audit_row.get("overall_score") is not None:
                    audit_score = f"{_audit_row['overall_score']}%"
        except Exception:
            pass

    param_status_text = f"{configured_params} / {total_params}" if total_params > 0 else "Not initialized"
    param_sub = f"{missing_params} missing" if missing_params > 0 and total_params > 0 else "All configured" if total_params > 0 else "Initialize parameters first"
    param_sub_class = "status-dot-amber" if missing_params > 0 else "status-dot-green" if total_params > 0 else ""

    scenario_label = "--"
    if project.get("selected_scenario_id"):
        try:
            from carbongpt.core.er_simulator import get_selected_scenario as _get_sel
            sel = _get_sel(project_id)
            if sel:
                scenario_label = sel["scenario"].get("name", "Selected")[:20]
        except Exception:
            scenario_label = "Selected"

    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    with mc1:
        st.metric(label="Projected ER (tCO2e/yr)", value=projected_er, delta=None, help="Average annual emission reductions from selected scenario")
    with mc2:
        st.metric(label="Parameters", value=param_status_text, delta=None, help=param_sub)
    with mc3:
        st.metric(label="Scenario", value=scenario_label, delta=None, help="Selected ER scenario for PDD drafting")
    with mc4:
        st.metric(label="Documents", value=doc_count, delta=None, help="Project documents uploaded")
    with mc5:
        st.metric(label="Audit Readiness", value=audit_score, delta=None, help="Run audit simulation to assess")

    _render_next_steps_panel(project, project_id)

    with st.expander("Recent Activity", expanded=False):
        activity_items = _build_activity_feed(project)
        items_html = ""
        for item in activity_items:
            time_html = f'<span class="activity-time">{item["time"][:10]}</span>' if item["time"] else ""
            items_html += f"""
            <span class="activity-item">
                <span class="activity-dot activity-dot-{item['dot']}"></span>
                <span>
                    <span class="activity-text">{item['text']}</span>
                    {time_html}
                </span>
            </span>"""
        st.markdown(f"""
        <span class="activity-feed" data-testid="activity-feed">
            <span class="activity-feed-title">{SVG_ICONS.get("activity", "")} Recent Activity</span>
            {items_html}
        </span>
        """, unsafe_allow_html=True)

    if project_type == "poa_programme":
        children = _fetch(f"/projects/{project_id}/children") or []
        if children:
            with st.expander(f"{len(children)} VPA{'s' if len(children) != 1 else ''} in this programme"):
                for child in children:
                    child_type_info = PROJECT_TYPE_INFO.get(child.get("project_type", ""), {})
                    child_badge = child_type_info.get("badge_class", "badge-vpa")
                    cc1, cc2 = st.columns([4, 1])
                    with cc1:
                        st.markdown(
                            f"<span class='project-type-badge {child_badge}'>{child_type_info.get('short', 'VPA')}</span> "
                            f"**{child['name']}**",
                            unsafe_allow_html=True,
                        )
                    with cc2:
                        if st.button("Open", key=f"open_child_{child['id']}", use_container_width=True):
                            st.session_state.selected_project_id = child["id"]
                            st.rerun()
        if st.button("+ Add VPA", key=f"add_vpa_{project_id}"):
            st.session_state["show_new_project"] = True
            st.session_state["new_proj_type"] = "vpa_component"
            st.session_state["new_proj_step"] = 2
            st.session_state.selected_project_id = None
            st.rerun()

    BASE_TAB_LABELS = [
        "Setup",
        "Documents",
        "Parameters",
        "ER Simulator",
        "Write / Draft",
        "Review",
        "Audit",
        "Findings",
        "Lifecycle",
        "Monitoring",
        "Export",
    ]

    recommended_idx = _get_recommended_tab_index(project, project_id, total_params, missing_params, doc_count, projected_er, audit_score)
    tab_labels = []
    for i, label in enumerate(BASE_TAB_LABELS):
        if i == recommended_idx:
            tab_labels.append(f"{label} (Next)")
        else:
            tab_labels.append(label)

    tab_state_key = f"ws_tab_{project_id}"
    radio_key = f"tab_radio_{project_id}"

    if tab_state_key in st.session_state:
        pending_idx = st.session_state.pop(tab_state_key)
        if 0 <= pending_idx < len(tab_labels):
            st.session_state[radio_key] = tab_labels[pending_idx]

    if radio_key not in st.session_state:
        st.session_state[radio_key] = tab_labels[0]

    selected_label = st.radio(
        "Navigate to section",
        tab_labels,
        horizontal=True,
        key=radio_key,
        label_visibility="collapsed",
    )
    selected_idx = tab_labels.index(selected_label) if selected_label in tab_labels else 0

    TAB_RENDERERS = [
        _render_project_settings,
        _render_documents_tab,
        render_parameter_dashboard,
        render_er_simulator,
        _render_write_tab,
        _render_review_tab,
        render_audit_simulation,
        _render_findings_response_tab,
        render_lifecycle_dashboard,
        render_monitoring_dashboard,
        _render_export_tab,
    ]
    TAB_RENDERERS[selected_idx](project)


def _render_calculations_tab(project):
    project_id = project["id"]
    methodology = project.get("methodology")

    st.subheader("Emission Reduction Calculations")

    if not methodology:
        st.warning("Assign a methodology to this project in Project Settings before running calculations.")
        return

    st.write(f"Methodology: **{methodology}**")

    parse_key = f"parsed_methodology_{project_id}"
    calc_key = f"calc_result_{project_id}"

    if parse_key not in st.session_state:
        st.session_state[parse_key] = None
    if calc_key not in st.session_state:
        st.session_state[calc_key] = None

    if st.session_state[parse_key] is None:
        meth_data = _fetch(f"/projects/{project_id}/methodology-data")
        if meth_data and meth_data.get("status") == "ready":
            st.session_state[parse_key] = meth_data["parsed"]
            parsed_at = meth_data.get("parsed_at", "")
            if parsed_at:
                st.caption(f"Methodology pre-analyzed: {parsed_at[:19]}")

    parsed = st.session_state.get(parse_key)

    if not parsed:
        st.info("This methodology has not been analyzed yet. Click below to extract its calculation framework.")
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Analyze Methodology", key=f"parse_meth_{project_id}",
                          type="primary"):
                with st.spinner("Analyzing methodology (this may take 30-60 seconds)..."):
                    result = _fetch(
                        f"/projects/{project_id}/parse-methodology",
                        method="POST",
                        json={"methodology_code": methodology},
                    )
                    if result and not result.get("error"):
                        st.session_state[parse_key] = result
                        st.rerun()
                    else:
                        err = (result or {}).get("error", "Unknown error")
                        st.error(f"Failed to analyze methodology: {err}")
        return

    st.divider()

    methods = parsed.get("calculation_methods", [])
    if methods:
        st.markdown("**Calculation Methods Available:**")
        method_labels = []
        for m in methods:
            mid = m.get("method_id", "")
            mname = m.get("method_name", mid)
            label = mname if mname.lower().startswith("method") else f"{mid}: {mname}"
            method_labels.append(label)
        selected_method_idx = st.selectbox(
            "Select calculation method",
            range(len(method_labels)),
            format_func=lambda i: method_labels[i],
            key=f"calc_method_{project_id}",
        )
        selected_method = methods[selected_method_idx]

        if selected_method.get("applicability"):
            st.caption(f"Applicability: {selected_method['applicability']}")
        elif selected_method.get("description"):
            st.caption(selected_method["description"])

        if selected_method.get("scale_restrictions"):
            st.caption(f"Scale: {selected_method['scale_restrictions']}")

        if selected_method.get("equations"):
            with st.expander("View Equations", expanded=True):
                for eq in selected_method["equations"]:
                    eq_id = eq.get("equation_id", "")
                    eq_label = eq.get("equation_label", "")
                    header = f"**{eq_id}**" if eq_id else ""
                    if eq_label:
                        header += f" - {eq_label}" if header else f"**{eq_label}**"
                    if header:
                        st.markdown(header)
                    st.code(eq.get("formula_text", ""), language=None)
                    if eq.get("formula_description"):
                        st.caption(eq["formula_description"])
                    if eq.get("variables"):
                        var_text = ", ".join(
                            f"{v['symbol']} ({v.get('name', '')})"
                            for v in eq["variables"]
                        )
                        st.caption(f"Variables: {var_text}")
                    st.markdown("---")
    else:
        selected_method = None

    st.divider()

    all_params = parsed.get("parameters", [])
    method_id = selected_method["method_id"] if selected_method else None

    eq_var_symbols = set()
    if selected_method:
        for eq in selected_method.get("equations", []):
            for var in eq.get("variables", []):
                s = var.get("symbol") or ""
                if s:
                    eq_var_symbols.add(s)

    def _param_relevant(p):
        cat = p.get("category", "")
        if cat == "qualitative":
            return False
        role = p.get("equation_role", "")
        if role == "output":
            return False
        sym = p.get("symbol") or ""
        sym_base = sym.split("_")[0] if sym and "_" in sym else sym
        if sym and (sym in eq_var_symbols or sym_base in {s.split("_")[0] for s in eq_var_symbols if s}):
            return True
        applicable = p.get("applicable_methods", [])
        if not applicable or "all" in applicable:
            if role in ("input", "intermediate") or cat in ("monitored", "methodology_default", "project_input"):
                return True
        if applicable and method_id and method_id in applicable:
            return True
        return False

    relevant_params = [p for p in all_params if _param_relevant(p)]

    proj_settings = project.get("project_settings") or {}
    context_dims = parsed.get("context_dimensions", []) if parsed else []
    dim_keys = [d["dimension_key"] for d in context_dims]

    import hashlib as _hashlib
    import json as _json_mod
    settings_hash = _hashlib.md5(_json_mod.dumps(proj_settings, sort_keys=True).encode()).hexdigest()[:8]

    def _resolve_default(param):
        dbc = param.get("defaults_by_context", [])
        if not dbc:
            dn = param.get("default_numeric")
            if dn is not None:
                return str(dn)
            return ""
        selected_values = []
        for dk in dim_keys:
            val = proj_settings.get(dk, "")
            if val:
                selected_values.append(val.lower())
        if not selected_values:
            return str(dbc[0]["value"])
        best_match = None
        best_score = -1
        for entry in dbc:
            ck = entry.get("context_key", "").lower()
            score = sum(1 for sv in selected_values if sv in ck)
            if score > best_score:
                best_score = score
                best_match = entry
        if best_match and best_score > 0:
            return str(best_match["value"])
        return str(dbc[0]["value"])

    def _display_group(p):
        cat = p.get("category", "")
        dbc = p.get("defaults_by_context", [])
        dn = p.get("default_numeric")
        if cat == "methodology_default" or dbc or dn is not None:
            return "methodology_default"
        if cat in ("monitored", "calculated"):
            return "monitored"
        if cat == "project_input":
            return "project_input"
        return "monitored"

    group_order = ["methodology_default", "monitored", "project_input"]
    group_labels = {
        "methodology_default": "Methodology Defaults",
        "monitored": "Monitored / Field Data",
        "project_input": "Project-Specific Inputs",
    }
    group_captions = {
        "methodology_default": "Pre-filled from methodology based on your project settings. You can override any value.",
        "monitored": "Values from field surveys, monitoring, or project records. Enter your project data.",
        "project_input": "Project-specific values defined by the developer.",
    }

    user_inputs = {}

    for grp in group_order:
        grp_params = [p for p in relevant_params if _display_group(p) == grp]
        if not grp_params:
            continue

        st.markdown(f"**{group_labels.get(grp, grp)}:**")
        cap = group_captions.get(grp)
        if cap:
            st.caption(cap)

        for i, param in enumerate(grp_params):
            default_resolved = _resolve_default(param)
            sym = param.get("symbol") or ""
            unit = param.get("unit") or ""
            param_name = param.get("name") or param.get("parameter_id") or f"Parameter {i+1}"

            label = f"{sym} - {param_name}" if sym else param_name
            if unit and unit != "NA":
                label += f" [{unit}]"

            help_parts = []
            if param.get("source"):
                help_parts.append(f"Source: {param['source']}")
            dbc = param.get("defaults_by_context", [])
            if dbc:
                defaults_text = "; ".join(f"{d['context_key']}: {d['value']} {d.get('unit','')}" for d in dbc[:6])
                help_parts.append(f"Available defaults: {defaults_text}")
            elif param.get("default_value"):
                help_parts.append(f"Default: {param['default_value']}")
            if param.get("monitoring_frequency"):
                help_parts.append(f"Monitoring: {param['monitoring_frequency']}")
            help_text = " | ".join(help_parts) if help_parts else None

            param_key = param.get("parameter_id", f"p{i}").replace(" ", "_").replace(".", "_")
            widget_key = f"param_{project_id}_{settings_hash}_{param_key}"

            val = st.text_input(
                label,
                value=default_resolved,
                key=widget_key,
                help=help_text,
            )
            if val:
                user_inputs[sym] = val

        st.markdown("---")

    st.divider()

    crediting_years = project.get("crediting_period_years") or 7
    cp_start = project.get("crediting_period_start")
    if cp_start:
        st.caption(f"Crediting period: {str(cp_start)[:10]}, {crediting_years} years (set in Project Settings)")
    else:
        st.caption(f"Crediting period: {crediting_years} years (set start date in Project Settings for vintage labels)")

    if st.button("Run Calculation", key=f"run_calc_{project_id}",
                  type="primary"):
        if not user_inputs:
            st.warning("Please fill in at least some parameter values.")
            return

        with st.spinner("Running emission reduction calculation..."):
            result = _fetch(
                f"/projects/{project_id}/calculate",
                method="POST",
                json={
                    "method_id": method_id,
                    "crediting_years": crediting_years,
                    "user_inputs": user_inputs,
                },
            )
            if result and not result.get("error"):
                st.session_state[calc_key] = result
            else:
                err = (result or {}).get("error", "Calculation failed")
                st.error(f"Calculation failed: {err}")

    calc_result = st.session_state.get(calc_key)
    if calc_result and not calc_result.get("error"):
        st.divider()
        _render_calc_results(project, calc_result)


def _render_calc_results(project, calc_result):
    import pandas as pd

    project_id = project["id"]

    st.markdown("### Calculation Results")

    if calc_result.get("narrative_explanation"):
        with st.expander("Narrative Explanation", expanded=True):
            st.write(calc_result["narrative_explanation"])

    annual = calc_result.get("annual_calculations", [])
    if annual:
        df = pd.DataFrame(annual)
        display_cols = {
            "year": "Year",
            "baseline_emissions_tco2e": "Baseline (tCO2e)",
            "project_emissions_tco2e": "Project (tCO2e)",
            "leakage_tco2e": "Leakage (tCO2e)",
            "net_emission_reductions_tco2e": "Net ER (tCO2e)",
        }
        available = [c for c in display_cols if c in df.columns]
        df_display = df[available].rename(columns=display_cols)
        st.dataframe(df_display, width="stretch", hide_index=True)

        total = calc_result.get("total_emission_reductions_tco2e", 0)
        avg = calc_result.get("average_annual_reductions_tco2e", 0)

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Emission Reductions",
                       f"{total:,.0f} tCO2e")
        with col2:
            st.metric("Avg. Annual Reductions",
                       f"{avg:,.0f} tCO2e/yr")

        st.subheader("Emission Reductions by Year")
        chart_df = df_display.set_index("Year")[["Net ER (tCO2e)"]] if "Year" in df_display.columns else None
        if chart_df is not None:
            st.bar_chart(chart_df)

    if calc_result.get("parameters_used"):
        with st.expander("Parameters Used"):
            params_df = pd.DataFrame(calc_result["parameters_used"])
            st.dataframe(params_df, width="stretch", hide_index=True)

    if calc_result.get("assumptions"):
        with st.expander("Assumptions"):
            for a in calc_result["assumptions"]:
                st.write(f"- {a}")

    if calc_result.get("monitoring_parameters"):
        with st.expander("Monitoring Parameters"):
            mon_df = pd.DataFrame(calc_result["monitoring_parameters"])
            st.dataframe(mon_df, width="stretch", hide_index=True)

    st.divider()
    if st.button("Download Calculation Spreadsheet (Excel)",
                  key=f"download_calc_{project_id}",
                  type="primary"):
        with st.spinner("Generating Excel file..."):
            import io
            resp = requests.post(
                f"{API_BASE}/projects/{project_id}/export-calculation",
                json={"calculation_result": calc_result},
                timeout=30,
            )
            if resp.status_code == 200:
                st.download_button(
                    label="Save Excel File",
                    data=resp.content,
                    file_name=f"{project['name'][:30]}_calculations.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"save_calc_excel_{project_id}",
                )
            else:
                st.error("Failed to generate Excel file.")


def _render_findings_response_tab(project):
    project_id = project["id"]
    standard = project.get("standard", "GoldStandard")
    methodology = project.get("methodology", "")
    project_type = project.get("project_type", "standalone_pdd")

    st.markdown(f"""
    <span class="section-header">
        <span class="section-header-icon section-header-icon-amber">{SVG_ICONS.get("findings", "")}</span>
        <span class="section-header-text">Respond to Findings</span>
    </span>
    """, unsafe_allow_html=True)

    st.markdown(
        "Upload VVB findings or PRR comments, and the AI will draft responses "
        "based on your project data, methodology, and how similar findings were resolved on other projects."
    )

    response_tabs = st.tabs(["Enter Findings Manually", "Upload Findings Document", "Findings Intelligence"])

    with response_tabs[0]:
        _render_manual_finding_entry(project)

    with response_tabs[1]:
        _render_findings_upload(project)

    with response_tabs[2]:
        _render_findings_intelligence(project)


def _render_manual_finding_entry(project):
    project_id = project["id"]
    project_type = project.get("project_type", "standalone_pdd")

    default_doc_type_map = {
        "standalone_pdd": "pdd",
        "poa_programme": "poa_dd",
        "vpa_component": "vpa_dd",
        "monitoring_report": "mr",
        "valver_report": "valver",
    }
    default_dt = default_doc_type_map.get(project_type, "pdd")

    st.markdown("#### Enter a finding to get an AI-drafted response")

    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            finding_type = st.selectbox(
                "Finding type",
                ["CL", "CAR", "FAR", "prr_comment", "observation"],
                format_func=lambda x: {
                    "CL": "Clarification Request (CL)",
                    "CAR": "Corrective Action Request (CAR)",
                    "FAR": "Forward Action Request (FAR)",
                    "prr_comment": "PRR Comment (Verra/GS Review)",
                    "observation": "General Observation",
                }.get(x, x),
                key=f"finding_type_{project_id}",
            )
        with col2:
            pdd_section = st.text_input(
                "PDD/MR section reference",
                placeholder="e.g., 1.12, 2.1, 4.3, Monitoring Plan",
                key=f"finding_section_{project_id}",
            )
        with col3:
            doc_type = st.selectbox(
                "Document type",
                ["pdd", "mr", "poa_dd", "vpa_dd", "valver"],
                index=["pdd", "mr", "poa_dd", "vpa_dd", "valver"].index(default_dt),
                format_func=lambda x: {
                    "pdd": "PDD",
                    "mr": "Monitoring Report",
                    "poa_dd": "PoA-DD",
                    "vpa_dd": "VPA-DD",
                    "valver": "Validation/Verification Report",
                }.get(x, x),
                key=f"finding_doctype_{project_id}",
            )

        finding_text = st.text_area(
            "Finding / question text",
            height=150,
            placeholder="Paste the VVB's finding, clarification request, or PRR comment here...",
            key=f"finding_text_{project_id}",
        )

        if st.button("Generate Response", key=f"gen_response_{project_id}", type="primary", disabled=not finding_text):
            with st.spinner("Drafting response based on project data and past findings..."):
                try:
                    result = _fetch(
                        f"/projects/{project_id}/respond-to-finding",
                        method="POST",
                        json_data={
                            "finding_text": finding_text,
                            "finding_type": finding_type,
                            "pdd_section": pdd_section,
                            "doc_type": doc_type,
                        },
                    )
                    if result:
                        st.session_state[f"finding_response_{project_id}"] = result
                except Exception as e:
                    st.error(f"Failed to generate response: {e}")

    response = st.session_state.get(f"finding_response_{project_id}")
    if response:
        st.markdown("---")
        st.markdown("#### AI-Drafted Response")

        with st.container(border=True):
            approach = response.get("response_approach", "")
            approach_labels = {
                "pdd_update": "PDD Update Required",
                "clarification": "Clarification Only",
                "evidence_provided": "Evidence to Provide",
                "calculation_corrected": "Calculation Correction",
                "methodology_reference": "Methodology Reference",
            }
            if approach:
                st.markdown(f"**Approach:** {approach_labels.get(approach, approach)}")

            st.markdown("**Response:**")
            st.markdown(response.get("response_text", ""))

        pdd_updates = response.get("pdd_updates_needed", [])
        if pdd_updates:
            with st.container(border=True):
                st.markdown("**PDD Sections to Update:**")
                for update in pdd_updates:
                    section = update.get("section", "")
                    change = update.get("change_description", "")
                    st.markdown(f"- **Section {section}:** {change}")

        evidence = response.get("evidence_to_provide", [])
        if evidence:
            with st.container(border=True):
                st.markdown("**Evidence to Provide:**")
                for ev in evidence:
                    st.markdown(f"- {ev}")


def _render_findings_upload(project):
    project_id = project["id"]
    project_type = project.get("project_type", "standalone_pdd")

    default_doc_type_map = {
        "standalone_pdd": "pdd",
        "poa_programme": "poa_dd",
        "vpa_component": "vpa_dd",
        "monitoring_report": "mr",
        "valver_report": "valver",
    }
    default_dt = default_doc_type_map.get(project_type, "pdd")

    st.markdown("#### Upload a findings document")
    st.markdown(
        "Upload a VVB findings log, PRR comment sheet, or validation/verification report (PDF or Word). "
        "The AI will extract individual findings and draft responses for each."
    )

    uploaded = st.file_uploader(
        "Choose a findings document",
        type=["pdf", "docx"],
        key=f"findings_upload_{project_id}",
    )

    if uploaded:
        with st.container(border=True):
            fc1, fc2 = st.columns([2, 1])
            with fc1:
                st.markdown(f"**File:** {uploaded.name}")
                st.markdown(f"**Size:** {uploaded.size / 1024:.1f} KB")
            with fc2:
                doc_type_for_response = st.selectbox(
                    "Your document type",
                    ["pdd", "mr", "poa_dd", "vpa_dd", "valver"],
                    index=["pdd", "mr", "poa_dd", "vpa_dd", "valver"].index(default_dt),
                    format_func=lambda x: {
                        "pdd": "PDD",
                        "mr": "Monitoring Report",
                        "poa_dd": "PoA-DD",
                        "vpa_dd": "VPA-DD",
                        "valver": "Val/Ver Report",
                    }.get(x, x),
                    key=f"batch_doctype_{project_id}",
                )

            if st.button(
                "Extract Findings from Document",
                key=f"extract_findings_btn_{project_id}",
                type="primary",
            ):
                with st.spinner("Parsing document and extracting findings with AI..."):
                    try:
                        import requests
                        api_base = st.session_state.get("api_base", "http://localhost:3000")
                        files_payload = {"file": (uploaded.name, uploaded.getvalue())}
                        resp = requests.post(
                            f"{api_base}/projects/{project_id}/parse-findings-document",
                            files=files_payload,
                            timeout=120,
                        )
                        if resp.status_code == 200:
                            result = resp.json()
                            findings_list = result.get("findings", [])
                            st.session_state[f"extracted_findings_{project_id}"] = findings_list
                            st.session_state[f"extracted_doc_name_{project_id}"] = result.get("document_name", uploaded.name)
                            st.session_state[f"batch_doc_type_{project_id}"] = doc_type_for_response
                            st.session_state[f"selected_findings_{project_id}"] = [True] * len(findings_list)
                            st.session_state.pop(f"batch_responses_{project_id}", None)
                            chunks_failed = result.get("chunks_failed", 0)
                            msg = f"Extracted {result.get('total', 0)} findings from {result.get('chunks_processed', 1)} document section(s)."
                            if chunks_failed > 0:
                                msg += f" Warning: {chunks_failed} section(s) failed to process."
                            st.success(msg)
                            warnings = result.get("warnings", [])
                            if warnings:
                                for w in warnings[:3]:
                                    st.warning(w)
                            st.rerun()
                        else:
                            error_detail = resp.json().get("detail", resp.text) if resp.headers.get("content-type", "").startswith("application/json") else resp.text
                            st.error(f"Extraction failed: {error_detail}")
                    except Exception as e:
                        st.error(f"Failed to extract findings: {e}")

    extracted = st.session_state.get(f"extracted_findings_{project_id}", [])
    if extracted:
        doc_name = st.session_state.get(f"extracted_doc_name_{project_id}", "Document")
        st.markdown("---")
        st.markdown(f"#### Extracted Findings from {doc_name}")

        type_counts = {}
        for f in extracted:
            ft = f.get("finding_type", "unknown")
            type_counts[ft] = type_counts.get(ft, 0) + 1

        summary_parts = [f"{count} {ft}{'s' if count > 1 else ''}" for ft, count in sorted(type_counts.items())]
        st.markdown(f"**{len(extracted)} findings found:** " + ", ".join(summary_parts))

        selected_key = f"selected_findings_{project_id}"
        if selected_key not in st.session_state:
            st.session_state[selected_key] = [True] * len(extracted)

        sel_all_col, desel_col, _ = st.columns([1, 1, 3])
        with sel_all_col:
            if st.button("Select All", key=f"sel_all_{project_id}"):
                st.session_state[selected_key] = [True] * len(extracted)
                st.rerun()
        with desel_col:
            if st.button("Deselect All", key=f"desel_all_{project_id}"):
                st.session_state[selected_key] = [False] * len(extracted)
                st.rerun()

        for idx, finding in enumerate(extracted):
            ftype = finding.get("finding_type", "CL")
            fid = finding.get("finding_id", f"#{idx + 1}")
            topic = finding.get("topic", "")
            section = finding.get("pdd_section", "")
            desc = finding.get("description", "")

            with st.container(border=True):
                hc1, hc2 = st.columns([0.3, 4.7])
                with hc1:
                    checked = st.checkbox(
                        "Include",
                        value=st.session_state[selected_key][idx],
                        key=f"finding_check_{project_id}_{idx}",
                        label_visibility="collapsed",
                    )
                    st.session_state[selected_key][idx] = checked
                with hc2:
                    header_parts = [f"**{ftype} {fid}**"]
                    if topic:
                        header_parts.append(f"*{topic}*")
                    if section:
                        header_parts.append(f"(Section {section})")
                    st.markdown(" -- ".join(header_parts))
                    if desc:
                        preview = desc[:300] + ("..." if len(desc) > 300 else "")
                        st.caption(preview)

        selected_count = sum(st.session_state.get(selected_key, []))
        st.markdown(f"**{selected_count} of {len(extracted)} findings selected for response generation**")

        bc1, bc2 = st.columns([1, 2])
        with bc1:
            if st.button(
                f"Generate Responses ({selected_count})",
                key=f"batch_respond_btn_{project_id}",
                type="primary",
                disabled=selected_count == 0,
            ):
                selected_findings = [
                    f for i, f in enumerate(extracted)
                    if st.session_state.get(selected_key, [])[i]
                ]
                batch_dt = st.session_state.get(f"batch_doc_type_{project_id}", default_dt)

                progress_bar = st.progress(0, text="Generating responses...")
                try:
                    result = _fetch(
                        f"/projects/{project_id}/batch-respond-to-findings",
                        method="POST",
                        json_data={
                            "findings": selected_findings,
                            "doc_type": batch_dt,
                        },
                    )
                    if result:
                        st.session_state[f"batch_responses_{project_id}"] = result
                        progress_bar.progress(100, text="All responses generated.")
                        st.rerun()
                except Exception as e:
                    st.error(f"Batch response generation failed: {e}")
                    progress_bar.empty()
        with bc2:
            if st.button("Clear Extracted Findings", key=f"clear_findings_{project_id}"):
                st.session_state.pop(f"extracted_findings_{project_id}", None)
                st.session_state.pop(f"extracted_doc_name_{project_id}", None)
                st.session_state.pop(selected_key, None)
                st.session_state.pop(f"batch_responses_{project_id}", None)
                st.rerun()

    batch_result = st.session_state.get(f"batch_responses_{project_id}")
    if batch_result:
        responses = batch_result.get("responses", [])
        successful = batch_result.get("successful", 0)
        failed = batch_result.get("failed", 0)

        st.markdown("---")
        st.markdown("#### AI-Drafted Responses")
        st.markdown(f"**{successful} successful**, **{failed} failed** out of {batch_result.get('total', 0)} findings")

        for resp in responses:
            fid = resp.get("finding_id", "")
            ftype = resp.get("finding_type", "CL")
            status = resp.get("status", "error")

            with st.container(border=True):
                rc1, rc2, rc3 = st.columns([1.5, 1, 0.5])
                with rc1:
                    st.markdown(f"**{ftype} {fid}**")
                    if resp.get("topic"):
                        st.caption(resp["topic"])
                with rc2:
                    approach = resp.get("response_approach", "")
                    approach_labels = {
                        "pdd_update": "PDD Update Required",
                        "clarification": "Clarification Only",
                        "evidence_provided": "Evidence to Provide",
                        "calculation_corrected": "Calculation Correction",
                        "methodology_reference": "Methodology Reference",
                    }
                    if approach:
                        st.markdown(approach_labels.get(approach, approach))
                with rc3:
                    if status == "success":
                        st.markdown(":green[OK]")
                    else:
                        st.markdown(":red[Failed]")

                if status == "success":
                    with st.expander("View Finding"):
                        st.markdown(resp.get("finding_text", ""))

                    st.markdown("**Response:**")
                    st.markdown(resp.get("response_text", ""))

                    pdd_updates = resp.get("pdd_updates_needed", [])
                    if pdd_updates:
                        st.markdown("**PDD Updates Needed:**")
                        for upd in pdd_updates:
                            st.markdown(f"- **Section {upd.get('section', '')}:** {upd.get('change_description', '')}")

                    evidence = resp.get("evidence_to_provide", [])
                    if evidence:
                        st.markdown("**Evidence to Provide:**")
                        for ev in evidence:
                            st.markdown(f"- {ev}")
                else:
                    st.error(f"Failed: {resp.get('error', 'Unknown error')}")

        _render_batch_export(project_id, responses)


def _render_batch_export(project_id, responses):
    successful = [r for r in responses if r.get("status") == "success"]
    if not successful:
        return

    st.markdown("---")
    st.markdown("#### Export Responses")

    export_col1, export_col2 = st.columns(2)
    with export_col1:
        if st.button("Copy All Responses as Text", key=f"copy_responses_{project_id}"):
            text_output = ""
            for r in successful:
                text_output += f"{'=' * 60}\n"
                text_output += f"{r.get('finding_type', 'CL')} {r.get('finding_id', '')}\n"
                text_output += f"Topic: {r.get('topic', '')}\n"
                text_output += f"Section: {r.get('pdd_section', '')}\n"
                text_output += f"{'=' * 60}\n\n"
                text_output += f"FINDING:\n{r.get('finding_text', '')}\n\n"
                text_output += f"RESPONSE:\n{r.get('response_text', '')}\n\n"
                updates = r.get("pdd_updates_needed", [])
                if updates:
                    text_output += "PDD UPDATES NEEDED:\n"
                    for u in updates:
                        text_output += f"  - Section {u.get('section', '')}: {u.get('change_description', '')}\n"
                    text_output += "\n"
                evidence = r.get("evidence_to_provide", [])
                if evidence:
                    text_output += "EVIDENCE TO PROVIDE:\n"
                    for e in evidence:
                        text_output += f"  - {e}\n"
                    text_output += "\n"
                text_output += "\n"
            st.text_area(
                "Response text (select all and copy)",
                value=text_output,
                height=300,
                key=f"responses_text_{project_id}",
            )

    with export_col2:
        try:
            import io
            import csv
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow([
                "Finding ID", "Type", "Section", "Topic", "Finding Text",
                "Response", "Approach", "PDD Updates", "Evidence"
            ])
            for r in successful:
                updates_str = "; ".join(
                    f"Section {u.get('section', '')}: {u.get('change_description', '')}"
                    for u in r.get("pdd_updates_needed", [])
                )
                evidence_str = "; ".join(r.get("evidence_to_provide", []))
                approach_labels = {
                    "pdd_update": "PDD Update",
                    "clarification": "Clarification",
                    "evidence_provided": "Evidence",
                    "calculation_corrected": "Calculation Fix",
                    "methodology_reference": "Methodology Ref",
                }
                writer.writerow([
                    r.get("finding_id", ""),
                    r.get("finding_type", ""),
                    r.get("pdd_section", ""),
                    r.get("topic", ""),
                    r.get("finding_text", ""),
                    r.get("response_text", ""),
                    approach_labels.get(r.get("response_approach", ""), r.get("response_approach", "")),
                    updates_str,
                    evidence_str,
                ])
            csv_bytes = buf.getvalue().encode("utf-8")
            st.download_button(
                "Download Responses as CSV",
                data=csv_bytes,
                file_name=f"findings_responses_project_{project_id}.csv",
                mime="text/csv",
                key=f"download_csv_{project_id}",
            )
        except Exception as e:
            st.warning(f"CSV export error: {e}")


def _render_findings_intelligence(project):
    project_id = project["id"]
    methodology = project.get("methodology", "")

    st.markdown("#### Findings Intelligence")
    st.markdown(
        "View common VVB findings patterns for your methodology. "
        "These patterns are extracted from real validation and verification reports."
    )

    if not methodology:
        st.info("Select a methodology in Project Setup to see findings intelligence.")
        return

    try:
        stats = _fetch("/admin/findings/stats")
    except Exception:
        stats = None

    if not stats or stats.get("total", 0) == 0:
        with st.container(border=True):
            st.markdown("**No findings data available yet.**")
            st.markdown(
                "The findings knowledge base needs to be populated by extracting findings from "
                "validation and verification reports. This can be triggered from the admin panel."
            )
        return

    total = stats.get("total", 0)
    by_meth = stats.get("by_methodology", {})
    top_topics = stats.get("top_topics", [])

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Findings in Knowledge Base", total)
    with col2:
        meth_findings = by_meth.get(methodology, {})
        meth_total = sum(meth_findings.values()) if meth_findings else 0
        st.metric(f"Findings for {methodology}", meth_total)

    if meth_findings:
        with st.container(border=True):
            st.markdown(f"**Findings breakdown for {methodology}:**")
            for ftype, count in sorted(meth_findings.items()):
                label = {
                    "CAR": "Corrective Action Requests",
                    "CL": "Clarification Requests",
                    "FAR": "Forward Action Requests",
                    "observation": "Observations",
                    "prr_comment": "PRR Comments",
                }.get(ftype, ftype)
                st.markdown(f"- {label}: **{count}**")

    if top_topics:
        with st.container(border=True):
            st.markdown("**Most common finding topics (all methodologies):**")
            for item in top_topics[:10]:
                st.markdown(f"- {item['topic']}: {item['count']} findings")

    try:
        findings = _fetch(f"/admin/findings/{methodology}?limit=20")
    except Exception:
        findings = []

    if findings:
        st.markdown(f"#### Recent findings for {methodology}")
        for f in findings[:10]:
            ftype = f.get("finding_type", "CL")
            topic = f.get("topic", "")
            severity = f.get("severity", "medium")
            desc = f.get("description", "")[:300]
            resolution = f.get("resolution", "")

            severity_color = {
                "critical": "red", "high": "orange",
                "medium": "blue", "low": "gray",
            }.get(severity, "gray")

            with st.container(border=True):
                hcol1, hcol2, hcol3 = st.columns([1, 2, 1])
                with hcol1:
                    st.markdown(f"**{ftype}**")
                with hcol2:
                    st.markdown(f"*{topic}*" if topic else "")
                with hcol3:
                    st.markdown(f"Severity: {severity}")

                st.markdown(desc)
                if resolution:
                    with st.expander("Resolution"):
                        st.markdown(resolution[:500])


def _render_export_tab(project):
    project_id = project["id"]
    standard = project.get("standard", "GoldStandard")
    methodology = project.get("methodology")

    st.markdown(f"""
    <span class="section-header">
        <span class="section-header-icon section-header-icon-green">{SVG_ICONS.get("export", "")}</span>
        <span class="section-header-text">Export Documents</span>
    </span>
    """, unsafe_allow_html=True)
    st.write("Generate filled templates with your drafted content, or download calculation spreadsheets.")

    st.markdown("### Template Export")
    st.write("Export a Word document with all your drafted sections filled into the standard template structure.")

    project_type = project.get("project_type", "standalone_pdd")
    available_types = DOC_TYPES_FOR_STANDARD.get(standard, {"pdd": "PDD", "mr": "MR"})

    default_dt = PROJECT_TYPE_INFO.get(project_type, {}).get("default_doc_type", "pdd")
    type_keys = list(available_types.keys())
    default_idx = type_keys.index(default_dt) if default_dt in type_keys else 0

    selected_doc_type = st.selectbox(
        "Document type to export",
        type_keys,
        index=default_idx,
        format_func=lambda x: available_types[x],
        key=f"export_doc_type_{project_id}",
    )

    write_sessions = _fetch(f"/projects/{project_id}/write-sessions?doc_type={selected_doc_type}")
    session_count = len(write_sessions) if write_sessions else 0

    if session_count > 0:
        st.info(f"{session_count} section(s) have been drafted using the AI Writer. These will be included in the template.")
    else:
        st.warning("No sections have been drafted yet. Use the Write / Draft tab to generate content before exporting.")

    calc_key = f"calc_result_{project_id}"
    has_calc = calc_key in st.session_state and st.session_state[calc_key] is not None
    include_calc = False
    if has_calc:
        include_calc = st.checkbox(
            "Include calculation results in the document",
            value=True,
            key=f"include_calc_{project_id}",
        )

    if st.button("Generate Template Document",
                  key=f"gen_template_{project_id}",
                  type="primary"):
        with st.spinner("Generating filled template document..."):
            payload = {
                "doc_type": selected_doc_type,
                "include_calculations": include_calc,
            }
            if include_calc and has_calc:
                payload["calculation_result"] = st.session_state[calc_key]
            resp = requests.post(
                f"{API_BASE}/projects/{project_id}/generate-template",
                json=payload,
                timeout=60,
            )
            if resp.status_code == 200:
                doc_label = available_types.get(selected_doc_type, selected_doc_type)
                safe_name = project["name"].replace(" ", "_")[:30]
                filename = f"{safe_name}_{selected_doc_type.upper()}.docx"
                st.download_button(
                    label=f"Save {doc_label}",
                    data=resp.content,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"save_template_{project_id}",
                )
                st.success("Template generated successfully.")
            else:
                detail = ""
                try:
                    detail = resp.json().get("detail", "")
                except Exception:
                    pass
                st.error(f"Failed to generate template. {detail}")

    st.divider()
    st.markdown("### ER Calculation Spreadsheet")
    st.write(
        "Generate an audit-proof multi-sheet Excel workbook. "
        "Ex-ante (PDD / VPA-DD) produces a projected crediting-period workbook. "
        "Ex-post (MR) produces a monitoring-period workbook with vintage allocation and deviation log."
    )

    er_doc_types = {k: v for k, v in available_types.items() if k in ("pdd", "vpa_dd", "poa_dd", "mr")}
    if not er_doc_types:
        er_doc_types = {"pdd": "PDD (ex-ante)"}

    er_doc_keys = list(er_doc_types.keys())
    er_default_key = default_dt if default_dt in er_doc_keys else er_doc_keys[0]
    er_selected = st.selectbox(
        "Workbook type",
        er_doc_keys,
        index=er_doc_keys.index(er_default_key),
        format_func=lambda x: {
            "pdd": "PDD — Ex-ante (crediting period projection)",
            "vpa_dd": "VPA-DD — Ex-ante (crediting period projection)",
            "poa_dd": "PoA-DD — Ex-ante (crediting period projection)",
            "mr": "MR — Ex-post (monitoring period, verified ERs)",
        }.get(x, er_doc_types[x]),
        key=f"er_workbook_type_{project_id}",
    )

    if has_calc:
        calc_result_for_export = st.session_state[calc_key]
        total_er = (
            calc_result_for_export.get("total_emission_reductions_tco2e")
            or calc_result_for_export.get("summary", {}).get("total_er")
            or 0
        )
        st.caption(f"Calculation in session: {total_er:,.0f} tCO2e — will be included in the workbook.")
    else:
        calc_result_for_export = {}
        st.caption(
            "No calculation in session. The workbook will use parameter defaults from your project setup. "
            "Run a calculation in the ER Simulator tab first for richer output."
        )

    if st.button(
        "Generate ER Workbook",
        key=f"export_er_workbook_{project_id}",
        type="primary",
    ):
        with st.spinner("Building workbook..."):
            resp = requests.post(
                f"{API_BASE}/projects/{project_id}/export-calculation",
                json={
                    "calculation_result": calc_result_for_export,
                    "doc_type": er_selected,
                },
                timeout=60,
            )
            if resp.status_code == 200:
                doc_suffix = "ExPost" if er_selected == "mr" else "ExAnte"
                safe_name = project["name"].replace(" ", "_")[:30]
                st.download_button(
                    label=f"Save {doc_suffix} ER Workbook (.xlsx)",
                    data=resp.content,
                    file_name=f"{safe_name}_ER_{doc_suffix}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"save_er_workbook_{project_id}",
                )
                st.success(
                    "Workbook ready. It contains: Cover, Parameters, ER Calculation, "
                    + ("Vintage Allocation, Data Quality, Deviation Log."
                       if er_selected == "mr"
                       else "Vintage Table, Sensitivity Analysis.")
                )
            else:
                try:
                    detail = resp.json().get("detail", "")
                except Exception:
                    detail = ""
                st.error(f"Failed to generate workbook. {detail}")

    st.divider()
    st.markdown("### Methodology Reference")
    if methodology:
        meth_detail = _fetch(f"/projects/methodologies/{methodology}")
        if meth_detail:
            with st.container(border=True):
                st.markdown(f"**{meth_detail.get('code', '')}** - {meth_detail.get('name', '')}")
                if meth_detail.get("standard"):
                    st.caption(f"Standard: {meth_detail['standard']}")
                if meth_detail.get("applicability"):
                    st.caption(f"Applicability: {meth_detail['applicability'][:300]}")
    else:
        st.caption("No methodology assigned to this project.")


def _render_documents_tab(project):
    project_id = project["id"]
    project_type = project.get("project_type", "standalone_pdd")

    st.markdown(f"""
    <span class="section-header">
        <span class="section-header-icon section-header-icon-blue">{SVG_ICONS.get("docs", "")}</span>
        <span class="section-header-text">Documents & Knowledge Base</span>
    </span>
    """, unsafe_allow_html=True)
    st.write("Upload project documents. Toggle which ones the AI uses when writing and reviewing your documents.")

    documents = project.get("documents", [])

    if not documents:
        _render_document_prompts(project_type)

    standard = project.get("standard", "GoldStandard")
    available_doc_types = list(DOC_TYPES_FOR_STANDARD.get(standard, {}).keys())
    upload_types = available_doc_types + ["reference", "research", "field_data", "other"]

    with st.container(border=True):
        st.markdown("#### Upload Document")
        upload_col1, upload_col2 = st.columns(2)
        with upload_col1:
            upload_file = st.file_uploader("Choose a file", type=["docx", "pdf"], key=f"upload_{project_id}")
        with upload_col2:
            doc_type = st.selectbox(
                "Document type",
                upload_types,
                format_func=lambda x: PROJECT_DOC_TYPES.get(x, x),
                key=f"upload_type_{project_id}",
            )
            upload_notes = st.text_input("Notes (optional)", key=f"upload_notes_{project_id}")

        if st.button("Upload", key=f"upload_btn_{project_id}", type="primary", disabled=not upload_file):
            if upload_file:
                files = {"file": (upload_file.name, upload_file.getvalue())}
                data = {"doc_type": doc_type}
                if upload_notes:
                    data["notes"] = upload_notes
                result = _fetch(
                    f"/projects/{project_id}/documents",
                    method="POST",
                    files=files,
                    data=data,
                )
                if result:
                    parsed = "parsed" if result.get("parsed") else "uploaded"
                    st.success(f"Document uploaded and {parsed} successfully.")
                    time.sleep(0.5)
                    st.rerun()

    if project.get("parent_project_id"):
        parent = _fetch(f"/projects/{project['parent_project_id']}")
        if parent and parent.get("documents"):
            parent_type_info = PROJECT_TYPE_INFO.get(parent.get("project_type", ""), {})
            parent_label = parent_type_info.get("short", "Parent")
            with st.container(border=True):
                st.markdown(f"#### Documents from {parent_label}: {parent['name']}")
                st.caption("These documents are automatically available as AI context.")
                for pdoc in parent.get("documents", []):
                    if pdoc.get("parsed_text"):
                        doc_type_label = PROJECT_DOC_TYPES.get(pdoc["doc_type"], pdoc["doc_type"])
                        st.markdown(f"- **{pdoc['file_name']}** ({doc_type_label})")

    if documents:
        core_docs = [d for d in documents if d.get("doc_type") in ("pdd", "mr", "valver", "poa_dd", "vpa_dd")]
        support_docs = [d for d in documents if d.get("doc_type") in ("reference", "research", "field_data")]
        other_docs = [d for d in documents if d.get("doc_type") in ("template", "other")]

        if core_docs:
            st.markdown("#### Core Documents")
            for doc in core_docs:
                _render_document_card(project_id, doc)

        if support_docs:
            st.markdown("#### Supporting Evidence")
            st.caption("KPT reports, field data, feasibility studies, and other supporting materials")
            for doc in support_docs:
                _render_document_card(project_id, doc)

        if other_docs:
            st.markdown("#### Other Documents")
            for doc in other_docs:
                _render_document_card(project_id, doc)

        ai_context_count = sum(1 for d in documents if d.get("use_as_ai_context", True) and d.get("parsed_text"))
        if ai_context_count > 0:
            st.info(f"{ai_context_count} document{'s' if ai_context_count != 1 else ''} active as AI context")
    elif not documents:
        pass

    _render_pending_evidence_review(project_id)

    _render_intelligence_review(project_id)


def _render_pending_evidence_review(project_id):
    pending_data = _fetch(f"/projects/{project_id}/evidence/pending")
    if not pending_data:
        return
    pending = pending_data.get("pending", [])
    if not pending:
        return

    st.markdown("---")
    st.markdown(f"#### Pending Evidence Review ({len(pending)} item{'s' if len(pending) != 1 else ''})")
    st.caption("Parameter values extracted from documents. Review and decide on each item.")

    for item in pending:
        link_id = item["id"]
        pk = item.get("param_key", "")
        param_name = item.get("param_name") or item.get("target_description") or pk
        current_val = item.get("current_param_value", "")
        param_status = item.get("param_status", "")
        extracted_val = item.get("extracted_value", "")
        extracted_unit = item.get("extracted_unit", "")
        quote = item.get("quote", "")
        doc_name = item.get("doc_file_name") or item.get("source_title", "")
        section = item.get("source_detail", "")
        confidence = item.get("confidence", 0)

        with st.container(border=True):
            pc1, pc2 = st.columns([3, 2])
            with pc1:
                st.markdown(f"**{param_name}** (`{pk}`)")
                current_display = current_val if current_val else "not set"
                st.caption(f"Current: {current_display} | Extracted: {extracted_val} {extracted_unit}")
                if quote:
                    st.caption(f"Source: \"{quote}\"")
                if doc_name:
                    loc = f" -- {section}" if section else ""
                    st.caption(f"From: {doc_name}{loc} (confidence: {confidence:.0%})")
            with pc2:
                bc1, bc2, bc3 = st.columns(3)
                with bc1:
                    if st.button("Accept & Apply", key=f"ev_accept_{link_id}", type="primary"):
                        result = _fetch(
                            f"/projects/{project_id}/evidence/{link_id}/decide",
                            method="POST",
                            json={"decision": "accepted"},
                        )
                        if result and result.get("requires_confirmation"):
                            st.session_state[f"ev_confirm_{link_id}"] = result
                        elif result and result.get("success"):
                            st.success(f"Applied: {pk} = {extracted_val}")
                            time.sleep(0.5)
                            st.rerun()
                        elif result and result.get("error"):
                            st.error(result["error"])

                with bc2:
                    if st.button("As Reference", key=f"ev_ref_{link_id}"):
                        result = _fetch(
                            f"/projects/{project_id}/evidence/{link_id}/decide",
                            method="POST",
                            json={"decision": "accepted_as_reference"},
                        )
                        if result and result.get("success"):
                            st.info("Recorded as reference")
                            time.sleep(0.5)
                            st.rerun()

                with bc3:
                    if st.button("Reject", key=f"ev_reject_{link_id}"):
                        result = _fetch(
                            f"/projects/{project_id}/evidence/{link_id}/decide",
                            method="POST",
                            json={"decision": "rejected"},
                        )
                        if result and result.get("success"):
                            st.info("Rejected")
                            time.sleep(0.5)
                            st.rerun()

            confirm_state = st.session_state.get(f"ev_confirm_{link_id}")
            if confirm_state:
                st.warning(confirm_state.get("message", "This will overwrite a confirmed parameter value."))
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("Confirm overwrite", key=f"ev_force_{link_id}", type="primary"):
                        result = _fetch(
                            f"/projects/{project_id}/evidence/{link_id}/decide",
                            method="POST",
                            json={"decision": "accepted", "force": True},
                        )
                        if result and result.get("success"):
                            del st.session_state[f"ev_confirm_{link_id}"]
                            st.success(f"Applied: {pk} = {extracted_val}")
                            time.sleep(0.5)
                            st.rerun()
                with cc2:
                    if st.button("Cancel", key=f"ev_cancel_{link_id}"):
                        del st.session_state[f"ev_confirm_{link_id}"]
                        st.rerun()


def _render_intelligence_review(project_id):
    suggestions_data = _fetch(f"/projects/{project_id}/intelligence-suggestions")
    if not suggestions_data:
        return
    suggestions = suggestions_data.get("suggestions", [])
    total = suggestions_data.get("total_count", 0)
    if total == 0:
        return

    st.markdown("---")
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
        <span style="font-size:1.15rem;font-weight:600;color:var(--text-primary, #1a1a2e);">Intelligence Review</span>
        <span style="background:var(--brand-primary, #0d9488);color:#fff;font-size:0.75rem;font-weight:600;
              padding:2px 10px;border-radius:12px;">{total} suggestion{'s' if total != 1 else ''}</span>
    </div>
    <p style="color:var(--text-secondary, #6b7280);font-size:0.85rem;margin-bottom:12px;">
        Data points extracted from your documents. Confirm to populate your Project Setup, or dismiss to hide.
    </p>
    """, unsafe_allow_html=True)

    for cat_group in suggestions:
        cat = cat_group["category"]
        cat_label = cat_group["category_label"]
        fields = cat_group["fields"]
        count = cat_group["count"]

        with st.expander(f"{cat_label} — {count} data point{'s' if count != 1 else ''}", expanded=False):
            confirm_all_items = []

            for field in fields:
                fkey = field["field_key"]
                label = field["label"]
                values = field["values"]
                current = field.get("current_value", "")

                best_value = values[0] if values else {}
                val = best_value.get("value", "")
                confidence = best_value.get("confidence", "medium")
                source = best_value.get("source", "")

                conf_colors = {"high": "#059669", "medium": "#d97706", "low": "#9ca3af"}
                conf_color = conf_colors.get(confidence, "#9ca3af")

                has_conflict = len(values) > 1
                has_current = bool(current.strip()) if current else False

                with st.container(border=True):
                    fc1, fc2, fc3 = st.columns([3, 1.5, 1])
                    with fc1:
                        st.markdown(f"**{label}**")
                        if has_conflict:
                            for i, v in enumerate(values):
                                src = v.get("source", "")
                                st.markdown(f"""<div style="font-size:0.85rem;margin:2px 0;">
                                    <span style="color:var(--text-primary, #1a1a2e);">{v['value']}</span>
                                    <span style="color:#9ca3af;font-size:0.75rem;margin-left:6px;">from {src}</span>
                                </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown(f"""<div style="font-size:0.9rem;">
                                <span style="color:var(--text-primary, #1a1a2e);">{val}</span>
                                <span style="color:{conf_color};font-size:0.7rem;font-weight:500;margin-left:8px;
                                      text-transform:uppercase;">{confidence}</span>
                            </div>""", unsafe_allow_html=True)
                            if source:
                                st.markdown(f'<span style="color:#9ca3af;font-size:0.75rem;">from {source}</span>', unsafe_allow_html=True)

                    with fc2:
                        if has_current:
                            st.markdown(f"""<div style="font-size:0.8rem;">
                                <span style="color:#9ca3af;">Current:</span>
                                <span style="color:var(--text-secondary, #6b7280);font-weight:500;">{current}</span>
                            </div>""", unsafe_allow_html=True)

                    with fc3:
                        confirm_label = "Replace" if has_current else "Confirm"
                        bc1, bc2 = st.columns(2)
                        with bc1:
                            if st.button(confirm_label, key=f"intel_confirm_{cat}_{fkey}_{project_id}", type="primary", use_container_width=True):
                                result = _fetch(
                                    f"/projects/{project_id}/intelligence-confirm",
                                    method="POST",
                                    json={"items": [{"category": cat, "field_key": fkey, "value": val, "source": source, "force": has_current}]},
                                )
                                if result:
                                    st.success(f"Updated: {label}")
                                    time.sleep(0.5)
                                    st.rerun()
                        with bc2:
                            if st.button("Dismiss", key=f"intel_dismiss_{cat}_{fkey}_{project_id}", use_container_width=True):
                                _fetch(
                                    f"/projects/{project_id}/intelligence-dismiss",
                                    method="POST",
                                    json={"items": [{"category": cat, "field_key": fkey}]},
                                )
                                time.sleep(0.3)
                                st.rerun()

                confirm_all_items.append({"category": cat, "field_key": fkey, "value": val, "source": source})

            if len(confirm_all_items) > 1:
                if st.button(f"Confirm all {cat_label}", key=f"intel_confirm_all_{cat}_{project_id}", type="primary"):
                    result = _fetch(
                        f"/projects/{project_id}/intelligence-confirm",
                        method="POST",
                        json={"items": confirm_all_items},
                    )
                    if result:
                        st.success(result.get("message", "Fields updated."))
                        time.sleep(0.5)
                        st.rerun()


def _render_document_card(project_id, doc):
    doc_type_label = PROJECT_DOC_TYPES.get(doc["doc_type"], doc["doc_type"])
    status_label = doc.get("status", "uploaded")
    use_ai = doc.get("use_as_ai_context", True)
    parsed_text = doc.get("parsed_text") or ""
    has_parsed = bool(parsed_text.strip())

    with st.container(border=True):
        dc1, dc2, dc3, dc4, dc5 = st.columns([3, 1.2, 0.8, 0.8, 0.5])
        with dc1:
            st.markdown(f"**{doc['file_name']}**")
            meta_parts = [doc_type_label]
            if has_parsed:
                char_count = len(parsed_text)
                word_count = len(parsed_text.split())
                if char_count > 1000:
                    meta_parts.append(f"{word_count:,} words extracted")
                else:
                    meta_parts.append(f"{char_count} chars extracted")
            st.caption(" | ".join(meta_parts))
        with dc2:
            status_display = {"parsed": "Parsed", "reviewed": "Reviewed", "uploaded": "Uploaded", "draft_generated": "Generated"}.get(status_label, status_label)
            st.caption(f"Status: {status_display}")
            if doc.get("notes"):
                st.caption(f"Notes: {doc['notes']}")
        with dc3:
            size = doc.get("file_size_bytes", 0) or 0
            if size > 1024 * 1024:
                st.caption(f"{size / 1024 / 1024:.1f} MB")
            elif size > 1024:
                st.caption(f"{size / 1024:.0f} KB")
        with dc4:
            toggle_label = "AI Context" if has_parsed else "Not parsed"
            new_val = st.checkbox(
                toggle_label,
                value=use_ai and has_parsed,
                key=f"ai_ctx_{doc['id']}",
                disabled=not has_parsed,
                help="Toggle whether the AI writer/reviewer uses this document as context",
            )
            if new_val != use_ai and has_parsed:
                _fetch(
                    f"/projects/{project_id}/documents/{doc['id']}/ai-context?use_as_ai_context={str(new_val).lower()}",
                    method="PATCH",
                )
                st.rerun()
        with dc5:
            if st.button("X", key=f"del_doc_{doc['id']}", help="Delete document"):
                _fetch(f"/projects/{project_id}/documents/{doc['id']}", method="DELETE")
                time.sleep(0.3)
                st.rerun()

        ai_summary = doc.get("ai_extracted_summary") or ""
        if ai_summary.strip():
            with st.expander("Extracted intelligence", expanded=False):
                st.markdown(ai_summary)
        elif has_parsed:
            ec1, ec2 = st.columns([4, 1])
            with ec1:
                with st.expander("Preview extracted text", expanded=False):
                    preview = parsed_text[:3000]
                    if len(parsed_text) > 3000:
                        preview += f"\n\n... ({len(parsed_text) - 3000:,} more characters)"
                    st.text(preview)
            with ec2:
                if st.button("Extract intelligence", key=f"extract_intel_{doc['id']}", help="Run AI to extract key data points from this document"):
                    with st.spinner("Extracting intelligence (this may take 15-30 seconds)..."):
                        result = _fetch(
                            f"/projects/{project_id}/documents/{doc['id']}/extract-intelligence",
                            method="POST",
                            timeout=120,
                        )
                        if result and result.get("summary"):
                            st.success("Intelligence extracted.")
                            time.sleep(0.5)
                            st.rerun()
                        elif result:
                            st.warning("Extraction completed but returned no data.")

        if has_parsed:
            if st.button("Extract parameter evidence", key=f"extract_evidence_{doc['id']}", help="Extract parameter values from this document for review"):
                with st.spinner("Extracting parameter evidence..."):
                    result = _fetch(
                        f"/projects/{project_id}/documents/{doc['id']}/extract-evidence",
                        method="POST",
                        timeout=120,
                    )
                    if result and result.get("extracted", 0) > 0:
                        st.success(f"Found {result['extracted']} parameter value{'s' if result['extracted'] != 1 else ''} for review.")
                        time.sleep(0.5)
                        st.rerun()
                    elif result and result.get("extracted", 0) == 0:
                        st.info("No new parameter values found in this document.")
                    else:
                        st.warning("Extraction failed. Check that parameters are initialized.")


def _render_document_prompts(project_type):
    prompts = {
        "standalone_pdd": {
            "title": "Recommended documents for your PDD",
            "items": [
                "KPT (Kitchen Performance Test) report",
                "Baseline study or survey data",
                "Feasibility study",
                "Stakeholder consultation report",
                "Technical specifications / test certificates",
            ],
        },
        "poa_programme": {
            "title": "Recommended documents for your PoA-DD",
            "items": [
                "Programme concept document",
                "CME organizational details",
                "Eligibility criteria documentation",
                "Methodology document",
            ],
        },
        "vpa_component": {
            "title": "Recommended documents for your VPA-DD",
            "items": [
                "Parent PoA-DD document (will be used for eligibility criteria context)",
                "VPA-specific KPT or field test reports",
                "Local baseline data",
                "VPA location documentation",
            ],
        },
        "monitoring_report": {
            "title": "Recommended documents for your Monitoring Report",
            "items": [
                "PDD (critical - the AI will reference your baseline, methodology, and monitoring plan)",
                "Previous Monitoring Reports (for consistency)",
                "Monitoring data spreadsheets",
                "Field visit reports",
                "Survey or sampling data",
            ],
        },
        "valver_report": {
            "title": "Recommended documents for your ValVer Report",
            "items": [
                "PDD or Project Description being validated/verified",
                "Monitoring Report (if verification)",
                "Field visit notes",
                "Interview records",
            ],
        },
    }
    prompt_data = prompts.get(project_type, prompts["standalone_pdd"])
    with st.container(border=True):
        st.markdown(f"#### {prompt_data['title']}")
        st.caption("Upload these documents to give the AI better context for writing and reviewing.")
        for item in prompt_data["items"]:
            st.markdown(f"- {item}")


def _render_review_tab(project):
    project_id = project["id"]
    standard = project.get("standard", "GoldStandard")
    project_type = project.get("project_type", "standalone_pdd")

    st.markdown(f"""
    <span class="section-header">
        <span class="section-header-icon section-header-icon-purple">{SVG_ICONS.get("review", "")}</span>
        <span class="section-header-text">AI Review</span>
    </span>
    """, unsafe_allow_html=True)

    default_dt = PROJECT_TYPE_INFO.get(project_type, {}).get("default_doc_type", "pdd")
    sessions_data = _fetch(f"/projects/{project_id}/write-sessions?doc_type={default_dt}")
    has_drafts = bool(sessions_data and isinstance(sessions_data, list) and len(sessions_data) > 0)
    if not has_drafts:
        _render_readiness_banner("info", "No draft sections yet. Write at least one section in the Write / Draft tab before running a review.")
    else:
        _render_readiness_banner("ready", "Draft sections available for review.")

    review_tabs = st.tabs(["Review Your Draft", "Review Uploaded Document", "Consistency Check"])

    with review_tabs[0]:
        st.markdown("#### Review Your Draft")
        st.write("The AI will assemble all your drafted sections and review them against the standard's requirements.")

        available_doc_types = DOC_TYPES_FOR_STANDARD.get(standard, {})
        default_dt = PROJECT_TYPE_INFO.get(project_type, {}).get("default_doc_type", "pdd")
        doc_type_keys = list(available_doc_types.keys())
        default_idx = doc_type_keys.index(default_dt) if default_dt in doc_type_keys else 0

        draft_doc_type = st.selectbox(
            "Document type to review",
            doc_type_keys,
            index=default_idx,
            format_func=lambda x: available_doc_types[x],
            key=f"draft_review_dt_{project_id}",
        )

        write_sessions = _fetch(f"/projects/{project_id}/write-sessions?doc_type={draft_doc_type}")
        drafted_count = sum(1 for s in (write_sessions or []) if (s.get("user_text") or s.get("generated_text", "")).strip())

        if drafted_count > 0:
            st.info(f"{drafted_count} section{'s' if drafted_count != 1 else ''} drafted. Ready for review.")

            if st.button("Start Draft Review", key=f"draft_review_btn_{project_id}", type="primary"):
                with st.spinner("AI is reviewing your draft... This may take a minute."):
                    result = _fetch(
                        f"/projects/{project_id}/review-draft?doc_type={draft_doc_type}",
                        method="POST",
                    )
                    if result:
                        st.session_state[f"draft_review_result_{project_id}_{draft_doc_type}"] = result
                        st.rerun()

            draft_result = st.session_state.get(f"draft_review_result_{project_id}_{draft_doc_type}")
            if draft_result:
                _render_review_result(draft_result)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-title">No drafted sections yet</div>
                <div class="empty-state-desc">Use the Write / Draft tab to generate content, then come back here to review it.</div>
            </div>
            """, unsafe_allow_html=True)

    with review_tabs[1]:
        st.markdown("#### Review Uploaded Document")
        st.write("Select an uploaded document to review against the standard's requirements.")

        documents = project.get("documents", [])
        reviewable = [d for d in documents if d.get("status") in ("parsed", "reviewed") and d.get("doc_type") in ("pdd", "mr", "valver", "poa_dd", "vpa_dd")]

        if not reviewable:
            st.info("Upload a PDD, MR, or other reviewable document first (DOCX or PDF format).")
        else:
            doc_options = {d["id"]: f"{d['file_name']} ({PROJECT_DOC_TYPES.get(d['doc_type'], d['doc_type'])})" for d in reviewable}
            selected_doc_id = st.selectbox(
                "Select document to review",
                list(doc_options.keys()),
                format_func=lambda x: doc_options[x],
                key=f"review_doc_select_{project_id}",
            )

            selected_doc = next((d for d in reviewable if d["id"] == selected_doc_id), None)

            if selected_doc and selected_doc.get("doc_type") == "mr":
                pdd_docs = [d for d in documents if d["doc_type"] == "pdd" and d.get("parsed_text")]
                if pdd_docs:
                    st.info(f"PDD found in project: {pdd_docs[0]['file_name']}. The AI will cross-reference your MR against the PDD for consistency.")
                else:
                    st.warning("No PDD found in this project. For the best MR review, upload your PDD first so the AI can check consistency.")

            if st.button("Start Review", key=f"review_btn_{project_id}", type="primary"):
                with st.spinner("AI is reviewing your document... This may take a minute."):
                    result = _fetch(f"/projects/{project_id}/review/{selected_doc_id}", method="POST")
                    if result:
                        st.session_state[f"review_result_{selected_doc_id}"] = result
                        st.rerun()

            result = st.session_state.get(f"review_result_{selected_doc_id}")
            if not result:
                if selected_doc and selected_doc.get("review_result"):
                    import json
                    try:
                        result = json.loads(selected_doc["review_result"]) if isinstance(selected_doc["review_result"], str) else selected_doc["review_result"]
                    except (json.JSONDecodeError, TypeError):
                        result = None

            if result:
                _render_review_result(result)

    with review_tabs[2]:
        st.markdown("#### Cross-Section Consistency Check")
        st.write("Analyze all drafted sections for internal contradictions, missing facts, and inconsistencies.")

        available_doc_types_cc = DOC_TYPES_FOR_STANDARD.get(standard, {})
        default_dt_cc = PROJECT_TYPE_INFO.get(project_type, {}).get("default_doc_type", "pdd")
        doc_type_keys_cc = list(available_doc_types_cc.keys())
        default_idx_cc = doc_type_keys_cc.index(default_dt_cc) if default_dt_cc in doc_type_keys_cc else 0

        cc_doc_type = st.selectbox(
            "Document type to check",
            doc_type_keys_cc,
            index=default_idx_cc,
            format_func=lambda x: available_doc_types_cc[x],
            key=f"cc_doc_type_{project_id}",
        )

        if st.button("Run Consistency Check", key=f"cc_btn_{project_id}", type="primary"):
            with st.spinner("Analyzing sections for consistency..."):
                cc_result = _fetch(
                    f"/projects/{project_id}/validate-consistency?doc_type={cc_doc_type}",
                    method="POST",
                )
                if cc_result:
                    st.session_state[f"cc_result_{project_id}_{cc_doc_type}"] = cc_result
                    st.rerun()

        cc_data = st.session_state.get(f"cc_result_{project_id}_{cc_doc_type}")
        if cc_data:
            if cc_data.get("error"):
                st.warning(cc_data["error"])
            else:
                contradictions = cc_data.get("contradictions", [])
                facts = cc_data.get("facts_extracted", [])
                missing = cc_data.get("missing_required", [])
                suggestions = cc_data.get("suggestions", [])

                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Contradictions", len(contradictions))
                with c2:
                    st.metric("Key Facts Found", len(facts))
                with c3:
                    st.metric("Missing Fields", len(missing))

                if contradictions:
                    with st.expander(f"Contradictions ({len(contradictions)})", expanded=True):
                        for cont in contradictions:
                            severity = cont.get("severity", "medium")
                            sev_color = {"high": "red", "medium": "orange", "low": "blue"}.get(severity, "gray")
                            st.markdown(
                                f'<span style="color:{sev_color};font-weight:600;">[{severity.upper()}]</span> '
                                f'{cont.get("description", "")}',
                                unsafe_allow_html=True,
                            )
                            if cont.get("section_a") and cont.get("section_b"):
                                st.caption(f"Section {cont['section_a']}: {cont.get('value_a', '')} vs Section {cont['section_b']}: {cont.get('value_b', '')}")

                if missing:
                    with st.expander(f"Missing Required Fields ({len(missing)})"):
                        for m in missing:
                            st.write(f"- **{m.get('field', '')}**: {m.get('description', '')}")

                if facts:
                    with st.expander(f"Key Facts Extracted ({len(facts)})"):
                        for f_item in facts:
                            st.write(f"- **{f_item.get('fact', '')}**: {f_item.get('value', '')} (referenced in {f_item.get('sections_referenced', '')})")

                if suggestions:
                    with st.expander("Improvement Suggestions"):
                        for sug in suggestions:
                            st.write(f"- {sug}")


def _render_review_result(result):
    risk = result.get("overall_risk", "UNKNOWN")
    risk_colors = {"LOW": "green", "MEDIUM": "orange", "HIGH": "red"}
    risk_color = risk_colors.get(risk, "gray")
    score = result.get("overall_score", "N/A")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"<span style='font-size:1.3em;font-weight:bold;color:{risk_color};'>Overall Risk: {risk}</span>",
            unsafe_allow_html=True,
        )
    with col2:
        score_label = f"{score}/100" if isinstance(score, int) else str(score)
        st.metric("Overall Score", score_label)

    pdd_consistency = result.get("pdd_consistency", [])
    if pdd_consistency:
        st.markdown("---")
        st.warning("**PDD Consistency Issues:**")
        for issue in pdd_consistency:
            st.write(f"- {issue}")

    priority = result.get("priority_actions", [])
    if priority:
        st.markdown("---")
        st.markdown("**Priority Actions**")
        for i, action in enumerate(priority, 1):
            st.write(f"{i}. {action}")

    sections = result.get("sections", [])
    if sections:
        st.markdown("---")
        st.markdown("**Section-by-Section Review**")
        for sec in sections:
            sec_name = sec.get("section", "Unknown")
            sec_score = sec.get("score", "N/A")
            score_color = "green" if isinstance(sec_score, int) and sec_score >= 80 else "orange" if isinstance(sec_score, int) and sec_score >= 60 else "red"
            with st.expander(f"{sec_name} -- Score: {sec_score}/100"):
                st.markdown(
                    f"<span style='color:{score_color};font-weight:bold;'>Score: {sec_score}/100</span>",
                    unsafe_allow_html=True,
                )
                issues = sec.get("issues", [])
                if issues:
                    st.markdown("**Issues:**")
                    for iss in issues:
                        st.write(f"- {iss}")
                fixes = sec.get("fixes", [])
                if fixes:
                    st.markdown("**Suggested Fixes:**")
                    for fix in fixes:
                        st.write(f"- {fix}")
                questions = sec.get("questions", [])
                if questions:
                    st.markdown("**Questions for You:**")
                    for q in questions:
                        st.write(f"- {q}")

    raw = result.get("raw_review")
    if raw:
        with st.expander("Full Review Text"):
            st.markdown(raw)


LAYER_LABELS = {
    "general_context": "General Context",
    "methodology_rules": "Methodology Rules",
    "technical_parameters": "Technical Parameters",
    "project_documents": "Project Documents",
    "knowledge_base": "Knowledge Base",
    "regulatory_web": "Regulatory / Web",
    "dependencies": "Dependencies",
    "compliance": "Compliance",
}

LAYER_COLORS = {
    "general_context": "#2563eb",
    "methodology_rules": "#7c3aed",
    "technical_parameters": "#dc2626",
    "project_documents": "#0d9488",
    "knowledge_base": "#ca8a04",
    "regulatory_web": "#ea580c",
    "dependencies": "#6366f1",
    "compliance": "#059669",
}


def _render_research_assistant(project_id, doc_type):
    with st.expander("AI Research Assistant — Fill missing project data", expanded=False):
        st.caption("The AI can analyze your project for missing information and research answers from multiple sources: uploaded documents, methodology rules, web search, and knowledge base.")

        ra_col1, ra_col2 = st.columns(2)
        with ra_col1:
            analyze_btn = st.button("Analyze Gaps", key=f"research_analyze_{project_id}")
        with ra_col2:
            run_btn = st.button("Research All Gaps", key=f"research_run_{project_id}", type="primary")

        if analyze_btn:
            with st.spinner("Analyzing project for missing information..."):
                gap_result = _fetch(f"/projects/{project_id}/research/analyze-gaps?doc_type={doc_type}", method="POST")
            if gap_result and gap_result.get("gaps"):
                gaps = gap_result["gaps"]
                st.info(gap_result.get("summary", f"Found {len(gaps)} gaps"))
                layer_groups = {}
                for g in gaps:
                    layer = g.get("layer", "general_context")
                    if layer not in layer_groups:
                        layer_groups[layer] = []
                    layer_groups[layer].append(g)
                for layer, layer_gaps in layer_groups.items():
                    label = LAYER_LABELS.get(layer, layer)
                    color = LAYER_COLORS.get(layer, "#666")
                    st.markdown(f'<span style="color:{color};font-weight:600">{label}</span> — {len(layer_gaps)} gap(s)', unsafe_allow_html=True)
                    for g in layer_gaps[:10]:
                        st.caption(f"  - {g.get('description', g.get('field', ''))}")
            elif gap_result:
                st.success("No gaps found — all project fields are populated.")
            else:
                st.error("Failed to analyze gaps.")

        if run_btn:
            with st.spinner("Researching missing information across all layers... This may take a minute."):
                research_result = _fetch(
                    f"/projects/{project_id}/research/run",
                    method="POST",
                    json={"doc_type": doc_type, "max_gaps": 20},
                )
            if research_result and research_result.get("results"):
                results = research_result["results"]
                st.info(research_result.get("summary", f"Found {len(results)} suggestions"))
                st.session_state[f"research_results_{project_id}"] = results
            elif research_result:
                st.warning(research_result.get("summary", "No suggestions found."))
            else:
                st.error("Research session failed.")

        stored_results = st.session_state.get(f"research_results_{project_id}")
        if not stored_results:
            existing = _fetch(f"/projects/{project_id}/research/results?status=pending")
            if existing and existing.get("results"):
                stored_results = existing["results"]

        if stored_results:
            st.markdown("---")
            st.markdown("**Research Suggestions**")
            for idx, res in enumerate(stored_results):
                _render_research_result_card(project_id, res, idx)


def _render_research_result_card(project_id, result, idx):
    result_data = result.get("result_data", result)
    if isinstance(result_data, str):
        try:
            import json as _json
            result_data = _json.loads(result_data)
        except Exception:
            result_data = {}

    field = result.get("field") or result_data.get("field", "Unknown field")
    value = result_data.get("value", "")
    confidence = result.get("confidence") or result_data.get("confidence", 0)
    layer = result.get("layer") or result_data.get("layer", "")
    sources = result.get("sources") or result_data.get("sources", [])
    result_id = result.get("id")
    status = result.get("status", "pending")

    if not value or status != "pending":
        return

    layer_label = LAYER_LABELS.get(layer, layer)
    layer_color = LAYER_COLORS.get(layer, "#666")

    if confidence >= 0.7:
        conf_label = "High"
        conf_color = "#059669"
    elif confidence >= 0.4:
        conf_label = "Medium"
        conf_color = "#ca8a04"
    else:
        conf_label = "Low"
        conf_color = "#dc2626"

    with st.container(border=True):
        field_display = field.split(".")[-1].replace("_", " ").title()
        st.markdown(
            f'<span style="font-weight:600">{field_display}</span> '
            f'<span style="color:{layer_color};font-size:0.85em">({layer_label})</span> '
            f'<span style="color:{conf_color};font-size:0.85em">Confidence: {conf_label} ({confidence:.0%})</span>',
            unsafe_allow_html=True,
        )

        if isinstance(value, str) and len(value) > 200:
            st.text_area("Suggested value", value=value, height=80, disabled=True, key=f"rv_{project_id}_{idx}", label_visibility="collapsed")
        else:
            st.markdown(f"**Suggested value:** {value}")

        options = result_data.get("options")
        if options and isinstance(options, list) and len(options) > 1:
            with st.expander("Alternative options"):
                for opt in options:
                    if isinstance(opt, dict):
                        st.caption(f"- {opt.get('value', opt)} (Source: {opt.get('source', 'N/A')}, Rank: {opt.get('rank', '?')})")
                    else:
                        st.caption(f"- {opt}")

        if sources and isinstance(sources, list):
            src_parts = []
            for s in sources[:4]:
                if isinstance(s, dict):
                    ref = s.get("reference", s.get("type", ""))
                    url = s.get("url")
                    if url:
                        src_parts.append(f'<span style="font-size:0.8em">[{ref}]({url})</span>')
                    else:
                        src_parts.append(f'<span style="font-size:0.8em">{ref}</span>')
            if src_parts:
                st.caption("Sources: " + " | ".join(src_parts))

        if result_id:
            c1, c2, c3 = st.columns([1, 1, 3])
            with c1:
                if st.button("Confirm", key=f"confirm_{project_id}_{result_id}_{idx}"):
                    confirm_resp = _fetch(
                        f"/projects/{project_id}/research/confirm",
                        method="POST",
                        json={"result_id": result_id},
                    )
                    if confirm_resp and confirm_resp.get("confirmed"):
                        st.success(f"Confirmed and saved: {field_display}")
                        if f"research_results_{project_id}" in st.session_state:
                            del st.session_state[f"research_results_{project_id}"]
                        st.rerun()
            with c2:
                if st.button("Reject", key=f"reject_{project_id}_{result_id}_{idx}"):
                    _fetch(
                        f"/projects/{project_id}/research/reject",
                        method="POST",
                        json={"result_id": result_id},
                    )
                    if f"research_results_{project_id}" in st.session_state:
                        del st.session_state[f"research_results_{project_id}"]
                    st.rerun()


def _render_write_tab(project):
    project_id = project["id"]
    standard = project.get("standard", "GoldStandard")
    project_type = project.get("project_type", "standalone_pdd")

    st.markdown(f"""
    <span class="section-header">
        <span class="section-header-icon section-header-icon-teal">{SVG_ICONS.get("write", "")}</span>
        <span class="section-header-text">AI Writing Assistant</span>
    </span>
    """, unsafe_allow_html=True)
    st.write("Draft your document section by section or generate the full document at once.")

    selected_scenario_id = project.get("selected_scenario_id")
    if selected_scenario_id:
        try:
            from carbongpt.core.er_simulator import get_selected_scenario
            sel = get_selected_scenario(project_id)
            if sel:
                sc = sel["scenario"]
                summary = sc.get("results_summary") or {}
                if isinstance(summary, str):
                    import json
                    try:
                        summary = json.loads(summary)
                    except Exception:
                        summary = {}
                total_er = summary.get("total_er", 0)
                annual_er = summary.get("average_annual_er", 0)
                _render_readiness_banner(
                    "info",
                    f"Selected Scenario: {sc.get('name', 'Unknown')} "
                    f"-- {total_er:,.0f} tCO2e total, {annual_er:,.0f} tCO2e/yr. "
                    f"ER projections from this scenario will be used in drafted sections."
                )
        except Exception:
            pass
    else:
        _render_readiness_banner("warning", "No scenario selected for PDD drafting. Select a scenario in the ER Simulator to include ER projections in your drafts.")

    doc_count = len(project.get("documents", []))
    has_methodology = bool(project.get("methodology"))
    if not has_methodology:
        _render_readiness_banner("warning", "No methodology selected. Set up your project methodology in the Setup tab first.")
    elif doc_count > 0:
        _render_readiness_banner("info", f"{doc_count} supporting document{'s' if doc_count != 1 else ''} uploaded. The AI writer will use them as context for your drafts.")
    else:
        _render_readiness_banner("info", "Tip: Upload supporting documents in the Documents tab to give the AI writer more context.")

    available_doc_types = DOC_TYPES_FOR_STANDARD.get(standard, {})
    if not available_doc_types:
        st.error("No document templates available for this standard.")
        return

    default_dt = PROJECT_TYPE_INFO.get(project_type, {}).get("default_doc_type", "pdd")
    doc_type_keys = list(available_doc_types.keys())
    default_idx = doc_type_keys.index(default_dt) if default_dt in doc_type_keys else 0

    col_dt, col_actions = st.columns([1, 2])
    with col_dt:
        selected_write_dt = st.selectbox(
            "Document type",
            doc_type_keys,
            index=default_idx,
            format_func=lambda x: available_doc_types[x],
            key=f"write_dt_{project_id}",
        )

    sections = _fetch(f"/projects/{project_id}/sections?doc_type={selected_write_dt}")
    if not sections:
        st.warning("Could not load sections for this document type.")
        return

    existing_sessions = _fetch(f"/projects/{project_id}/write-sessions?doc_type={selected_write_dt}")
    session_map = {}
    if existing_sessions:
        for sess in existing_sessions:
            session_map[sess["section_id"]] = sess

    drafted_count = sum(1 for s in sections if s["id"] in session_map)
    total_count = len(sections)

    with col_actions:
        st.caption(f"{drafted_count} of {total_count} sections drafted")
        if drafted_count > 0:
            st.progress(drafted_count / total_count)

    user_instructions = st.text_area(
        "Instructions for the AI (applies to all generation)",
        key=f"write_instr_{project_id}",
        placeholder="e.g., 'Focus on cookstove distribution in rural areas', 'Use conservative emission factors'...",
        height=60,
    )

    project_docs = project.get("documents", [])
    ai_context_docs = [d for d in project_docs if d.get("use_as_ai_context", True) and (d.get("parsed_text") or "").strip()]
    if ai_context_docs:
        doc_names = [f"**{d['file_name']}** ({len(d['parsed_text'].split()):,} words)" for d in ai_context_docs]
        with st.expander(f"AI Context: {len(ai_context_docs)} document{'s' if len(ai_context_docs) != 1 else ''} will be used", expanded=False):
            for dn in doc_names:
                st.markdown(f"- {dn}")
            st.caption("Toggle documents on/off in the Documents tab.")
    elif project_docs:
        st.caption("No documents are active as AI context. Toggle them on in the Documents tab.")

    project_brief = (project.get("project_intake") or {}).get("_project_brief")
    if project_brief:
        with st.expander("Project Brief (shared context for all sections)"):
            st.markdown(project_brief)
            if st.button("Regenerate Brief", key=f"regen_brief_{project_id}"):
                with st.spinner("Regenerating project brief..."):
                    brief_result = _fetch(f"/projects/{project_id}/generate-brief", method="POST")
                    if brief_result:
                        st.success("Project brief updated.")
                        st.rerun()
    else:
        if st.button("Generate Project Brief", key=f"gen_brief_{project_id}", help="Creates a consistent summary shared across all sections"):
            with st.spinner("Generating project brief..."):
                brief_result = _fetch(f"/projects/{project_id}/generate-brief", method="POST")
                if brief_result:
                    st.success("Project brief generated. It will be included in all section prompts.")
                    st.rerun()

    _render_research_assistant(project_id, selected_write_dt)

    gen_col1, gen_col2, gen_col3 = st.columns([1, 1, 1])
    with gen_col1:
        generate_all = st.button(
            "Generate Full Document",
            key=f"generate_all_btn_{project_id}",
            type="primary",
            help="Generate all sections at once. This may take several minutes.",
        )
    with gen_col2:
        if drafted_count > 0:
            regenerate_all = st.button(
                "Regenerate All",
                key=f"regenerate_all_btn_{project_id}",
                help="Regenerate all sections, replacing existing drafts.",
            )
        else:
            regenerate_all = False

    if generate_all or regenerate_all:
        progress_bar = st.progress(0, text="Starting full document generation...")
        status_text = st.empty()

        result = None
        with st.spinner(""):
            import time as _time
            progress_bar.progress(0.02, text=f"Generating {total_count} sections...")
            result = _fetch(
                f"/projects/{project_id}/write-all?doc_type={selected_write_dt}",
                method="POST",
                json={"user_instructions": user_instructions or None},
                timeout=600,
            )

        if result:
            success_count = result.get("success_count", 0)
            total = result.get("total", 0)
            progress_bar.progress(1.0, text=f"Done: {success_count}/{total} sections generated")
            st.success(f"Generated {success_count} of {total} sections successfully.")
            _time.sleep(1)
            st.rerun()
        else:
            progress_bar.empty()
            st.error("Full document generation failed. Try generating sections individually.")

    st.divider()

    std_label = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(standard, standard)
    doc_label = available_doc_types.get(selected_write_dt, selected_write_dt)

    with st.container(border=True):
        st.markdown(
            f"<div style='text-align:center; padding: 12px 0 4px 0;'>"
            f"<span style='font-size:1.4em; font-weight:700;'>{doc_label}</span><br/>"
            f"<span style='color:#666;'>{std_label}</span><br/>"
            f"<span style='font-size:0.95em;'>{project.get('name', '')}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    current_parent = None
    for sec in sections:
        sec_id = sec["id"]
        sec_title = sec["title"]
        parent = sec.get("parent_section", "")

        if parent and parent != current_parent:
            current_parent = parent
            st.markdown(f"#### {parent}")

        has_draft = sec_id in session_map
        sess = session_map.get(sec_id, {})
        draft_text = sess.get("user_text") or sess.get("generated_text") or ""

        if has_draft and draft_text.strip():
            stripe_class = "section-card-drafted"
            status_text = "Drafted"
        else:
            stripe_class = "section-card-empty"
            status_text = "Not started"

        with st.container(border=True):
            st.markdown(
                f"<div class='{stripe_class}' style='margin:-1rem -1rem 0.5rem -1rem; padding:0;'></div>",
                unsafe_allow_html=True,
            )
            header_col, status_col, action_col1, action_col2 = st.columns([3.5, 0.8, 1, 1])
            with header_col:
                st.markdown(f"**{sec_id} &mdash; {sec_title}**")
            with status_col:
                if has_draft and draft_text.strip():
                    wc = len(draft_text.split())
                    st.markdown(
                        f"<span class='status-badge status-active'>{status_text}</span>"
                        f"<br/><span style='font-size:0.7rem;color:#94a3b8;'>{wc} words</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<span class='status-badge status-draft'>{status_text}</span>",
                        unsafe_allow_html=True,
                    )
            with action_col1:
                btn_label = "Regenerate" if has_draft else "Generate"
                if st.button(btn_label, key=f"gen_sec_{project_id}_{selected_write_dt}_{sec_id}", use_container_width=True):
                    with st.spinner(f"Generating {sec_id}..."):
                        result = _fetch(
                            f"/projects/{project_id}/write?doc_type={selected_write_dt}",
                            method="POST",
                            json={
                                "section_id": sec_id,
                                "user_instructions": user_instructions or None,
                            },
                        )
                        if result:
                            val = result.get("validation")
                            if val:
                                st.session_state[f"val_{project_id}_{selected_write_dt}_{sec_id}"] = val
                            st.rerun()
            with action_col2:
                with st.popover("Info"):
                    st.markdown(f"**Requirements for {sec_id}:**")
                    for req in sec.get("must_include", []):
                        st.write(f"- {req}")
                    explain_key = f"explain_{project_id}_{selected_write_dt}_{sec_id}"
                    if st.button("Explain", key=f"explain_btn_{project_id}_{selected_write_dt}_{sec_id}"):
                        with st.spinner("..."):
                            expl_result = _fetch(
                                f"/projects/{project_id}/explain?doc_type={selected_write_dt}",
                                method="POST",
                                json={"section_id": sec_id},
                            )
                            if expl_result:
                                st.session_state[explain_key] = expl_result.get("explanation", "")
                    explanation = st.session_state.get(explain_key)
                    if explanation:
                        st.info(explanation)

            edit_key = f"edit_{project_id}_{selected_write_dt}_{sec_id}"
            editing = st.session_state.get(edit_key, False)

            if has_draft and draft_text:
                if editing:
                    edited_text = st.text_area(
                        f"Edit {sec_id}",
                        value=draft_text,
                        height=300,
                        key=f"textarea_{project_id}_{selected_write_dt}_{sec_id}",
                        label_visibility="collapsed",
                    )
                    save_col, cancel_col, _ = st.columns([1, 1, 4])
                    with save_col:
                        if st.button("Save", key=f"save_sec_{project_id}_{selected_write_dt}_{sec_id}", type="primary", use_container_width=True):
                            _fetch(
                                f"/projects/{project_id}/section-text",
                                method="PATCH",
                                json={
                                    "section_id": sec_id,
                                    "doc_type": selected_write_dt,
                                    "text": edited_text,
                                },
                            )
                            st.session_state[edit_key] = False
                            st.rerun()
                    with cancel_col:
                        if st.button("Cancel", key=f"cancel_sec_{project_id}_{selected_write_dt}_{sec_id}", use_container_width=True):
                            st.session_state[edit_key] = False
                            st.rerun()
                else:
                    st.markdown(draft_text)
                    if st.button("Edit", key=f"edit_btn_{project_id}_{selected_write_dt}_{sec_id}"):
                        st.session_state[edit_key] = True
                        st.rerun()

                val_data = st.session_state.get(f"val_{project_id}_{selected_write_dt}_{sec_id}")
                if val_data:
                    q_score = val_data.get("quality_score", 0)
                    covered = val_data.get("covered", [])
                    missing_items = val_data.get("missing", [])
                    has_ph = val_data.get("has_placeholders", False)
                    wc_val = val_data.get("word_count", 0)

                    score_color = "#22c55e" if q_score >= 0.7 else ("#f59e0b" if q_score >= 0.4 else "#ef4444")
                    with st.expander(f"Quality: {q_score:.0%} | {len(covered)}/{len(covered)+len(missing_items)} requirements covered"):
                        st.markdown(
                            f"<span style='color:{score_color};font-weight:600;font-size:1.1em;'>"
                            f"Quality Score: {q_score:.0%}</span> "
                            f"| {wc_val} words"
                            f"{' | Has placeholders' if has_ph else ''}",
                            unsafe_allow_html=True,
                        )
                        if covered:
                            st.markdown("**Covered requirements:**")
                            for ci in covered:
                                st.markdown(f"- {ci}")
                        if missing_items:
                            st.markdown("**Missing requirements:**")
                            for mi in missing_items:
                                st.warning(f"- {mi}")
            else:
                st.markdown(
                    "<span style='color:#999; font-style:italic;'>"
                    "[This section has not been drafted yet]</span>",
                    unsafe_allow_html=True,
                )


def _build_tool33_lookup(meth_parsed, settings, country):
    meth_code = meth_parsed.get("methodology_code", "")
    if not meth_code:
        return {}
    try:
        from carbongpt.core.tool_defaults import get_defaults_for_methodology, FUEL_NCV, FUEL_EF_CO2, FUEL_EF_NONCO2
        baseline_fuel = settings.get("baseline_fuel", "")
        project_fuel = settings.get("project_fuel", "")
        defaults = get_defaults_for_methodology(
            meth_code,
            country=country,
            baseline_fuel=baseline_fuel,
            project_fuel=project_fuel,
        )
        params = defaults.get("parameters", {})
        if not baseline_fuel:
            params.setdefault("baseline_NCV", {"value": "15.6 (wood) / 29.5 (charcoal)", "unit": "TJ/Gg", "source": "IPCC 2006 (select baseline fuel for specific value)"})
            params.setdefault("baseline_EF_CO2", {"value": "112.0 (wood) / 165.22 (charcoal w/ production)", "unit": "tCO2/TJ", "source": "IPCC 2006 / TPDDTEC (select baseline fuel for specific value)"})
            params.setdefault("baseline_EF_nonCO2", {"value": "9.46 (wood) / 44.83 (charcoal w/ production)", "unit": "tCO2e/TJ", "source": "VM0050/TPDDTEC AR5 GWP (select baseline fuel for specific value)"})
        if not project_fuel:
            params.setdefault("project_NCV", {"value": "select project fuel for value", "unit": "TJ/Gg", "source": "IPCC 2006 (select project fuel in Methodology Choices)"})
            params.setdefault("project_EF_CO2", {"value": "select project fuel for value", "unit": "tCO2/TJ", "source": "IPCC 2006 (select project fuel in Methodology Choices)"})
            params.setdefault("project_EF_nonCO2", {"value": "select project fuel for value", "unit": "tCO2e/TJ", "source": "IPCC 2006 (select project fuel in Methodology Choices)"})
        return params
    except Exception:
        return {}


def _match_tool33_param(symbol, tool33_params):
    if not symbol or not tool33_params:
        return None
    import unicodedata
    sym_clean = unicodedata.normalize("NFKD", symbol).lower().replace(" ", "").replace(",", "").replace("_", "")
    SYMBOL_MAP = {
        "efbfco2": ["baseline_EF_CO2"],
        "efbfnonco2": ["baseline_EF_nonCO2"],
        "efpfco2": ["project_EF_CO2"],
        "efpfnonco2": ["project_EF_nonCO2"],
        "ncvbfuel": ["baseline_NCV"],
        "ncvpfuel": ["project_NCV"],
        "ncvb": ["baseline_NCV"],
        "ncvp": ["project_NCV"],
        "fnrbiy": ["fNRB"],
        "fnrb": ["fNRB"],
        "cf": ["CF"],
        "efco2": ["baseline_EF_CO2"],
        "efnonco2": ["baseline_EF_nonCO2"],
    }
    for pattern, keys in SYMBOL_MAP.items():
        if pattern in sym_clean or sym_clean in pattern:
            for k in keys:
                if k in tool33_params:
                    return tool33_params[k]
    for pkey, pval in tool33_params.items():
        if not isinstance(pval, dict):
            continue
        pkey_clean = pkey.lower().replace("_", "").replace(" ", "")
        if sym_clean in pkey_clean or pkey_clean in sym_clean:
            return pval
    return None


def _render_tool33_defaults(project_id, meth_parsed, settings, meth_inputs, country=""):
    meth_code = meth_parsed.get("methodology_code", "")
    if not meth_code:
        return
    code_upper = meth_code.upper().replace("GS-", "")
    if code_upper not in ("VM0050", "TPDDTEC"):
        return

    try:
        from carbongpt.core.tool_defaults import get_fnrb_for_country, get_fuel_defaults, WOOD_TO_CHARCOAL_CF, LEAKAGE_DEFAULTS
    except ImportError:
        return
    baseline_fuel = settings.get("baseline_fuel", "")
    project_fuel = settings.get("project_fuel", "")

    with st.container(border=True):
        st.markdown("#### Reference Default Values (CDM TOOL33 v3 / IPCC)")
        st.caption("Official default values for your methodology. These are auto-populated from CDM TOOL33 v3 and IPCC guidelines.")

        if country:
            fnrb_data = get_fnrb_for_country(country)
            if fnrb_data:
                current_fnrb = meth_inputs.get("tool33_fNRB", "")
                pct = int(fnrb_data['value'] * 100)
                default_label = f"fNRB = {fnrb_data['value']} ({pct}%)"
                val = st.text_input(
                    f"fNRB - Fraction of non-renewable biomass [{fnrb_data['unit']}]",
                    value=current_fnrb,
                    key=f"tool33_fnrb_{project_id}",
                    placeholder=default_label,
                )
                meth_inputs["tool33_fNRB"] = val
                st.caption(f"Source: {fnrb_data['source']}. {fnrb_data.get('note', '')}")
        else:
            st.caption("Set the project country in Project Setup to see country-specific fNRB values.")

        if baseline_fuel:
            bl_fuel_lower = baseline_fuel.lower().replace(" ", "_").replace("-", "_")
            bl_is_charcoal = bl_fuel_lower in ("charcoal", "green_charcoal")

            if bl_is_charcoal:
                from carbongpt.core.tool_defaults import CHARCOAL_DEFAULTS_SUMMARY
                st.markdown(f"**Baseline fuel: {baseline_fuel}**")
                charcoal_scenarios = {
                    "With production emissions (methodology default)": "with_production",
                    "With production emissions (methodology cap)": "with_production_cap",
                    "Combustion only (no production emissions)": "combustion_only",
                    "Custom values": "custom",
                }
                current_scenario = meth_inputs.get("tool33_charcoal_scenario", "With production emissions (methodology default)")
                scenario_labels = list(charcoal_scenarios.keys())
                scenario_idx = 0
                if current_scenario in scenario_labels:
                    scenario_idx = scenario_labels.index(current_scenario)
                selected_scenario = st.selectbox(
                    "Charcoal emission factor scenario",
                    scenario_labels,
                    index=scenario_idx,
                    key=f"tool33_charcoal_scenario_{project_id}",
                    help="Select how charcoal emissions are calculated. 'With production' includes emissions from charcoal production (wood pyrolysis). The 'cap' is the maximum permitted value.",
                )
                meth_inputs["tool33_charcoal_scenario"] = selected_scenario
                scenario_key = charcoal_scenarios[selected_scenario]

                if scenario_key == "custom":
                    for param_name, unit, default_val in [
                        ("NCV", "TJ/Gg", 29.5),
                        ("EF_CO2", "tCO2/TJ", 165.22),
                        ("EF_nonCO2", "tCO2e/TJ", 44.83),
                    ]:
                        sk = f"bl_{param_name}"
                        current_val = meth_inputs.get(f"tool33_{sk}", "")
                        val = st.text_input(
                            f"Baseline {param_name} ({baseline_fuel}) [{unit}]",
                            value=current_val,
                            key=f"tool33_bl_{param_name}_{project_id}",
                            placeholder=f"Enter value (default reference: {default_val})",
                        )
                        meth_inputs[f"tool33_{sk}"] = val
                else:
                    scenario_data = CHARCOAL_DEFAULTS_SUMMARY[scenario_key]
                    ef_co2 = scenario_data["EF_CO2"]
                    ef_nonco2 = scenario_data["EF_nonCO2_AR5"]
                    ncv = CHARCOAL_DEFAULTS_SUMMARY["NCV"]

                    for param_name, value, unit in [
                        ("NCV", ncv, "TJ/Gg"),
                        ("EF_CO2", ef_co2, "tCO2/TJ"),
                        ("EF_nonCO2", ef_nonco2, "tCO2e/TJ"),
                    ]:
                        sk = f"bl_{param_name}"
                        current_val = meth_inputs.get(f"tool33_{sk}", "")
                        val = st.text_input(
                            f"Baseline {param_name} ({baseline_fuel}) [{unit}]",
                            value=current_val,
                            key=f"tool33_bl_{param_name}_{project_id}",
                            placeholder=f"Default: {value} ({selected_scenario})",
                        )
                        meth_inputs[f"tool33_{sk}"] = val

                    st.caption(f"{scenario_data.get('note', '')} Source: {CHARCOAL_DEFAULTS_SUMMARY['source']}")

                cf_data = WOOD_TO_CHARCOAL_CF["default"]
                current_cf = meth_inputs.get("tool33_CF", "")
                val = st.text_input(
                    f"CF - Wood-to-charcoal conversion factor [{cf_data['unit']}]",
                    value=current_cf,
                    key=f"tool33_cf_{project_id}",
                    placeholder=f"Default: {cf_data['value']} ({cf_data['source']})",
                )
                meth_inputs["tool33_CF"] = val

            else:
                bf_defaults = get_fuel_defaults(baseline_fuel)
                if bf_defaults:
                    st.markdown(f"**Baseline fuel: {baseline_fuel}**")
                    for param_key in ["NCV", "EF_CO2", "EF_nonCO2"]:
                        param_data = bf_defaults.get(param_key)
                        if not param_data or not isinstance(param_data, dict) or "value" not in param_data:
                            continue
                        sk = f"bl_{param_key}"
                        current_val = meth_inputs.get(f"tool33_{sk}", "")
                        val = st.text_input(
                            f"Baseline {param_key} ({baseline_fuel}) [{param_data['unit']}]",
                            value=current_val,
                            key=f"tool33_bl_{param_key}_{project_id}",
                            placeholder=f"Default: {param_data['value']} ({param_data['source']})",
                        )
                        meth_inputs[f"tool33_{sk}"] = val

        if project_fuel and project_fuel != baseline_fuel:
            pf_defaults = get_fuel_defaults(project_fuel)
            if pf_defaults:
                st.markdown(f"**Project fuel: {project_fuel}**")
                for param_key in ["NCV", "EF_CO2", "EF_nonCO2"]:
                    param_data = pf_defaults.get(param_key)
                    if not param_data or not isinstance(param_data, dict) or "value" not in param_data:
                        continue
                    sk = f"pj_{param_key}"
                    current_val = meth_inputs.get(f"tool33_{sk}", "")
                    val = st.text_input(
                        f"Project {param_key} ({project_fuel}) [{param_data['unit']}]",
                        value=current_val,
                        key=f"tool33_pj_{param_key}_{project_id}",
                        placeholder=f"Default: {param_data['value']} ({param_data['source']})",
                    )
                    meth_inputs[f"tool33_{sk}"] = val

        leak_key = "cookstove_renewable_biomass"
        leak_data = LEAKAGE_DEFAULTS.get(leak_key, {})
        if leak_data:
            st.caption(f"Leakage: {leak_data['value']} discount factor ({leak_data['source']})")


def _render_methodology_layer(project_id, meth_parsed, existing_settings, intake, country=""):
    meth_inputs = intake.get("methodology_parameters", {})
    new_settings = dict(existing_settings)

    context_dims = meth_parsed.get("context_dimensions", [])
    calc_methods = meth_parsed.get("calculation_methods", [])
    parameters = meth_parsed.get("parameters", [])

    qualitative_params = [p for p in parameters if p.get("category") == "qualitative"]

    auto_derived_dims = set()
    selected_baseline = existing_settings.get("baseline_fuel", "")
    selected_project = existing_settings.get("project_fuel", "")

    if context_dims:
        with st.container(border=True):
            st.markdown("#### Methodology Choices")
            st.caption("These selections determine which default values and equations apply to your project.")
            for dim in context_dims:
                dim_key = dim.get("dimension_key", "")
                if not dim_key:
                    continue
                options = dim.get("options", [])
                if not options:
                    continue

                if dim_key == "method_selection":
                    auto_derived_dims.add(dim_key)
                    continue

                if dim_key == "scale_classification":
                    intake_scale = st.session_state.get(f"setup_po_scale_{project_id}", "") or intake.get("project_overview", {}).get("scale", "")
                    if intake_scale:
                        scale_lower = intake_scale.lower()
                        matched = None
                        for opt in options:
                            if opt.lower() == scale_lower or scale_lower in opt.lower() or opt.lower() in scale_lower:
                                matched = opt
                                break
                        if matched:
                            new_settings[dim_key] = matched
                            auto_derived_dims.add(dim_key)
                            continue

                current_val = existing_settings.get(dim_key, "")
                idx = 0
                if current_val in options:
                    idx = options.index(current_val)
                selected = st.selectbox(
                    dim.get("label", dim_key),
                    options,
                    index=idx,
                    key=f"meth_dim_{project_id}_{dim_key}",
                    help=dim.get("description", ""),
                )
                new_settings[dim_key] = selected

                if dim_key == "baseline_fuel":
                    selected_baseline = selected
                elif dim_key == "project_fuel":
                    selected_project = selected

    if selected_baseline and selected_project:
        from carbongpt.core.parameter_engine import normalize_fuel_type
        from carbongpt.core.methodology_rules import derive_tpddtec_method, get_tpddtec_method_badge_info
        bl_norm = normalize_fuel_type(selected_baseline)
        pj_norm = normalize_fuel_type(selected_project)
        scale_val = new_settings.get("scale_classification", "")
        baseline_approach = new_settings.get("baseline_approach", existing_settings.get("baseline_approach", "measured"))
        method_result = derive_tpddtec_method(bl_norm, pj_norm, scale_val, baseline_approach)
        derived_method = method_result["method_label"]
        derived_method_id = method_result["method_id"]
        new_settings["method_selection"] = derived_method
        new_settings["calculation_method"] = derived_method_id

        badge_info = get_tpddtec_method_badge_info(derived_method_id)
        st.markdown(
            f'<span style="background:{badge_info["color"]};color:white;padding:3px 10px;border-radius:4px;font-size:0.85em;font-weight:bold;">'
            f'{badge_info["label"]}</span>',
            unsafe_allow_html=True,
        )
        st.caption(method_result["reason"])

        if method_result["method2_available"] and not method_result["baseline_approach_locked"]:
            approach_options = ["measured", "default"]
            current_approach = baseline_approach if baseline_approach in approach_options else "measured"
            approach_labels = {
                "measured": "Measured field data (Baseline Performance Field Test — BFT required)",
                "default": "Methodology default (0.5 t/capita/yr fuelwood, no BFT needed)",
            }
            new_approach = st.radio(
                "Baseline fuel consumption approach",
                approach_options,
                index=approach_options.index(current_approach),
                format_func=lambda x: approach_labels[x],
                key=f"meth_approach_{project_id}",
            )
            if new_approach != baseline_approach:
                new_settings["baseline_approach"] = new_approach
                method_result2 = derive_tpddtec_method(bl_norm, pj_norm, scale_val, new_approach)
                new_settings["method_selection"] = method_result2["method_label"]
                new_settings["calculation_method"] = method_result2["method_id"]
                badge_info2 = get_tpddtec_method_badge_info(method_result2["method_id"])
                st.caption(f"Approach changed: will use {badge_info2['label']}")
            else:
                new_settings["baseline_approach"] = baseline_approach

        if auto_derived_dims:
            derived_info = []
            if "scale_classification" in auto_derived_dims:
                derived_info.append(f"Scale: {new_settings.get('scale_classification', '')}")
            if derived_info:
                st.caption("Auto-derived: " + " | ".join(derived_info))

    if qualitative_params:
        with st.container(border=True):
            st.markdown("#### Qualitative Requirements")
            st.caption("Descriptive information required by the methodology.")
            for param in qualitative_params:
                p_name = param.get("name", "")
                p_source = param.get("source", "")
                p_id = param.get("parameter_id", p_name)
                safe_key = (p_id or p_name).replace(" ", "_").replace(",", "").replace(".", "_")[:40]
                current_val = meth_inputs.get(safe_key, "")
                val = st.text_area(
                    p_name,
                    value=current_val,
                    key=f"meth_qual_{project_id}_{safe_key}",
                    placeholder=f"Source: {p_source[:80]}" if p_source else "",
                    height=80,
                )
                meth_inputs[safe_key] = val

    with st.container(border=True):
        st.markdown("#### Parameters & Defaults")
        st.caption("Emission factors, fuel properties, monitoring parameters, and activity data are managed centrally in the Parameters tab. Initialize parameters there after saving your methodology choices.")

        def _go_to_params():
            st.session_state[f"ws_tab_{project_id}"] = 2

        st.button("Go to Parameters tab", key=f"goto_params_from_setup_{project_id}", on_click=_go_to_params)

    return new_settings, meth_inputs


def _intel_source_label(intake, category, field_key):
    sources = intake.get("_intelligence_sources", {})
    key = f"{category}.{field_key}"
    src = sources.get(key, "")
    if src:
        st.markdown(
            f'<span style="font-size:0.7rem;color:#0d9488;font-style:italic;" data-testid="intel-source-{category}-{field_key}">'
            f'from {src}</span>',
            unsafe_allow_html=True,
        )


def _render_intake_by_type(project_id, project_type, intake, standard="GoldStandard", methodology=None, methodology_settings=None):
    if project_type in ("standalone_pdd", ""):
        return _render_intake_pdd(project_id, intake, standard, methodology=methodology, methodology_settings=methodology_settings)
    elif project_type == "poa_programme":
        return _render_intake_poa(project_id, intake, standard)
    elif project_type == "vpa_component":
        return _render_intake_vpa(project_id, intake, standard)
    elif project_type == "monitoring_report":
        return _render_intake_mr(project_id, intake, standard)
    elif project_type == "valver_report":
        return _render_intake_valver(project_id, intake, standard)
    else:
        return _render_intake_pdd(project_id, intake, standard, methodology=methodology, methodology_settings=methodology_settings)


def _render_proponent_card(project_id, intake, standard, prefix=""):
    prop = intake.get("proponent", {})
    sfx = f"_{prefix}" if prefix else ""

    with st.container(border=True):
        std_label = "Project Developer" if standard == "GoldStandard" else "Project Proponent"
        st.markdown(f"#### {std_label}")
        pc1, pc2 = st.columns(2)
        with pc1:
            prop_org = st.text_input("Organization name", value=prop.get("organization_name", ""),
                                      key=f"setup_prop_org{sfx}_{project_id}",
                                      placeholder="e.g., CleanCook Ltd.")
            _intel_source_label(intake, "proponent", "organization_name")
            prop_email = st.text_input("Email", value=prop.get("email", ""),
                                        key=f"setup_prop_email{sfx}_{project_id}",
                                        placeholder="contact@example.com")
            _intel_source_label(intake, "proponent", "email")
        with pc2:
            prop_contact = st.text_input("Contact person", value=prop.get("contact_person", ""),
                                          key=f"setup_prop_contact{sfx}_{project_id}",
                                          placeholder="Full name of primary contact")
            _intel_source_label(intake, "proponent", "contact_person")
            prop_phone = st.text_input("Phone", value=prop.get("phone", ""),
                                        key=f"setup_prop_phone{sfx}_{project_id}",
                                        placeholder="+1 234 567 8900")
            _intel_source_label(intake, "proponent", "phone")
        prop_address = st.text_input("Address", value=prop.get("address", ""),
                                      key=f"setup_prop_address{sfx}_{project_id}",
                                      placeholder="Street, City, Country")
        _intel_source_label(intake, "proponent", "address")
        prop_other = ""
        if standard == "Verra":
            prop_other = st.text_area("Other entities involved", value=prop.get("other_entities", ""),
                                       key=f"setup_prop_other{sfx}_{project_id}",
                                       placeholder="Other organizations involved, their roles, and contact details...",
                                       height=68)
            _intel_source_label(intake, "proponent", "other_entities")

    return {
        "organization_name": prop_org,
        "contact_person": prop_contact,
        "email": prop_email,
        "phone": prop_phone,
        "address": prop_address,
        "other_entities": prop_other,
    }


SCALE_OPTIONS = ["", "Micro-scale", "Small-scale", "Large-scale"]
ACTIVITY_TYPE_OPTIONS = ["", "Greenfield", "Switch from existing", "Capacity addition", "Energy efficiency", "Other"]


def _render_intake_pdd(project_id, intake, standard="GoldStandard", methodology=None, methodology_settings=None):
    from carbongpt.core.methodology_rules import get_methodology_metadata, has_methodology_fuel_choices

    po = intake.get("project_overview", {})
    tech = intake.get("technology", {})
    loc = intake.get("location", {})
    ba = intake.get("baseline_additionality", {})
    mon = intake.get("monitoring", {})
    er = intake.get("emission_reductions", {})
    sdgs_data = intake.get("sdgs", {})
    stk = intake.get("stakeholders", {})
    safeg = intake.get("safeguards", {})
    prior = intake.get("prior_consideration", {})
    legal = intake.get("legal_compliance", {})

    meth_settings = methodology_settings or {}
    meth_meta = get_methodology_metadata(methodology)
    fuel_from_methodology = (
        has_methodology_fuel_choices(methodology)
        or bool(meth_settings.get("baseline_fuel"))
    )

    proponent_data = _render_proponent_card(project_id, intake, standard, prefix="pdd")

    if meth_meta:
        derived_parts = []
        if meth_meta.get("activity_type"):
            derived_parts.append(f"Activity type: **{meth_meta['activity_type']}**")
        if meth_meta.get("sectoral_scope"):
            derived_parts.append(f"Sectoral scope: **{meth_meta['sectoral_scope']}**")
        if meth_meta.get("scale_options"):
            derived_parts.append(f"Scale: **{', '.join(meth_meta['scale_options'])}**")
        if derived_parts:
            st.caption("Derived from methodology: " + " | ".join(derived_parts))

    with st.container(border=True):
        st.markdown("#### Project Facts")
        st.caption("Only provide facts unique to your project. The AI will draft everything else from your methodology and uploaded documents.")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            po_start_date = st.text_input("Project start date", value=po.get("start_date", ""),
                                           key=f"setup_po_start_{project_id}",
                                           placeholder="YYYY-MM-DD")
            _intel_source_label(intake, "project_overview", "start_date")
        with pc2:
            _meth_scale = (methodology_settings or {}).get("scale_classification", "")
            _po_scale_raw = po.get("scale", "")
            _effective_scale = _meth_scale or _po_scale_raw
            if _meth_scale:
                st.markdown(f"**Project scale:** {_meth_scale}")
                st.caption("Read-only — change in Methodology Choices below.")
                po_scale = _meth_scale
            else:
                available_scales = SCALE_OPTIONS
                if meth_meta and meth_meta.get("scale_options"):
                    available_scales = [""] + meth_meta["scale_options"]
                scale_idx = available_scales.index(_po_scale_raw) if _po_scale_raw in available_scales else 0
                po_scale = st.selectbox("Project scale", available_scales,
                                         index=scale_idx,
                                         key=f"setup_po_scale_{project_id}",
                                         format_func=lambda x: x if x else "Select scale...")
                _intel_source_label(intake, "project_overview", "scale")
        with pc3:
            _num_devices = po.get("num_devices")
            _num_units_legacy = po.get("num_units", "")
            if _num_devices is not None:
                st.markdown(f"**Devices deployed:** {int(_num_devices):,}")
                st.caption("Read-only — change in the Parameters tab.")
                po_num_units = str(int(_num_devices))
            else:
                po_num_units = st.text_input("Number of units", value=_num_units_legacy,
                                              key=f"setup_po_num_units_{project_id}",
                                              placeholder="e.g., 50,000 stoves")
                _intel_source_label(intake, "project_overview", "num_units")

    po_activity_type = meth_meta["activity_type"] if meth_meta and meth_meta.get("activity_type") else po.get("activity_type", "")
    po_sector = meth_meta["sectoral_scope"] if meth_meta and meth_meta.get("sectoral_scope") else po.get("sectoral_scope", "")

    with st.container(border=True):
        st.markdown("#### Technology & Approach")
        st.caption("AI document context only — these narrative fields guide the AI writing assistant. They do not affect calculations.")
        tech_desc = st.text_area("What is the project technology or intervention?", value=tech.get("description", ""),
                                  key=f"setup_tech_desc_{project_id}",
                                  placeholder="e.g., Distribution of improved biomass cookstoves to replace traditional three-stone fires...",
                                  height=80)
        _intel_source_label(intake, "technology", "description")
        tc1, tc2 = st.columns(2)
        with tc1:
            tech_manufacturer = st.text_input("Manufacturer / supplier", value=tech.get("manufacturer", ""),
                                               key=f"setup_tech_mfr_{project_id}",
                                               placeholder="e.g., BioLite, Tesla, Vestas")
            _intel_source_label(intake, "technology", "manufacturer")
            if fuel_from_methodology:
                _bl_from_meth = (methodology_settings or {}).get("baseline_fuel", "")
                _bl_display = _bl_from_meth or tech.get("fuel_baseline", tech.get("baseline_scenario", ""))
                tech_baseline_scenario = _bl_display
                if _bl_display:
                    st.markdown(f"**Baseline fuel:** {_bl_display}")
                    st.caption("Read-only — change in Methodology Choices below.")
                else:
                    st.caption("Baseline fuel: set in Methodology Choices below.")
            else:
                tech_baseline_scenario = st.text_input("Baseline practice / fuel", value=tech.get("fuel_baseline", tech.get("baseline_scenario", "")),
                                                    key=f"setup_tech_fuel_bl_{project_id}",
                                                    placeholder="e.g., Wood, Diesel, Grid electricity")
                _intel_source_label(intake, "technology", "fuel_baseline")
        with tc2:
            tech_model = st.text_input("Model / specification", value=tech.get("model", ""),
                                        key=f"setup_tech_model_{project_id}",
                                        placeholder="e.g., HomeStove 2, V150-4.2MW")
            _intel_source_label(intake, "technology", "model")
            if fuel_from_methodology:
                _pj_from_meth = (methodology_settings or {}).get("project_fuel", "")
                _pj_display = _pj_from_meth or tech.get("fuel_project", tech.get("project_scenario", ""))
                tech_project_scenario = _pj_display
                if _pj_display:
                    st.markdown(f"**Project fuel:** {_pj_display}")
                    st.caption("Read-only — change in Methodology Choices below.")
                else:
                    st.caption("Project fuel: set in Methodology Choices below.")
            else:
                tech_project_scenario = st.text_input("Project practice / fuel", value=tech.get("fuel_project", tech.get("project_scenario", "")),
                                                   key=f"setup_tech_fuel_pj_{project_id}",
                                                   placeholder="e.g., LPG, Solar PV, Improved cookstove")
                _intel_source_label(intake, "technology", "fuel_project")
        tech_distribution = st.text_input("Distribution / implementation method", value=tech.get("distribution_method", ""),
                                           key=f"setup_tech_dist_{project_id}",
                                           placeholder="e.g., Direct sales, Lease model, Government programme")
        _intel_source_label(intake, "technology", "distribution_method")

    with st.container(border=True):
        st.markdown("#### Location & Beneficiaries")
        st.caption("Region, coordinates, and country are set in the location section above.")
        loc_target = st.text_input("Target population", value=loc.get("target_population", ""),
                                    key=f"setup_loc_target_{project_id}",
                                    placeholder="e.g., Rural households in Northern Region")
        st.caption("AI document context only — used to describe the project beneficiary population.")
        _intel_source_label(intake, "location", "target_population")
        loc_regions = loc.get("regions", "")
        loc_coords = loc.get("coordinates", "")

    sdg_list = _render_sdg_section(project_id, sdgs_data, methodology_settings=meth_settings)

    with st.expander("Additional details (optional)", expanded=False):
        st.caption("The AI will draft these sections automatically. Only fill in if you have specific information the AI should use instead of generating.")

        st.markdown("**Baseline & Additionality**")
        ba_baseline = st.text_area("Baseline scenario", value=ba.get("baseline_scenario", ""),
                                    key=f"setup_ba_baseline_{project_id}",
                                    placeholder="Leave blank and the AI will describe the baseline from your methodology and project context...",
                                    height=68)
        ba_additionality = st.text_area("Additionality justification", value=ba.get("additionality_justification", ""),
                                         key=f"setup_ba_add_{project_id}",
                                         placeholder="Leave blank and the AI will draft the additionality argument...",
                                         height=68)

        if standard == "GoldStandard":
            st.markdown("**Prior Consideration (GS)**")
            prior_awareness = st.text_input("Date of awareness of carbon finance",
                                             value=prior.get("awareness_date", ""),
                                             key=f"setup_prior_aware_{project_id}",
                                             placeholder="YYYY-MM-DD")
            prior_funding = st.text_area("Funding sources",
                                          value=prior.get("funding_sources", ""),
                                          key=f"setup_prior_funding_{project_id}",
                                          placeholder="e.g., ODA 30%, carbon finance 40%, equity 30%...",
                                          height=68)

        st.markdown("**Monitoring**")
        mon_approach = st.text_area("Monitoring notes", value=mon.get("monitoring_approach", ""),
                                     key=f"setup_mon_approach_{project_id}",
                                     placeholder="Any project-specific monitoring details. The AI will use the methodology's monitoring requirements automatically...",
                                     height=68)

        st.markdown("**Stakeholder & Safeguards**")
        stk_consultation = st.text_area("Stakeholder consultation summary", value=stk.get("consultation_summary", ""),
                                         key=f"setup_stk_consult_{project_id}",
                                         placeholder="Brief summary of consultations held, if any...",
                                         height=68)

    result = {
        "proponent": proponent_data,
        "project_overview": {
            "start_date": po_start_date, "scale": po_scale, "num_units": po_num_units,
            "activity_type": po_activity_type, "sectoral_scope": po_sector,
        },
        "technology": {
            "description": tech_desc, "manufacturer": tech_manufacturer, "model": tech_model,
            "fuel_baseline": tech_baseline_scenario, "fuel_project": tech_project_scenario,
            "baseline_scenario": tech_baseline_scenario, "project_scenario": tech_project_scenario,
            "distribution_method": tech_distribution,
        },
        "location": {
            "regions": loc_regions, "coordinates": loc_coords,
            "target_population": loc_target,
        },
        "baseline_additionality": {
            "baseline_scenario": ba_baseline, "additionality_justification": ba_additionality,
            "barriers": ba.get("barriers", ""), "common_practice": ba.get("common_practice", ""),
        },
        "monitoring": {
            "monitoring_approach": mon_approach,
            "key_parameters": mon.get("key_parameters", ""),
            "sampling_approach": mon.get("sampling_approach", ""),
            "qa_qc": mon.get("qa_qc", ""),
        },
        "emission_reductions": {
            "annual_er_estimate": er.get("annual_er_estimate", ""),
            "total_er_estimate": er.get("total_er_estimate", ""),
            "calculation_approach": er.get("calculation_approach", ""),
            "er_summary": er.get("er_summary", ""),
        },
        "sdgs": {"selected_sdgs": sdg_list},
        "stakeholders": {
            "consultation_summary": stk_consultation,
            "grievance_mechanism": stk.get("grievance_mechanism", ""),
            "gender_assessment": stk.get("gender_assessment", ""),
        },
        "safeguards": {
            "environmental_safeguards": safeg.get("environmental_safeguards", ""),
            "social_safeguards": safeg.get("social_safeguards", ""),
            "do_no_harm": safeg.get("do_no_harm", ""),
        },
    }
    if standard == "GoldStandard":
        result["prior_consideration"] = {
            "awareness_date": prior_awareness if standard == "GoldStandard" else "",
            "evidence": prior.get("evidence", ""),
            "financial_need": prior.get("financial_need", ""),
            "funding_sources": prior_funding if standard == "GoldStandard" else "",
        }
    if standard == "Verra":
        result["legal_compliance"] = {
            "ownership": legal.get("ownership", ""),
            "regulatory_compliance": legal.get("regulatory_compliance", ""),
            "double_counting": legal.get("double_counting", ""),
            "audit_history": legal.get("audit_history", ""),
        }
    return result


def _render_intake_poa(project_id, intake, standard="GoldStandard"):
    prog = intake.get("programme", {})
    mgmt = intake.get("management_system", {})
    elig = intake.get("eligibility", {})
    mon = intake.get("monitoring", {})
    er = intake.get("emission_reductions", {})
    sdgs_data = intake.get("sdgs", {})
    stk = intake.get("stakeholders", {})
    safeg = intake.get("safeguards", {})

    proponent_data = _render_proponent_card(project_id, intake, standard, prefix="poa")

    with st.container(border=True):
        st.markdown("#### Programme Facts")
        st.caption("Provide the key facts about your programme. The AI will draft detailed sections from this and your methodology.")
        prog_objective = st.text_area("Programme objective", value=prog.get("objective", ""),
                                       key=f"setup_poa_objective_{project_id}",
                                       placeholder="What is the overall objective of this Programme of Activities?",
                                       height=68)
        prog_scope = st.text_input("Geographic scope", value=prog.get("geographic_scope", ""),
                                   key=f"setup_poa_scope_{project_id}",
                                   placeholder="Countries/regions covered by the programme")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            prog_cme = st.text_input("CME name", value=prog.get("cme_name", ""),
                                      key=f"setup_poa_cme_{project_id}",
                                      placeholder="Coordinating/Managing Entity")
        with pc2:
            prog_target_vpas = st.text_input("Target VPAs", value=prog.get("target_vpas", ""),
                                              key=f"setup_poa_target_vpas_{project_id}",
                                              placeholder="e.g., 15")
        with pc3:
            prog_duration = st.text_input("Duration (years)", value=prog.get("duration", ""),
                                           key=f"setup_poa_duration_{project_id}",
                                           placeholder="e.g., 28")

    with st.container(border=True):
        st.markdown("#### VPA Eligibility Criteria")
        elig_criteria = st.text_area("What criteria must a VPA meet to be included?", value=elig.get("criteria", ""),
                                      key=f"setup_poa_elig_{project_id}",
                                      placeholder="Define the eligibility criteria for VPA inclusion in this programme...",
                                      height=80)

    with st.container(border=True):
        st.markdown("#### Emission Reductions")
        ec1, ec2 = st.columns(2)
        with ec1:
            er_annual = st.text_input("Estimated annual ERs (tCO2e)", value=er.get("annual_er_estimate", ""),
                                       key=f"setup_poa_er_annual_{project_id}")
        with ec2:
            er_total = st.text_input("Total estimated ERs (tCO2e)", value=er.get("total_er_estimate", ""),
                                      key=f"setup_poa_er_total_{project_id}")

    _poa_meth = intake.get("programme", {}).get("methodology", "")
    sdg_list = _render_sdg_section(project_id, sdgs_data, methodology_hint=_poa_meth)

    with st.expander("Additional details (optional)", expanded=False):
        st.caption("The AI will draft these sections automatically. Only fill in if you have specific information.")

        st.markdown("**Management System**")
        mgmt_description = st.text_area("Management system description",
                                          value=mgmt.get("description", ""),
                                          key=f"setup_poa_mgmt_desc_{project_id}",
                                          placeholder="Leave blank and the AI will draft from programme context...",
                                          height=68)

        st.markdown("**Stakeholder & Safeguards**")
        stk_consultation = st.text_area("Stakeholder consultation summary", value=stk.get("consultation_summary", ""),
                                         key=f"setup_poa_stk_{project_id}",
                                         placeholder="Brief summary of consultations held...",
                                         height=68)

    return {
        "proponent": proponent_data,
        "programme": {
            "objective": prog_objective, "geographic_scope": prog_scope,
            "cme_name": prog_cme, "cme_details": prog.get("cme_details", ""),
            "target_vpas": prog_target_vpas,
            "duration": prog_duration, "first_submission_date": prog.get("first_submission_date", ""),
        },
        "management_system": {
            "description": mgmt_description,
            "multiple_technologies": mgmt.get("multiple_technologies", ""),
            "qa_qc": mgmt.get("qa_qc", ""),
        },
        "eligibility": {
            "criteria": elig_criteria,
            "inclusion_process": elig.get("inclusion_process", ""),
            "approval_mechanism": elig.get("approval_mechanism", ""),
        },
        "monitoring": {"monitoring_approach": mon.get("monitoring_approach", "")},
        "emission_reductions": {"annual_er_estimate": er_annual, "total_er_estimate": er_total},
        "sdgs": {"selected_sdgs": sdg_list},
        "stakeholders": {"consultation_summary": stk_consultation, "grievance_mechanism": stk.get("grievance_mechanism", "")},
        "safeguards": {"environmental_safeguards": safeg.get("environmental_safeguards", ""), "social_safeguards": safeg.get("social_safeguards", "")},
    }


def _render_intake_vpa(project_id, intake, standard="GoldStandard"):
    vpa = intake.get("vpa_details", {})
    tech = intake.get("technology", {})
    loc = intake.get("location", {})
    mon = intake.get("monitoring", {})
    er = intake.get("emission_reductions", {})

    proponent_data = _render_proponent_card(project_id, intake, standard, prefix="vpa")

    with st.container(border=True):
        st.markdown("#### VPA Facts")
        st.caption("Key facts about this VPA component. The AI will draft detailed sections from this and the parent PoA-DD.")
        vpa_elig = st.text_area("How this VPA meets PoA eligibility criteria", value=vpa.get("eligibility_justification", ""),
                                 key=f"setup_vpa_elig_{project_id}",
                                 placeholder="Explain how this VPA satisfies the eligibility criteria defined in the parent PoA-DD...",
                                 height=80)
        vc1, vc2 = st.columns(2)
        with vc1:
            vpa_start = st.text_input("VPA start date", value=vpa.get("start_date", ""),
                                       key=f"setup_vpa_start_{project_id}",
                                       placeholder="YYYY-MM-DD")
        with vc2:
            vpa_baseline = st.text_input("Baseline practice", value=vpa.get("baseline_scenario", ""),
                                          key=f"setup_vpa_baseline_{project_id}",
                                          placeholder="e.g., Three-stone fire, Diesel generator")

    with st.container(border=True):
        st.markdown("#### Technology & Location")
        tech_desc = st.text_area("Technology / approach", value=tech.get("description", ""),
                                  key=f"setup_vpa_tech_{project_id}",
                                  placeholder="What technology or intervention is used in this VPA?",
                                  height=68)
        tc1, tc2 = st.columns(2)
        with tc1:
            tech_manufacturer = st.text_input("Manufacturer", value=tech.get("manufacturer", ""),
                                               key=f"setup_vpa_mfr_{project_id}")
            loc_regions = st.text_input("Location / regions", value=loc.get("regions", ""),
                                         key=f"setup_vpa_regions_{project_id}",
                                         placeholder="Regions or districts for this VPA")
        with tc2:
            tech_model = st.text_input("Model", value=tech.get("model", ""),
                                        key=f"setup_vpa_model_{project_id}")
            loc_beneficiaries = st.text_input("Number of beneficiaries", value=loc.get("beneficiaries", ""),
                                               key=f"setup_vpa_bene_{project_id}",
                                               placeholder="e.g., 50,000 people")

    with st.container(border=True):
        st.markdown("#### Emission Reductions")
        ec1, ec2 = st.columns(2)
        with ec1:
            er_annual = st.text_input("Expected annual ERs (tCO2e)", value=er.get("annual_er_estimate", ""),
                                       key=f"setup_vpa_er_annual_{project_id}")
        with ec2:
            er_total = st.text_input("Expected total ERs (tCO2e)", value=er.get("total_er_estimate", ""),
                                      key=f"setup_vpa_er_total_{project_id}")

    return {
        "proponent": proponent_data,
        "vpa_details": {
            "eligibility_justification": vpa_elig, "start_date": vpa_start,
            "baseline_scenario": vpa_baseline,
        },
        "technology": {
            "description": tech_desc, "manufacturer": tech_manufacturer, "model": tech_model,
            "distribution_method": tech.get("distribution_method", ""),
        },
        "location": {
            "regions": loc_regions, "coordinates": loc.get("coordinates", ""),
            "target_population": loc.get("target_population", ""), "beneficiaries": loc_beneficiaries,
        },
        "monitoring": {"monitoring_approach": mon.get("monitoring_approach", "")},
        "emission_reductions": {"annual_er_estimate": er_annual, "total_er_estimate": er_total},
    }


def _render_intake_mr(project_id, intake, standard="GoldStandard"):
    period = intake.get("monitoring_period", {})
    impl = intake.get("implementation_status", {})
    data = intake.get("data_collection", {})
    deviations = intake.get("deviations", {})
    fars = intake.get("forward_action_requests", {})
    calibration = intake.get("calibration_data_quality", {})
    results = intake.get("results", {})

    proponent_data = _render_proponent_card(project_id, intake, standard, prefix="mr")

    st.info("Upload your PDD in the Documents tab so the AI can extract baseline, methodology, and monitoring details automatically.")

    with st.container(border=True):
        st.markdown("#### Monitoring Period")
        st.caption("The essential facts for this monitoring report. The AI will draft all sections from this, your PDD, and the methodology.")
        mp1, mp2, mp3 = st.columns(3)
        with mp1:
            period_start = st.text_input("Period start", value=period.get("start_date", ""),
                                          key=f"setup_mr_period_start_{project_id}",
                                          placeholder="YYYY-MM-DD")
        with mp2:
            period_end = st.text_input("Period end", value=period.get("end_date", ""),
                                        key=f"setup_mr_period_end_{project_id}",
                                        placeholder="YYYY-MM-DD")
        with mp3:
            period_number = st.text_input("Period number", value=period.get("period_number", ""),
                                           key=f"setup_mr_period_num_{project_id}",
                                           placeholder="e.g., 1, 2, 3")

    with st.container(border=True):
        st.markdown("#### Implementation Status")
        ic1, ic2 = st.columns(2)
        with ic1:
            impl_units_active = st.text_input("Active units / devices",
                                               value=impl.get("units_active", ""),
                                               key=f"setup_mr_impl_active_{project_id}",
                                               placeholder="e.g., 45,000")
        with ic2:
            impl_units_decommissioned = st.text_input("Decommissioned / replaced",
                                                       value=impl.get("units_decommissioned", ""),
                                                       key=f"setup_mr_impl_decom_{project_id}",
                                                       placeholder="e.g., 2,500")
        data_units = st.text_input("New installations this period",
                                    value=data.get("num_units", ""),
                                    key=f"setup_mr_units_{project_id}",
                                    placeholder="e.g., 10,000 stoves distributed")

    with st.container(border=True):
        st.markdown("#### Emission Reduction Results")
        rc1, rc2 = st.columns(2)
        with rc1:
            res_baseline = st.text_input("Baseline emissions (tCO2e)", value=results.get("baseline_emissions", ""),
                                          key=f"setup_mr_res_bl_{project_id}")
        with rc2:
            res_project = st.text_input("Project emissions (tCO2e)", value=results.get("project_emissions", ""),
                                         key=f"setup_mr_res_pj_{project_id}")
        rc3, rc4 = st.columns(2)
        with rc3:
            res_leakage = st.text_input("Leakage (tCO2e)", value=results.get("leakage", ""),
                                         key=f"setup_mr_res_leak_{project_id}")
        with rc4:
            res_net = st.text_input("Net ERs (tCO2e)", value=results.get("net_er", ""),
                                     key=f"setup_mr_res_net_{project_id}")

    with st.expander("Additional details (optional)", expanded=False):
        st.caption("The AI will draft these sections from your PDD and methodology. Only fill in if you have specific information.")

        st.markdown("**Forward Action Requests**")
        fars_previous = st.text_area("FARs from previous verification",
                                      value=fars.get("previous_fars", ""),
                                      key=f"setup_mr_fars_prev_{project_id}",
                                      placeholder="List any FARs that need to be addressed in this MR...",
                                      height=68)

        st.markdown("**Deviations**")
        dev_methodology = st.text_area("Deviations from PDD methodology", value=deviations.get("methodology_deviations", ""),
                                        key=f"setup_mr_dev_meth_{project_id}",
                                        placeholder="Only if there are deviations from the registered methodology...",
                                        height=68)

        st.markdown("**Data Collection Notes**")
        data_summary = st.text_area("Additional monitoring data notes", value=data.get("collection_summary", ""),
                                     key=f"setup_mr_data_summary_{project_id}",
                                     placeholder="Any notable findings, issues, or context about the monitoring data...",
                                     height=68)

    return {
        "proponent": proponent_data,
        "monitoring_period": {
            "start_date": period_start, "end_date": period_end,
            "period_number": period_number,
        },
        "implementation_status": {
            "status_description": impl.get("status_description", ""),
            "units_active": impl_units_active,
            "units_decommissioned": impl_units_decommissioned,
            "training_activities": impl.get("training_activities", ""),
        },
        "forward_action_requests": {
            "previous_fars": fars_previous,
            "response": fars.get("response", ""),
        },
        "data_collection": {
            "num_units": data_units, "collection_summary": data_summary,
            "data_highlights": data.get("data_highlights", ""),
        },
        "calibration_data_quality": {
            "calibration_records": calibration.get("calibration_records", ""),
            "data_sources": calibration.get("data_sources", ""),
        },
        "deviations": {
            "methodology_deviations": dev_methodology, "period_changes": deviations.get("period_changes", ""),
        },
        "results": {
            "baseline_emissions": res_baseline, "project_emissions": res_project,
            "leakage": res_leakage, "net_er": res_net,
        },
    }


def _render_intake_valver(project_id, intake, standard="GoldStandard"):
    scope = intake.get("scope", {})
    assessment = intake.get("assessment", {})
    findings = intake.get("findings", {})

    with st.container(border=True):
        st.markdown("#### Assessment Scope")
        scope_type = st.selectbox("Assessment type",
                                   ["Validation", "Verification", "Combined"],
                                   index=["Validation", "Verification", "Combined"].index(scope.get("assessment_type", "Validation"))
                                   if scope.get("assessment_type") in ["Validation", "Verification", "Combined"] else 0,
                                   key=f"setup_vv_type_{project_id}")
        scope_desc = st.text_area("Scope description", value=scope.get("scope_description", ""),
                                   key=f"setup_vv_scope_{project_id}",
                                   placeholder="Describe the scope of this validation/verification...",
                                   height=80)

    with st.container(border=True):
        st.markdown("#### Assessment Methodology")
        assess_method = st.text_area("Assessment methodology", value=assessment.get("methodology", ""),
                                      key=f"setup_vv_method_{project_id}",
                                      placeholder="Describe the assessment methodology used...",
                                      height=80)
        assess_site = st.text_area("Site visit details", value=assessment.get("site_visit", ""),
                                    key=f"setup_vv_site_{project_id}",
                                    placeholder="Details of site visits conducted...",
                                    height=80)
        assess_interviews = st.text_area("Interview records", value=assessment.get("interviews", ""),
                                          key=f"setup_vv_interviews_{project_id}",
                                          placeholder="Summary of interviews conducted...",
                                          height=80)

    with st.container(border=True):
        st.markdown("#### Key Findings")
        findings_summary = st.text_area("Findings summary", value=findings.get("summary", ""),
                                         key=f"setup_vv_findings_{project_id}",
                                         placeholder="Summary of key findings from the assessment...",
                                         height=100)
        findings_cars = st.text_area("CARs (Corrective Action Requests)", value=findings.get("cars", ""),
                                      key=f"setup_vv_cars_{project_id}",
                                      placeholder="List any Corrective Action Requests raised...",
                                      height=80)
        findings_cls = st.text_area("CLs (Clarification Requests)", value=findings.get("cls", ""),
                                     key=f"setup_vv_cls_{project_id}",
                                     placeholder="List any Clarification Requests raised...",
                                     height=80)

    return {
        "scope": {
            "assessment_type": scope_type, "scope_description": scope_desc,
        },
        "assessment": {
            "methodology": assess_method, "site_visit": assess_site,
            "interviews": assess_interviews,
        },
        "findings": {
            "summary": findings_summary, "cars": findings_cars, "cls": findings_cls,
        },
    }


_SDG_GOALS = [
    ("1", "No Poverty"),
    ("2", "Zero Hunger"),
    ("3", "Good Health and Well-being"),
    ("4", "Quality Education"),
    ("5", "Gender Equality"),
    ("6", "Clean Water and Sanitation"),
    ("7", "Affordable and Clean Energy"),
    ("8", "Decent Work and Economic Growth"),
    ("9", "Industry, Innovation and Infrastructure"),
    ("10", "Reduced Inequalities"),
    ("11", "Sustainable Cities and Communities"),
    ("12", "Responsible Consumption and Production"),
    ("13", "Climate Action"),
    ("14", "Life Below Water"),
    ("15", "Life on Land"),
    ("16", "Peace, Justice and Strong Institutions"),
    ("17", "Partnerships for the Goals"),
]

_SDG_INDICATORS = {
    "1": [
        "Reduction in household expenditure on fuel (USD/household/year)",
        "Share of household income saved on fuel (%)",
        "Number of households lifted above fuel poverty line",
    ],
    "3": [
        "Reduction in annual mean PM2.5 exposure (μg/m³)",
        "Reduction in carbon monoxide (CO) exposure (ppm)",
        "Reduction in indoor air pollution-related DALYs averted (DALYs/year)",
        "Number of premature deaths avoided from indoor air pollution (deaths/year)",
    ],
    "5": [
        "Reduction in time spent collecting fuelwood (hours/week/household)",
        "Reduction in time spent cooking (hours/day/household)",
        "Share of female project employees (%)",
    ],
    "6": [
        "Number of households with improved access to clean water",
        "Reduction in waterborne disease incidence (%)",
    ],
    "7": [
        "Number of households with access to clean cooking (households)",
        "Annual clean energy delivered (GJ/year)",
        "Cooking tier level achieved (WHO/World Bank Tier, scale 1-5)",
        "Number of devices distributed / installed",
    ],
    "8": [
        "Number of direct jobs created (FTE)",
        "Number of indirect / supply chain jobs created (FTE)",
        "Share of local sourcing for equipment / materials (%)",
    ],
    "13": [
        "Annual greenhouse gas emission reductions (tCO2e/year)",
        "Total emission reductions over crediting period (tCO2e)",
        "Fraction of non-renewable biomass (fNRB) in baseline (fraction 0–1)",
    ],
    "15": [
        "Annual reduction in wood fuel / charcoal consumption (tonnes/year)",
        "Area of forest protected from deforestation / degradation (ha)",
        "Fraction of non-renewable biomass (fNRB) reduction (fraction 0–1)",
    ],
}

_EVIDENCE_TIERS = [
    "Tier 1 — Directly monitored",
    "Tier 2 — Default / conservative estimate",
    "Tier 3 — Modelled / calculated",
]

_COOKSTOVE_CORE_SDGS = {"1", "3", "5", "7", "13"}
_COOKSTOVE_WOOD_SDGS = {"1", "3", "5", "7", "13", "15"}


def _render_sdg_section(project_id, sdgs_data, methodology_settings=None, methodology_hint=""):
    meth_s = methodology_settings or {}
    baseline_fuel = meth_s.get("baseline_fuel", "").lower()
    is_cookstove = bool(
        meth_s.get("calculation_method")
        or meth_s.get("baseline_fuel")
        or "tpddtec" in str(methodology_hint).lower()
        or "mecd" in str(methodology_hint).lower()
        or "cookstove" in str(methodology_hint).lower()
    )
    suggested_sdgs = _COOKSTOVE_WOOD_SDGS if (is_cookstove and baseline_fuel in ("wood", "charcoal", "biomass", "crop residues")) else (
        _COOKSTOVE_CORE_SDGS if is_cookstove else set()
    )

    existing_sdgs = sdgs_data.get("selected_sdgs", [])
    existing_map = {}
    for s in existing_sdgs:
        gn = str(s.get("goal_number", ""))
        existing_map[gn] = s

    with st.container(border=True):
        st.markdown("#### SDGs & Co-benefits")

        if suggested_sdgs:
            _sugg_key = f"sdg_suggestion_applied_{project_id}"
            _already_have = bool(existing_map)
            if not _already_have and _sugg_key not in st.session_state:
                st.info(
                    f"Cookstove projects commonly report SDGs "
                    f"{', '.join(sorted(suggested_sdgs, key=int))}. "
                    f"Click below to pre-select them."
                )
                if st.button("Pre-select suggested SDGs", key=f"sdg_apply_sugg_{project_id}"):
                    st.session_state[_sugg_key] = True
                    st.rerun()
            elif not _already_have and _sugg_key in st.session_state:
                st.caption(f"Suggested SDGs pre-selected: {', '.join(sorted(suggested_sdgs, key=int))}.")
        else:
            st.caption("Select the SDGs this project contributes to and fill in the indicator data for each.")

        sdg_list = []

        for goal_num, goal_name in _SDG_GOALS:
            default_selected = (
                goal_num in existing_map
                or (not existing_map and goal_num in suggested_sdgs and f"sdg_suggestion_applied_{project_id}" in st.session_state)
            )
            is_selected = st.checkbox(
                f"SDG {goal_num} — {goal_name}",
                value=default_selected,
                key=f"setup_sdg_{project_id}_{goal_num}",
            )
            if not is_selected:
                continue

            existing_entry = existing_map.get(goal_num, {})
            existing_indicators = existing_entry.get("indicators", [])
            old_contrib = existing_entry.get("contribution_description", "")

            with st.container(border=True):
                indicator_options = _SDG_INDICATORS.get(goal_num, [])
                indicator_options_with_other = indicator_options + ["Other (specify)"]

                existing_ind_name = existing_indicators[0].get("indicator_name", "") if existing_indicators else ""
                if existing_ind_name and existing_ind_name not in indicator_options:
                    ind_default_idx = len(indicator_options)
                else:
                    ind_default_idx = indicator_options.index(existing_ind_name) if existing_ind_name in indicator_options else 0

                if indicator_options:
                    ind_choice = st.selectbox(
                        f"Key indicator for SDG {goal_num}",
                        indicator_options_with_other,
                        index=ind_default_idx,
                        key=f"setup_sdg_ind_{project_id}_{goal_num}",
                    )
                    if ind_choice == "Other (specify)":
                        ind_name = st.text_input(
                            "Specify indicator name (include unit)",
                            value=existing_ind_name if existing_ind_name not in indicator_options else "",
                            key=f"setup_sdg_ind_custom_{project_id}_{goal_num}",
                            placeholder="e.g. Number of women trained (count)",
                        )
                    else:
                        ind_name = ind_choice
                else:
                    ind_name = st.text_input(
                        "Indicator name (include unit)",
                        value=existing_ind_name,
                        key=f"setup_sdg_ind_name_{project_id}_{goal_num}",
                        placeholder="e.g. Reduction in PM2.5 exposure (μg/m³)",
                    )

                val_c1, val_c2 = st.columns(2)
                with val_c1:
                    baseline_val = st.text_input(
                        "Baseline value",
                        value=existing_indicators[0].get("baseline_value", "") if existing_indicators else "",
                        key=f"setup_sdg_bl_{project_id}_{goal_num}",
                        placeholder="e.g. 245",
                    )
                with val_c2:
                    project_val = st.text_input(
                        "Project / target value",
                        value=existing_indicators[0].get("project_value", "") if existing_indicators else "",
                        key=f"setup_sdg_pv_{project_id}_{goal_num}",
                        placeholder="e.g. 35",
                    )

                existing_tier = existing_indicators[0].get("evidence_tier", _EVIDENCE_TIERS[1]) if existing_indicators else _EVIDENCE_TIERS[1]
                tier_idx = _EVIDENCE_TIERS.index(existing_tier) if existing_tier in _EVIDENCE_TIERS else 1
                evidence_tier = st.selectbox(
                    "Evidence tier",
                    _EVIDENCE_TIERS,
                    index=tier_idx,
                    key=f"setup_sdg_tier_{project_id}_{goal_num}",
                )

                measurement = st.text_area(
                    "Measurement / monitoring approach",
                    value=existing_indicators[0].get("measurement_approach", "") if existing_indicators else old_contrib,
                    key=f"setup_sdg_meas_{project_id}_{goal_num}",
                    placeholder="How will this indicator be measured and monitored?",
                    height=68,
                )

            sdg_list.append({
                "goal_number": goal_num,
                "contribution_description": measurement,
                "indicators": [{
                    "indicator_name": ind_name,
                    "baseline_value": baseline_val,
                    "project_value": project_val,
                    "evidence_tier": evidence_tier,
                    "measurement_approach": measurement,
                }],
            })

    return sdg_list


def _render_project_settings(project):
    project_id = project["id"]
    project_type = project.get("project_type", "standalone_pdd")
    intake = project.get("project_intake") or {}
    if isinstance(intake, str):
        import json as _json
        intake = _json.loads(intake)

    st.markdown(f"""
    <span class="section-header">
        <span class="section-header-icon section-header-icon-teal">{SVG_ICONS.get("setup", "")}</span>
        <span class="section-header-text">Project Setup</span>
    </span>
    """, unsafe_allow_html=True)
    st.caption("Fill in the details below. This data will be used by the AI when drafting and reviewing your documents.")

    with st.container(border=True):
        st.markdown("#### About Your Project")
        new_name = st.text_input("Project name", value=project.get("name", ""),
                                  key=f"setup_name_{project_id}")
        new_standard = st.selectbox("Standard", STANDARD_OPTIONS,
                                     index=STANDARD_OPTIONS.index(project.get("standard", "GoldStandard"))
                                     if project.get("standard") in STANDARD_OPTIONS else 0,
                                     key=f"setup_standard_{project_id}")
        st.markdown("**Location**")
        setup_loc = _render_location_section(f"setup_{project_id}", project)
        new_country = setup_loc["country"]

        # If methodology was set via the TPDDTEC wizard, show it as read-only info
        # rather than showing a blank selector that confuses the user.
        _meth_settings = project.get("methodology_settings") or {}
        _tpddtec_active = bool(_meth_settings.get("baseline_fuel") and _meth_settings.get("calculation_method"))
        if _tpddtec_active:
            with st.container(border=True):
                st.caption("Methodology (set via wizard)")
                _calc = _meth_settings.get("method_selection") or _meth_settings.get("calculation_method", "")
                _bl = _meth_settings.get("baseline_fuel", "")
                _pj = _meth_settings.get("project_fuel", "")
                _sc = _meth_settings.get("scale_classification", "")
                st.markdown(f"**TPDDTEC v4.0** — {_calc}")
                if _bl or _pj:
                    st.caption(f"Baseline: {_bl} | Project: {_pj}" + (f" | {_sc}" if _sc else ""))
                st.caption("Change fuel and scale choices in Methodology Choices below.")
            new_methodology = project.get("methodology") or ""
        else:
            new_methodology = _methodology_selector(
                f"setup_{project_id}", standard=new_standard,
                current_value=project.get("methodology"))
            meth_detail = None
            if new_methodology:
                meth_detail = _fetch(f"/projects/methodologies/{new_methodology}")
            if meth_detail:
                with st.container(border=True):
                    st.caption("Selected methodology")
                    meth_name = meth_detail.get("name") or ""
                    meth_code = meth_detail.get("code", "")
                    meth_version = meth_detail.get("version") or ""
                    header = f"**{meth_code}**"
                    if meth_version:
                        header += f" v{meth_version}"
                    if meth_name:
                        header += f" - {meth_name}"
                    st.markdown(header)
                    detail_parts = []
                    if meth_detail.get("standard"):
                        std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS", "CDM": "CDM"}.get(meth_detail["standard"], meth_detail["standard"])
                        detail_parts.append(f"Standard: {std_display}")
                    if meth_detail.get("sector"):
                        detail_parts.append(f"Sector: {meth_detail['sector']}")
                    if meth_detail.get("category"):
                        detail_parts.append(f"Category: {meth_detail['category']}")
                    if detail_parts:
                        st.markdown(" | ".join(detail_parts))
                    if meth_detail.get("applicability"):
                        st.markdown(f"Applicability: {meth_detail['applicability']}")
                    if meth_detail.get("status") == "deprecated":
                        st.warning(f"This methodology is deprecated. Superseded by: {meth_detail.get('superseded_by', 'N/A')}")

        new_desc = st.text_area("Project description / objective", value=project.get("description", "") or "",
                                 key=f"setup_desc_{project_id}",
                                 placeholder="Briefly describe the project activity and its objective...")
        new_status = st.selectbox("Project status", list(STATUS_LABELS.keys()),
                                   format_func=lambda x: STATUS_LABELS[x],
                                   index=list(STATUS_LABELS.keys()).index(project.get("status", "draft"))
                                   if project.get("status") in STATUS_LABELS else 0,
                                   key=f"setup_status_{project_id}")

    intake_data = _render_intake_by_type(project_id, project_type, intake, standard=new_standard, methodology=new_methodology, methodology_settings=project.get("methodology_settings") or {})

    st.divider()
    st.subheader("Crediting Period")

    from datetime import date as _date
    from carbongpt.core.methodology_rules import get_crediting_period_default

    cp_start_raw = project.get("crediting_period_start")
    cp_start_val = None
    if cp_start_raw:
        try:
            if isinstance(cp_start_raw, str):
                cp_start_val = _date.fromisoformat(cp_start_raw[:10])
            else:
                cp_start_val = cp_start_raw
        except Exception:
            pass
    cp_start = st.date_input(
        "Crediting period start date",
        value=cp_start_val,
        key=f"setup_cp_start_{project_id}",
    )
    saved_cp_years = project.get("crediting_period_years")
    cp_default = saved_cp_years if saved_cp_years else get_crediting_period_default(new_standard)
    cp_years = st.number_input(
        "Crediting period (years)",
        min_value=1, max_value=30,
        value=cp_default,
        key=f"setup_cp_years_{project_id}",
    )
    if cp_start:
        cp_end = _date(cp_start.year + cp_years, cp_start.month, cp_start.day) if cp_start else None
        if cp_end:
            st.caption(f"Crediting period: {cp_start.isoformat()} to {cp_end.isoformat()} ({cp_years} years)")
            vintages = [str(cp_start.year + i) for i in range(cp_years)]
            st.caption(f"Vintages: {', '.join(vintages)}")

    existing_settings = project.get("project_settings") or {}

    meth_parsed = None
    methodology = new_methodology or project.get("methodology")
    if methodology:
        meth_data = _fetch(f"/projects/{project_id}/methodology-data")
        if meth_data and meth_data.get("status") == "ready":
            meth_parsed = meth_data.get("parsed")

    new_settings = dict(existing_settings)
    meth_layer_inputs = {}
    if meth_parsed:
        has_params = meth_parsed.get("parameters") or meth_parsed.get("context_dimensions") or meth_parsed.get("calculation_methods")
        if has_params:
            st.divider()
            st.subheader("Methodology-Specific Setup")
            st.caption("These fields are derived from the selected methodology's requirements. They feed directly into the AI writer for accurate, methodology-compliant content.")
            new_settings, meth_layer_inputs = _render_methodology_layer(
                project_id, meth_parsed, existing_settings, intake,
                country=new_country or project.get("country", "")
            )
    elif methodology:
        st.divider()
        st.info("Methodology data is not yet available for this methodology. AI-trained methodologies will show their specific parameters, equations, and default values here.")

    _mecd_basket_data = None
    _project_methodology = new_methodology or project.get("methodology", "")
    if _project_methodology and "MECD" in _project_methodology.upper():
        st.divider()
        st.subheader("Baseline Fuel Basket (MECD)")
        with st.container(border=True):
            st.caption(
                "Authoritative editable — define the mix of fuels currently used by target households. "
                "Shares must sum to 100%. This data feeds the baseline emission factor calculation."
            )
            _MECD_FUEL_OPTIONS = [
                ("wood", "Wood / Firewood"),
                ("charcoal", "Charcoal"),
                ("kerosene", "Kerosene"),
                ("lpg", "LPG"),
                ("crop_residues", "Crop residues"),
                ("dung", "Animal dung"),
                ("coal", "Coal"),
                ("other", "Other"),
            ]
            _existing_basket = intake.get("baseline_fuels") or []
            _basket_rows = []
            st.caption("Add each fuel currently used by target households and its percentage share.")
            _num_basket = st.number_input(
                "Number of baseline fuels",
                min_value=1, max_value=8, value=max(1, len(_existing_basket)),
                key=f"mecd_num_fuels_{project_id}",
                step=1,
            )
            _basket_total = 0.0
            for _bi in range(int(_num_basket)):
                _brow = _existing_basket[_bi] if _bi < len(_existing_basket) else {}
                _bc1, _bc2 = st.columns([2, 1])
                with _bc1:
                    _bfuel_opts = [f[0] for f in _MECD_FUEL_OPTIONS]
                    _bfuel_labels = {f[0]: f[1] for f in _MECD_FUEL_OPTIONS}
                    _cur_fuel = _brow.get("fuel_key", _bfuel_opts[_bi % len(_bfuel_opts)])
                    _bfuel_idx = _bfuel_opts.index(_cur_fuel) if _cur_fuel in _bfuel_opts else 0
                    _bfuel = st.selectbox(
                        f"Fuel {_bi + 1}",
                        _bfuel_opts,
                        index=_bfuel_idx,
                        format_func=lambda x: _bfuel_labels.get(x, x),
                        key=f"mecd_fuel_{project_id}_{_bi}",
                    )
                with _bc2:
                    _bshare = st.number_input(
                        f"Share % (fuel {_bi + 1})",
                        min_value=0.0, max_value=100.0,
                        value=float(_brow.get("share_pct", 0.0)),
                        step=1.0, format="%.1f",
                        key=f"mecd_share_{project_id}_{_bi}",
                    )
                _basket_rows.append({"fuel_key": _bfuel, "share_pct": _bshare})
                _basket_total += _bshare

            if abs(_basket_total - 100.0) < 0.5:
                st.success(f"Total: {_basket_total:.1f}% — basket is valid.")
            else:
                st.warning(f"Total: {_basket_total:.1f}% — shares must sum to 100%.")

            try:
                from carbongpt.core.mecd_simulator import compute_mecd_baseline_ef
                _dom = max(_basket_rows, key=lambda r: r["share_pct"]) if _basket_rows else None
                if _dom and abs(_basket_total - 100.0) < 0.5:
                    _mecd_case = "2" if _dom["fuel_key"] == "charcoal" else "1"
                    _bf_result = compute_mecd_baseline_ef(_mecd_case, _basket_rows)
                    if isinstance(_bf_result, dict):
                        _ef_val = _bf_result.get("EF_b_useful") or _bf_result.get("EF_b_input") or _bf_result.get("value")
                        if _ef_val is not None:
                            st.caption(
                                f"Derived baseline EF: ~{float(_ef_val):.4f} tCO2e/TJ "
                                f"(dominant fuel: {_dom['fuel_key']}, Eq. {_mecd_case})"
                            )
            except Exception:
                pass

            _mecd_basket_data = _basket_rows if abs(_basket_total - 100.0) < 0.5 else None

    st.divider()

    if st.button("Save All Changes", key=f"save_setup_{project_id}", type="primary"):
        methodology_changed = new_methodology != project.get("methodology")
        if methodology_changed:
            intake_data["methodology_parameters"] = meth_layer_inputs if meth_layer_inputs else {}
            dim_keys_to_keep = set()
            if meth_parsed:
                for dim in meth_parsed.get("context_dimensions", []):
                    dk = dim.get("dimension_key", "")
                    if dk:
                        dim_keys_to_keep.add(dk)
                dim_keys_to_keep.add("calculation_method")
            new_settings = {k: v for k, v in new_settings.items() if k in dim_keys_to_keep}
        elif meth_layer_inputs:
            intake_data["methodology_parameters"] = meth_layer_inputs

        fuel_dim_map = {
            "baseline_fuel": ("fuel_baseline", "baseline_scenario"),
            "project_fuel": ("fuel_project", "project_scenario"),
        }
        if meth_parsed:
            for dim in meth_parsed.get("context_dimensions", []):
                dk = dim.get("dimension_key", "")
                if dk in fuel_dim_map and new_settings.get(dk):
                    if "technology" not in intake_data:
                        intake_data["technology"] = {}
                    for field in fuel_dim_map[dk]:
                        intake_data["technology"][field] = new_settings[dk]
        else:
            for dk, fields in fuel_dim_map.items():
                if new_settings.get(dk):
                    if "technology" not in intake_data:
                        intake_data["technology"] = {}
                    for field in fields:
                        intake_data["technology"][field] = new_settings[dk]

        if _mecd_basket_data is not None:
            intake_data["baseline_fuels"] = _mecd_basket_data

        update_payload = {
            "name": new_name,
            "standard": new_standard,
            "methodology": new_methodology,
            "country": new_country or None,
            "description": new_desc or None,
            "status": new_status,
            "crediting_period_years": cp_years,
            "project_settings": new_settings,
            "project_intake": intake_data,
            "location_name": setup_loc.get("location_name"),
            "region": setup_loc.get("region"),
            "district": setup_loc.get("district"),
            "latitude": setup_loc.get("latitude"),
            "longitude": setup_loc.get("longitude"),
            "boundary_geojson": setup_loc.get("boundary_geojson"),
        }
        if cp_start:
            update_payload["crediting_period_start"] = cp_start.isoformat()
        _fetch(f"/projects/{project_id}", method="PATCH", json=update_payload)
        st.success("Project updated.")
        time.sleep(0.5)
        st.rerun()

    st.divider()
    st.subheader("Danger Zone")
    if st.button("Delete Project", key=f"delete_proj_{project_id}", type="secondary"):
        st.session_state[f"confirm_delete_{project_id}"] = True

    if st.session_state.get(f"confirm_delete_{project_id}"):
        st.warning("Are you sure? This will delete the project and all its documents.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, delete", key=f"confirm_del_yes_{project_id}"):
                _fetch(f"/projects/{project_id}", method="DELETE")
                st.session_state.selected_project_id = None
                st.session_state.pop(f"confirm_delete_{project_id}", None)
                st.rerun()
        with col2:
            if st.button("Cancel", key=f"confirm_del_no_{project_id}"):
                st.session_state.pop(f"confirm_delete_{project_id}", None)
                st.rerun()


def _render_project_settings_legacy(project):
    project_id = project["id"]
    st.subheader("Project Settings")

    new_name = st.text_input("Project name", value=project.get("name", ""),
                              key=f"settings_name_{project_id}")
    new_standard = st.selectbox("Standard", STANDARD_OPTIONS,
                                 index=STANDARD_OPTIONS.index(project.get("standard", "GoldStandard"))
                                 if project.get("standard") in STANDARD_OPTIONS else 0,
                                 key=f"settings_standard_{project_id}")
    new_methodology = _methodology_selector(
        f"settings_{project_id}", standard=new_standard,
        current_value=project.get("methodology"))

    if not new_methodology:
        desc_for_recs = project.get("description", "")
        country_for_recs = project.get("country", "")
        rec_text = f"{desc_for_recs} {country_for_recs}".strip()
        if rec_text and len(rec_text) > 3:
            from carbongpt.core.copilot import recommend_methodologies
            recs = recommend_methodologies(description=rec_text)
            if recs:
                st.markdown("**Recommended Methodologies**")
                for r in recs[:3]:
                    with st.container(border=True):
                        st.markdown(f"**{r['code']}** ({r['standard']})")
                        st.caption(r["reason"])

    meth_detail = None
    if new_methodology:
        meth_detail = _fetch(f"/projects/methodologies/{new_methodology}")
    if meth_detail:
        with st.container(border=True):
            st.caption("Selected methodology")
            meth_name = meth_detail.get("name") or ""
            meth_code = meth_detail.get("code", "")
            meth_version = meth_detail.get("version") or ""
            header = f"**{meth_code}**"
            if meth_version:
                header += f" v{meth_version}"
            if meth_name:
                header += f" - {meth_name}"
            st.markdown(header)
            detail_parts = []
            if meth_detail.get("standard"):
                std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS", "CDM": "CDM"}.get(meth_detail["standard"], meth_detail["standard"])
                detail_parts.append(f"Standard: {std_display}")
            if meth_detail.get("sector"):
                detail_parts.append(f"Sector: {meth_detail['sector']}")
            if meth_detail.get("category"):
                detail_parts.append(f"Category: {meth_detail['category']}")
            if detail_parts:
                st.markdown(" | ".join(detail_parts))
            if meth_detail.get("applicability"):
                st.markdown(f"Applicability: {meth_detail['applicability']}")
            if meth_detail.get("status") == "deprecated":
                st.warning(f"This methodology is deprecated. Superseded by: {meth_detail.get('superseded_by', 'N/A')}")

    st.markdown("**Location**")
    settings_loc = _render_location_section(f"settings_{project_id}", project)
    new_country = settings_loc["country"]
    new_desc = st.text_area("Description", value=project.get("description", "") or "",
                             key=f"settings_desc_{project_id}")
    new_status = st.selectbox("Status", list(STATUS_LABELS.keys()),
                               format_func=lambda x: STATUS_LABELS[x],
                               index=list(STATUS_LABELS.keys()).index(project.get("status", "draft"))
                               if project.get("status") in STATUS_LABELS else 0,
                               key=f"settings_status_{project_id}")

    st.divider()
    st.subheader("Crediting Period")

    from datetime import date as _date

    cp_start_raw = project.get("crediting_period_start")
    cp_start_val = None
    if cp_start_raw:
        try:
            if isinstance(cp_start_raw, str):
                cp_start_val = _date.fromisoformat(cp_start_raw[:10])
            else:
                cp_start_val = cp_start_raw
        except Exception:
            pass
    cp_start = st.date_input(
        "Crediting period start date",
        value=cp_start_val,
        key=f"settings_cp_start_{project_id}",
    )
    cp_years = st.number_input(
        "Crediting period (years)",
        min_value=1, max_value=30,
        value=project.get("crediting_period_years") or 7,
        key=f"settings_cp_years_{project_id}",
    )
    if cp_start:
        from datetime import timedelta
        cp_end = _date(cp_start.year + cp_years, cp_start.month, cp_start.day) if cp_start else None
        if cp_end:
            st.caption(f"Crediting period: {cp_start.isoformat()} to {cp_end.isoformat()} ({cp_years} years)")
            vintages = [str(cp_start.year + i) for i in range(cp_years)]
            st.caption(f"Vintages: {', '.join(vintages)}")

    existing_settings = project.get("project_settings") or {}

    meth_parsed = None
    methodology = project.get("methodology")
    if methodology:
        meth_data = _fetch(f"/projects/{project_id}/methodology-data")
        if meth_data and meth_data.get("status") == "ready":
            meth_parsed = meth_data.get("parsed")

    new_settings = dict(existing_settings)
    context_dims = []
    if meth_parsed:
        context_dims = meth_parsed.get("context_dimensions", [])

    if context_dims:
        st.divider()
        st.subheader("Methodology Parameters")
        st.caption("These settings determine which default values are used in calculations.")

        for dim in context_dims:
            dim_key = dim["dimension_key"]
            options = dim["options"]
            current_val = existing_settings.get(dim_key, "")
            idx = 0
            if current_val in options:
                idx = options.index(current_val)
            selected = st.selectbox(
                dim["label"],
                options,
                index=idx,
                key=f"settings_dim_{project_id}_{dim_key}",
                help=dim.get("description", ""),
            )
            new_settings[dim_key] = selected

    st.divider()

    if st.button("Save Changes", key=f"save_settings_{project_id}", type="primary"):
        update_payload = {
            "name": new_name,
            "standard": new_standard,
            "methodology": new_methodology,
            "country": new_country or None,
            "description": new_desc or None,
            "status": new_status,
            "crediting_period_years": cp_years,
            "project_settings": new_settings,
            "location_name": settings_loc.get("location_name"),
            "region": settings_loc.get("region"),
            "district": settings_loc.get("district"),
            "latitude": settings_loc.get("latitude"),
            "longitude": settings_loc.get("longitude"),
            "boundary_geojson": settings_loc.get("boundary_geojson"),
        }
        if cp_start:
            update_payload["crediting_period_start"] = cp_start.isoformat()
        _fetch(f"/projects/{project_id}", method="PATCH", json=update_payload)
        st.success("Project updated.")
        time.sleep(0.5)
        st.rerun()

    st.divider()
    st.subheader("Danger Zone")
    if st.button("Delete Project", key=f"delete_proj_{project_id}", type="secondary"):
        st.session_state[f"confirm_delete_{project_id}"] = True

    if st.session_state.get(f"confirm_delete_{project_id}"):
        st.warning("Are you sure? This will delete the project and all its documents.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, delete", key=f"confirm_del_yes_{project_id}"):
                _fetch(f"/projects/{project_id}", method="DELETE")
                st.session_state.selected_project_id = None
                st.session_state.pop(f"confirm_delete_{project_id}", None)
                st.rerun()
        with col2:
            if st.button("Cancel", key=f"confirm_del_no_{project_id}"):
                st.session_state.pop(f"confirm_delete_{project_id}", None)
                st.rerun()


COPILOT_ACTION_ICONS = {
    "create_project": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14"/><path d="M5 12h14"/></svg>',
    "initialize_parameters": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" x2="4" y1="21" y2="14"/><line x1="4" x2="4" y1="10" y2="3"/><line x1="12" x2="12" y1="21" y2="12"/><line x1="12" x2="12" y1="8" y2="3"/><line x1="20" x2="20" y1="21" y2="16"/><line x1="20" x2="20" y1="12" y2="3"/></svg>',
    "run_er_simulation": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>',
    "draft_section": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>',
    "run_audit": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>',
    "run_review": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    "suggest_methodology": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2Z"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
    "get_project_status": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>',
    "navigate": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>',
}

COPILOT_ACTION_LABELS = {
    "create_project": "Project Created",
    "initialize_parameters": "Parameters Initialized",
    "run_er_simulation": "ER Simulation Complete",
    "draft_section": "Section Drafted",
    "run_audit": "Audit Complete",
    "run_review": "Review Ready",
    "suggest_methodology": "Methodology Recommendations",
    "get_project_status": "Project Status",
    "navigate": "Navigation",
}


def _render_chat_widget():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False
    if "chat_actions" not in st.session_state:
        st.session_state.chat_actions = {}

    project_id = st.session_state.get("selected_project_id")
    project_name = ""
    if project_id:
        proj = _fetch(f"/projects/{project_id}")
        if proj:
            project_name = proj.get("name", "")

    if not st.session_state.chat_open:
        cta_cols = st.columns([5, 1.2])
        with cta_cols[1]:
            if st.button("AI Copilot", key="chat_toggle_btn", type="primary", use_container_width=True):
                st.session_state.chat_open = True
                st.rerun()
        return

    close_cols = st.columns([5, 1.2])
    with close_cols[0]:
        context_badge = ""
        if project_name:
            context_badge = f'<span class="chat-context-badge">Project: {project_name}</span>'
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:8px;padding-top:6px;">'
            f'<div style="background:var(--brand-primary);color:white;width:28px;height:28px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;font-size:0.7rem;font-weight:700;flex-shrink:0;">AI</div>'
            f'<span style="font-weight:600;font-size:0.95rem;color:var(--text-primary);">CarbonGPT Copilot</span>'
            f'{context_badge}</div>',
            unsafe_allow_html=True,
        )
    with close_cols[1]:
        if st.button("Close", key="chat_toggle_btn", use_container_width=True):
            st.session_state.chat_open = False
            st.rerun()

    st.markdown("---")

    chat_container = st.container(height=400)
    with chat_container:
        if not st.session_state.chat_history:
            greeting = "Hello! I'm your CarbonGPT Copilot. I can help you manage your entire carbon project through conversation."
            if project_name:
                greeting += f"\n\nCurrently working on: **{project_name}**"
            greeting += (
                "\n\nTry asking me to:"
                "\n- Create a new cookstove project in Ghana"
                "\n- Estimate emission reductions"
                "\n- Draft a PDD section"
                "\n- Run an audit simulation"
                "\n- Check project status"
                "\n- Recommend a methodology"
                "\n\nWhat would you like to do?"
            )
            with st.chat_message("assistant"):
                st.markdown(greeting)

        for idx, msg in enumerate(st.session_state.chat_history):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            with st.chat_message(role):
                st.markdown(content)

            action_data = st.session_state.chat_actions.get(idx)
            if action_data and role == "assistant":
                action_type = action_data.get("action", "")
                action_success = action_data.get("success", True)
                icon = COPILOT_ACTION_ICONS.get(action_type, COPILOT_ACTION_ICONS.get("navigate", ""))
                label = COPILOT_ACTION_LABELS.get(action_type, "Action")
                action_msg = action_data.get("message", "")
                error_class = " copilot-action-error" if not action_success else ""
                st.markdown(f"""
                <span class="copilot-action-card{error_class}" data-testid="copilot-action-card">
                    <span class="copilot-action-icon">{icon}</span>
                    <span>
                        <span class="copilot-action-label">{label}</span>
                        <span class="copilot-action-text">{action_msg}</span>
                    </span>
                </span>
                """, unsafe_allow_html=True)

    nav_pending = st.session_state.get("copilot_nav_pending")
    if nav_pending:
        nav_col1, nav_col2 = st.columns([3, 1])
        with nav_col2:
            def _copilot_nav(pid, pending):
                if pid:
                    st.session_state[f"ws_tab_{pid}"] = pending.get("index", 0)
                if pending.get("new_project_id"):
                    st.session_state.selected_project_id = pending["new_project_id"]
                st.session_state.copilot_nav_pending = None

            st.button(f"Go to {nav_pending['tab']}", key="copilot_nav_btn", type="primary", use_container_width=True,
                      on_click=_copilot_nav, args=(project_id, nav_pending))

    chip_col = st.columns(1)[0]
    with chip_col:
        chip_cols = st.columns(6)
        chip_suggestions = [
            ("Project Status", "What's my project status?"),
            ("Estimate ERs", "Estimate emission reductions for my project"),
            ("Draft PDD", "Draft a PDD section"),
            ("Run Audit", "Run an audit simulation"),
            ("Suggest Methodology", "Which methodology should I use for my project?"),
            ("Help", "What can you do?"),
        ]
        for i, (label, prompt) in enumerate(chip_suggestions):
            with chip_cols[i]:
                if st.button(label, key=f"chip_{i}", use_container_width=True):
                    st.session_state.chat_chip_send = prompt
                    st.rerun()

    ic1, ic2, ic3 = st.columns([5, 0.7, 0.7])
    with ic1:
        user_input = st.text_input(
            "Message",
            key="chat_input",
            placeholder="Tell me what to do... e.g. 'Create a cookstove project in Kenya'",
            label_visibility="collapsed",
        )
    with ic2:
        send_clicked = st.button("Send", key="chat_send_btn", type="primary", use_container_width=True)
    with ic3:
        clear_clicked = st.button("Clear", key="chat_clear_btn", use_container_width=True)

    import streamlit.components.v1 as components
    components.html("""
    <div style="display:flex;align-items:center;gap:6px;padding:4px 0;">
        <button id="voiceBtn" onclick="startVoice()" style="
            background:linear-gradient(135deg,#0d9488,#0f766e);color:#fff;border:none;
            border-radius:8px;padding:6px 14px;cursor:pointer;font-size:0.8rem;font-weight:500;
            display:flex;align-items:center;gap:6px;transition:all 0.2s;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>
            </svg>
            Voice Input
        </button>
        <span id="voiceStatus" style="font-size:0.75rem;color:#6b7280;"></span>
    </div>
    <script>
    function startVoice() {
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            document.getElementById('voiceStatus').textContent = 'Speech recognition not supported in this browser';
            return;
        }
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        const btn = document.getElementById('voiceBtn');
        const status = document.getElementById('voiceStatus');
        btn.style.background = '#dc2626';
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><rect x="9" y="9" width="6" height="6"/></svg> Listening...';
        status.textContent = 'Speak now...';

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            status.textContent = 'Heard: ' + transcript;
            btn.style.background = 'linear-gradient(135deg,#0d9488,#0f766e)';
            btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg> Voice Input';

            const inputs = window.parent.document.querySelectorAll('input[aria-label="Message"]');
            if (inputs.length > 0) {
                const input = inputs[inputs.length - 1];
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(input, transcript);
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                input.focus();
                setTimeout(() => {
                    input.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true}));
                }, 200);
            }
        };

        recognition.onerror = function(event) {
            status.textContent = 'Error: ' + event.error;
            btn.style.background = 'linear-gradient(135deg,#0d9488,#0f766e)';
            btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg> Voice Input';
        };

        recognition.onend = function() {
            btn.style.background = 'linear-gradient(135deg,#0d9488,#0f766e)';
            btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg> Voice Input';
        };

        recognition.start();
    }
    </script>
    """, height=50)

    if clear_clicked:
        st.session_state.chat_history = []
        st.session_state.chat_actions = {}
        st.session_state.copilot_nav_pending = None
        st.rerun()

    chip_msg = st.session_state.pop("chat_chip_send", None)
    actual_message = chip_msg or (user_input.strip() if send_clicked and user_input and user_input.strip() else None)

    if actual_message:
        st.session_state.chat_history.append({"role": "user", "content": actual_message})

        with st.spinner("Copilot is working..."):
            response = _fetch(
                "/projects/chat",
                method="POST",
                json={
                    "message": actual_message,
                    "project_id": project_id,
                    "history": st.session_state.chat_history[-10:],
                },
                timeout=90,
            )

        if response and response.get("reply"):
            assistant_idx = len(st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "assistant", "content": response["reply"]})

            action_taken = response.get("action_taken")
            if action_taken:
                st.session_state.chat_actions[assistant_idx] = action_taken

                if action_taken.get("action") == "create_project" and action_taken.get("project_id"):
                    st.session_state.copilot_nav_pending = {
                        "tab": "Setup",
                        "index": 0,
                        "new_project_id": action_taken["project_id"],
                    }
                elif action_taken.get("action") == "run_er_simulation" and action_taken.get("result_data") and project_id:
                    st.session_state[f"sim_result_{project_id}"] = action_taken["result_data"]
                    st.session_state.copilot_nav_pending = {
                        "tab": action_taken.get("navigation_hint", "ER Simulator"),
                        "index": action_taken.get("navigation_index", 3),
                    }
                elif action_taken.get("action") == "run_audit" and action_taken.get("result_data") and project_id:
                    st.session_state[f"audit_result_{project_id}"] = action_taken["result_data"]
                    st.session_state.copilot_nav_pending = {
                        "tab": action_taken.get("navigation_hint", "Audit"),
                        "index": action_taken.get("navigation_index", 6),
                    }
                elif action_taken.get("navigation_hint"):
                    st.session_state.copilot_nav_pending = {
                        "tab": action_taken["navigation_hint"],
                        "index": action_taken.get("navigation_index", 0),
                    }
        elif response:
            st.session_state.chat_history.append({"role": "assistant", "content": "I'm sorry, I couldn't generate a response. Please try again."})

        st.rerun()


if page == "Workspace":
    if "selected_project_id" not in st.session_state:
        st.session_state.selected_project_id = None

    if st.session_state.selected_project_id:
        _render_project_workspace(st.session_state.selected_project_id)
    else:
        _render_home()
elif page == "Portfolio":
    render_portfolio_dashboard()
elif page == "Admin":
    render_repository()

_render_chat_widget()
