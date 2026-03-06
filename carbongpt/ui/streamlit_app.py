import os
import time
import requests
import streamlit as st

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

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: var(--radius-full); }
    ::-webkit-scrollbar-thumb:hover { background: var(--text-tertiary); }

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

PAGES = ["Workspace", "Admin"]

SVG_ICONS = {
    "projects": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>',
    "intelligence": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>',
    "admin": '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',
    "docs": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>',
    "globe": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>',
    "methodology": '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>',
}

with st.sidebar:
    st.markdown(f"""
    <div class="brand-header">
        <div class="brand-logo-row">
            <div class="brand-icon">C</div>
            <h2>CarbonGPT</h2>
        </div>
        <div class="brand-tagline">AI Carbon Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-label">Navigation</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", PAGES, key="nav_page", label_visibility="collapsed")

    st.markdown(f"""
    <div class="sidebar-footer">
        <div class="sidebar-footer-text">CarbonGPT Platform</div>
        <div class="sidebar-footer-version">v1.0 -- AI-Powered</div>
    </div>
    """, unsafe_allow_html=True)


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
    st.markdown("""
    <div class="page-header">
        <h1>Administration</h1>
        <div class="page-subtitle">Document repository, compliance rules, knowledge base, and sync tools</div>
    </div>
    """, unsafe_allow_html=True)
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


def _render_home():
    st.markdown("""
    <div class="page-header">
        <h1>Workspace</h1>
        <div class="page-subtitle">Manage your carbon projects and explore market intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    home_tabs = st.tabs(["Projects", "Carbon Intelligence"])
    with home_tabs[0]:
        _render_project_list()
    with home_tabs[1]:
        render_intelligence()


def _render_project_list():

    projects = _fetch("/projects") or []

    col_left, col_right = st.columns([4, 1])
    with col_left:
        if projects:
            st.markdown(f'<span class="stat-pill">{len(projects)} project{"s" if len(projects) != 1 else ""}</span>', unsafe_allow_html=True)
    with col_right:
        if st.button("New Project", key="new_proj_btn", type="primary", use_container_width=True):
            st.session_state["show_new_project"] = True

    if st.session_state.get("show_new_project"):
        _render_new_project_wizard(projects)
        return

    if not projects:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">&#9670;</div>
            <div class="empty-state-title">No projects yet</div>
            <div class="empty-state-desc">Create your first carbon project to start drafting PDDs, Monitoring Reports, and other documents with AI assistance.</div>
        </div>
        """, unsafe_allow_html=True)
        return

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
    card_border_class = "project-card-gs" if std_raw == "GoldStandard" else "project-card-verra" if std_raw == "Verra" else ""
    indent_class = "project-card-indent" if indent else ""
    std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(std_raw, std_raw)

    meta_parts = []
    if std_display:
        meta_parts.append(f'<span class="project-card-meta-item">{SVG_ICONS.get("globe", "")} {std_display}</span>')
    if proj.get("methodology"):
        meta_parts.append(f'<span class="project-card-meta-item">{SVG_ICONS.get("methodology", "")} {proj["methodology"]}</span>')
    if proj.get("country"):
        meta_parts.append(f'<span class="project-card-meta-item">{proj["country"]}</span>')
    meta_html = '<span class="project-card-meta-sep">&bull;</span>'.join(meta_parts)

    child_html = ""
    if child_count > 0:
        child_html = f'<span class="stat-pill" style="margin-left:8px;">{child_count} VPA{"s" if child_count != 1 else ""}</span>'

    status_class = f"status-{status.replace('_', '')}"

    with st.container(border=True):
        col_main, col_stats, col_action = st.columns([4, 1.5, 0.8])
        with col_main:
            st.markdown(f"""
            <div class="project-card-content" style="{'margin-left:20px;' if indent else ''}">
                <div class="project-card-title">
                    <span class="project-type-badge {badge_class}">{type_info['short']}</span>
                    {proj['name']}{child_html}
                </div>
                <div class="project-card-meta">{meta_html}</div>
            </div>
            """, unsafe_allow_html=True)
        with col_stats:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:16px;justify-content:flex-end;padding-top:4px;">
                <div class="project-card-stat">
                    <div class="project-card-stat-value">{doc_count}</div>
                    <div class="project-card-stat-label">Docs</div>
                </div>
                <span class="status-badge {status_class}">{status_label}</span>
            </div>
            """, unsafe_allow_html=True)
        with col_action:
            if st.button("Open", key=f"open_proj_{pid}", type="primary", use_container_width=True):
                st.session_state.selected_project_id = pid
                st.rerun()


def _render_new_project_wizard(existing_projects):
    st.markdown("### Create New Project")

    if st.button("Cancel", key="cancel_new_proj"):
        st.session_state["show_new_project"] = False
        st.session_state.pop("new_proj_step", None)
        st.session_state.pop("new_proj_type", None)
        st.rerun()

    step_key = "new_proj_step"
    if step_key not in st.session_state:
        st.session_state[step_key] = 1

    step = st.session_state[step_key]

    if step == 1:
        st.markdown("**Step 1: What are you working on?**")
        type_cols = st.columns(len(PROJECT_TYPE_INFO))
        for i, (ptype, info) in enumerate(PROJECT_TYPE_INFO.items()):
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

    elif step == 2:
        selected_type = st.session_state.get("new_proj_type", "standalone_pdd")
        type_info = PROJECT_TYPE_INFO[selected_type]
        badge_class = type_info.get("badge_class", "badge-pdd")
        st.markdown(
            f"<span class='project-type-badge {badge_class}'>{type_info['short']}</span> "
            f"**{type_info['label']}**",
            unsafe_allow_html=True,
        )

        available_standards = type_info.get("standards", STANDARD_OPTIONS)
        if len(available_standards) == 1:
            new_standard = available_standards[0]
            std_display = {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(new_standard, new_standard)
            st.info(f"Standard: {std_display}")
        else:
            new_standard = st.selectbox("Standard", available_standards, key="wizard_standard",
                                         format_func=lambda x: {"GoldStandard": "Gold Standard", "Verra": "Verra VCS"}.get(x, x))

        needs_parent = type_info.get("needs_parent", False)
        parent_id = None
        if needs_parent:
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

        new_name = st.text_input("Project name", key="wizard_name",
                                  placeholder="e.g., Ghana Improved Cookstoves")
        new_methodology = _methodology_selector("wizard", standard=new_standard)
        c1, c2 = st.columns(2)
        with c1:
            new_country = st.text_input("Country", key="wizard_country", placeholder="e.g., Ghana")
        with c2:
            new_desc = st.text_area("Description (optional)", key="wizard_desc",
                                     placeholder="Brief description...", height=68)

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

        if parent_id:
            parent_proj = next((p for p in existing_projects if p["id"] == parent_id), None)
            if parent_proj:
                inherited = []
                if parent_proj.get("methodology") and not new_methodology:
                    inherited.append(f"Methodology: {parent_proj['methodology']}")
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
            if st.button("Create Project", key="wizard_create", type="primary"):
                if not new_name:
                    st.warning("Please enter a project name.")
                else:
                    final_methodology = new_methodology
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


def _render_project_workspace(project_id):
    project = _fetch(f"/projects/{project_id}")
    if not project:
        st.error("Project not found.")
        st.session_state.selected_project_id = None
        st.rerun()
        return

    if st.button("Back to Projects", key="back_to_projects"):
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
        meta_items.append(f'<span class="workspace-meta-item">{project["methodology"]}</span>')
    if project.get("country"):
        meta_items.append(f'<span class="workspace-meta-item">{project["country"]}</span>')
    meta_html = '<span class="workspace-meta-dot"></span>'.join(meta_items)

    parent_html = ""
    if project.get("parent_project_id"):
        parent = _fetch(f"/projects/{project['parent_project_id']}")
        if parent:
            parent_type_info = PROJECT_TYPE_INFO.get(parent.get("project_type", ""), {})
            parent_short = parent_type_info.get("short", "Project")
            parent_html = f'<span style="display:block;margin-top:8px;"><span class="stat-pill">Linked to {parent_short}: {parent["name"]}</span></span>'

    desc_html = ""
    if project.get("description"):
        desc_html = f'<span style="display:block;margin-top:8px;font-size:0.85rem;color:var(--text-secondary);">{project["description"]}</span>'

    with st.container(border=True):
        st.markdown(
            f'<span class="project-type-badge {badge_class}">{type_info["short"]}</span> '
            f'<span class="workspace-header-badge {std_badge_class}">{std_display}</span> '
            f'<span class="status-badge {status_class}">{status_label}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f"### {project['name']}")
        st.markdown(
            f'<span class="workspace-header-meta">{meta_html}</span>',
            unsafe_allow_html=True,
        )
        if parent_html:
            st.markdown(parent_html, unsafe_allow_html=True)
        if desc_html:
            st.markdown(desc_html, unsafe_allow_html=True)

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

    tabs = st.tabs(["Project Setup", "Documents", "Write / Draft", "Review", "Respond to Findings", "Export"])

    with tabs[0]:
        _render_project_settings(project)
    with tabs[1]:
        _render_documents_tab(project)
    with tabs[2]:
        _render_write_tab(project)
    with tabs[3]:
        _render_review_tab(project)
    with tabs[4]:
        _render_findings_response_tab(project)
    with tabs[5]:
        _render_export_tab(project)


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

    st.subheader("Respond to Findings")

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

    st.subheader("Export Documents")
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
    st.markdown("### Calculation Spreadsheet")

    if has_calc:
        calc_result = st.session_state[calc_key]
        total_er = calc_result.get("total_emission_reductions_tco2e", 0)
        st.write(f"Calculation available: {total_er:,.0f} tCO2e total emission reductions")
        if st.button("Download Excel Spreadsheet",
                      key=f"export_calc_excel_{project_id}",
                      type="primary"):
            with st.spinner("Generating spreadsheet..."):
                resp = requests.post(
                    f"{API_BASE}/projects/{project_id}/export-calculation",
                    json={"calculation_result": calc_result},
                    timeout=30,
                )
                if resp.status_code == 200:
                    safe_name = project["name"].replace(" ", "_")[:30]
                    st.download_button(
                        label="Save Excel File",
                        data=resp.content,
                        file_name=f"{safe_name}_calculations.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"save_export_excel_{project_id}",
                    )
                else:
                    st.error("Failed to generate spreadsheet.")
    else:
        st.info("No calculations available yet. Emission reduction calculations will be available in a future update.")

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

    st.subheader("Documents & Knowledge Base")
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

    _render_intelligence_review(project_id)


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

    st.subheader("Review")

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
    risk_color = risk_colors.get(risk, "red")
    score = result.get("overall_score", "N/A")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Overall Risk", risk)
    with col2:
        st.metric("Overall Score", f"{score}/100" if isinstance(score, int) else score)

    pdd_consistency = result.get("pdd_consistency", [])
    if pdd_consistency:
        st.warning("**PDD Consistency Issues:**")
        for issue in pdd_consistency:
            st.write(f"- {issue}")

    priority = result.get("priority_actions", [])
    if priority:
        st.subheader("Priority Actions")
        for i, action in enumerate(priority, 1):
            st.write(f"{i}. {action}")

    sections = result.get("sections", [])
    if sections:
        st.subheader("Section-by-Section Review")
        for sec in sections:
            sec_name = sec.get("section", "Unknown")
            sec_score = sec.get("score", "N/A")
            with st.expander(f"{sec_name} (Score: {sec_score}/100)"):
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
            st.write(raw)


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

    st.subheader("AI Writing Assistant")
    st.write("Draft your document section by section or generate the full document at once.")

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
            params.setdefault("baseline_NCV", {"value": "15.6 (wood)", "unit": "TJ/Gg", "source": "IPCC 2006 default for wood (select baseline fuel for specific value)"})
            params.setdefault("baseline_EF_CO2", {"value": "112.0 (wood)", "unit": "tCO2/TJ", "source": "IPCC 2006 default for wood (select baseline fuel for specific value)"})
            params.setdefault("baseline_EF_nonCO2", {"value": "4.03 (wood)", "unit": "tCO2e/TJ", "source": "TPDDTEC default for wood (select baseline fuel for specific value)"})
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
        st.markdown("#### Reference Default Values (CDM TOOL33 / IPCC)")
        st.caption("Official default values for your methodology. These are auto-populated from CDM TOOL33 and IPCC guidelines.")

        if country:
            fnrb_data = get_fnrb_for_country(country)
            if fnrb_data:
                current_fnrb = meth_inputs.get("tool33_fNRB", "")
                mean_pct = int(fnrb_data['value'] * 100)
                sd_pct = int(fnrb_data.get('sd', 0) * 100)
                default_label = f"fNRB = {fnrb_data['value']} ({mean_pct}% +/- {sd_pct}%)"
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
            bf_defaults = get_fuel_defaults(baseline_fuel)
            if bf_defaults:
                for param_key, param_data in bf_defaults.items():
                    safe_key = f"bl_{param_key}".replace(" ", "_")[:30]
                    current_val = meth_inputs.get(f"tool33_{safe_key}", "")
                    label = f"Baseline {param_key} ({baseline_fuel}) [{param_data['unit']}]"
                    val = st.text_input(
                        label,
                        value=current_val,
                        key=f"tool33_bl_{param_key}_{project_id}",
                        placeholder=f"Default: {param_data['value']} ({param_data['source']})",
                    )
                    meth_inputs[f"tool33_{safe_key}"] = val

        if project_fuel and project_fuel != baseline_fuel:
            pf_defaults = get_fuel_defaults(project_fuel)
            if pf_defaults:
                for param_key, param_data in pf_defaults.items():
                    safe_key = f"pj_{param_key}".replace(" ", "_")[:30]
                    current_val = meth_inputs.get(f"tool33_{safe_key}", "")
                    label = f"Project {param_key} ({project_fuel}) [{param_data['unit']}]"
                    val = st.text_input(
                        label,
                        value=current_val,
                        key=f"tool33_pj_{param_key}_{project_id}",
                        placeholder=f"Default: {param_data['value']} ({param_data['source']})",
                    )
                    meth_inputs[f"tool33_{safe_key}"] = val

        if code_upper == "VM0050":
            cf_data = WOOD_TO_CHARCOAL_CF["default"]
            current_cf = meth_inputs.get("tool33_CF", "")
            val = st.text_input(
                f"CF - Wood-to-charcoal conversion factor [{cf_data['unit']}]",
                value=current_cf,
                key=f"tool33_cf_{project_id}",
                placeholder=f"Default: {cf_data['value']} ({cf_data['source']})",
            )
            meth_inputs["tool33_CF"] = val

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
    meth_name = meth_parsed.get("methodology_name", "")

    project_input_params = [p for p in parameters if p.get("category") == "project_input"]
    monitored_params = [p for p in parameters if p.get("category") == "monitored"]
    default_params = [p for p in parameters if p.get("category") == "methodology_default"]
    qualitative_params = [p for p in parameters if p.get("category") == "qualitative"]

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

    if calc_methods:
        with st.container(border=True):
            st.markdown("#### Calculation Method")
            st.caption("Select which quantification approach applies to your project.")
            method_options = []
            for cm in calc_methods:
                mid = cm.get("method_id", "")
                mname = cm.get("method_name", mid)
                method_options.append((mid, mname))
            if method_options:
                current_method = existing_settings.get("calculation_method", "")
                method_ids = [m[0] for m in method_options]
                method_labels = {m[0]: m[1] for m in method_options}
                idx = 0
                if current_method in method_ids:
                    idx = method_ids.index(current_method)
                selected_method = st.selectbox(
                    "Quantification method",
                    method_ids,
                    index=idx,
                    format_func=lambda x: method_labels.get(x, x),
                    key=f"meth_calcmethod_{project_id}",
                )
                new_settings["calculation_method"] = selected_method
                selected_cm = next((cm for cm in calc_methods if cm.get("method_id") == selected_method), None)
                if selected_cm:
                    applicability = selected_cm.get("applicability", "")
                    if applicability:
                        st.caption(f"Applicability: {applicability[:300]}")

    if project_input_params:
        with st.container(border=True):
            st.markdown("#### Project-Specific Parameters")
            st.caption("Values specific to your project activity, required by the methodology.")
            for param in project_input_params:
                p_name = param.get("name", "")
                p_symbol = param.get("symbol", "")
                p_unit = param.get("unit", "")
                p_source = param.get("source", "")
                p_id = param.get("parameter_id", p_symbol or p_name)
                safe_key = (p_id or p_name).replace(" ", "_").replace(",", "").replace(".", "_")[:40]

                label = p_name
                if p_unit:
                    label += f" [{p_unit}]"
                if p_symbol and p_symbol != p_name:
                    label = f"{p_symbol} - {label}"

                current_val = meth_inputs.get(safe_key, "")
                val = st.text_input(
                    label,
                    value=current_val,
                    key=f"meth_pi_{project_id}_{safe_key}",
                    placeholder=f"Source: {p_source[:80]}" if p_source else "",
                )
                meth_inputs[safe_key] = val

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

    if monitored_params:
        with st.container(border=True):
            st.markdown("#### Monitoring Parameters")
            st.caption("These parameters must be monitored during the crediting period. Provide your planned approach or initial values.")
            for param in monitored_params:
                p_name = param.get("name", "")
                p_symbol = param.get("symbol", "")
                p_unit = param.get("unit", "")
                p_source = param.get("source", "")
                p_id = param.get("parameter_id", p_symbol or p_name)
                safe_key = (p_id or p_name).replace(" ", "_").replace(",", "").replace(".", "_")[:40]

                label = p_name
                if p_unit:
                    label += f" [{p_unit}]"
                if p_symbol and p_symbol != p_name:
                    label = f"{p_symbol} - {label}"

                current_val = meth_inputs.get(f"mon_{safe_key}", "")
                val = st.text_input(
                    label,
                    value=current_val,
                    key=f"meth_mon_{project_id}_{safe_key}",
                    placeholder=f"Monitoring source: {p_source[:80]}" if p_source else "Describe your monitoring approach or enter initial/estimated value",
                )
                meth_inputs[f"mon_{safe_key}"] = val

    _render_tool33_defaults(project_id, meth_parsed, new_settings, meth_inputs,
                            country=country)

    tool33_lookup = _build_tool33_lookup(meth_parsed, new_settings, country)

    if default_params:
        with st.container(border=True):
            st.markdown("#### Methodology Default Values")
            st.caption("These values are defined by the methodology. Review and override only if your project has specific justification.")
            for param in default_params:
                p_name = param.get("name", "")
                p_symbol = param.get("symbol", "")
                p_unit = param.get("unit", "")
                p_id = param.get("parameter_id", p_symbol or p_name)
                safe_key = (p_id or p_name).replace(" ", "_").replace(",", "").replace(".", "_")[:40]

                default_val = param.get("default_value") or ""
                if isinstance(default_val, (dict, list)):
                    import json as _json
                    default_val = _json.dumps(default_val)
                default_val = str(default_val)

                defaults_by_ctx = param.get("defaults_by_context", [])
                resolved_default = default_val
                if defaults_by_ctx and context_dims:
                    for dbc in defaults_by_ctx:
                        ctx_key = dbc.get("dimension_key", "")
                        ctx_val = new_settings.get(ctx_key, "")
                        if ctx_val:
                            values_map = dbc.get("values", {})
                            if isinstance(values_map, dict) and ctx_val in values_map:
                                resolved_default = str(values_map[ctx_val])
                                break

                tool33_val = ""
                tool33_src = ""
                if not resolved_default and tool33_lookup:
                    t33 = _match_tool33_param(p_symbol or p_name, tool33_lookup)
                    if t33:
                        tool33_val = str(t33.get("value", ""))
                        tool33_src = t33.get("source", "CDM TOOL33 / IPCC")
                        resolved_default = tool33_val

                label = p_name
                if p_unit:
                    label += f" [{p_unit}]"
                if p_symbol and p_symbol != p_name:
                    label = f"{p_symbol} - {label}"

                current_override = meth_inputs.get(f"def_{safe_key}", "")
                if resolved_default:
                    placeholder = f"Default: {resolved_default[:100]}"
                    if tool33_src:
                        placeholder += f" ({tool33_src})"
                else:
                    placeholder = "No default specified"
                val = st.text_input(
                    label,
                    value=current_override,
                    key=f"meth_def_{project_id}_{safe_key}",
                    placeholder=placeholder,
                )
                meth_inputs[f"def_{safe_key}"] = val

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


def _render_intake_by_type(project_id, project_type, intake, standard="GoldStandard"):
    if project_type in ("standalone_pdd", ""):
        return _render_intake_pdd(project_id, intake, standard)
    elif project_type == "poa_programme":
        return _render_intake_poa(project_id, intake, standard)
    elif project_type == "vpa_component":
        return _render_intake_vpa(project_id, intake, standard)
    elif project_type == "monitoring_report":
        return _render_intake_mr(project_id, intake, standard)
    elif project_type == "valver_report":
        return _render_intake_valver(project_id, intake, standard)
    else:
        return _render_intake_pdd(project_id, intake, standard)


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


def _render_intake_pdd(project_id, intake, standard="GoldStandard"):
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

    proponent_data = _render_proponent_card(project_id, intake, standard, prefix="pdd")

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
            current_scale = po.get("scale", "")
            scale_idx = SCALE_OPTIONS.index(current_scale) if current_scale in SCALE_OPTIONS else 0
            po_scale = st.selectbox("Project scale", SCALE_OPTIONS,
                                     index=scale_idx,
                                     key=f"setup_po_scale_{project_id}",
                                     format_func=lambda x: x if x else "Select scale...")
            _intel_source_label(intake, "project_overview", "scale")
        with pc3:
            po_num_units = st.text_input("Number of units", value=po.get("num_units", ""),
                                          key=f"setup_po_num_units_{project_id}",
                                          placeholder="e.g., 50,000 stoves")
            _intel_source_label(intake, "project_overview", "num_units")
        ac1, ac2 = st.columns(2)
        with ac1:
            current_activity = po.get("activity_type", "")
            activity_idx = ACTIVITY_TYPE_OPTIONS.index(current_activity) if current_activity in ACTIVITY_TYPE_OPTIONS else 0
            po_activity_type = st.selectbox("Activity type", ACTIVITY_TYPE_OPTIONS,
                                             index=activity_idx,
                                             key=f"setup_po_activity_type_{project_id}",
                                             format_func=lambda x: x if x else "Select activity type...")
        with ac2:
            po_sector = st.text_input("Sectoral scope", value=po.get("sectoral_scope", ""),
                                       key=f"setup_po_sector_{project_id}",
                                       placeholder="e.g., Energy industries, Household")

    with st.container(border=True):
        st.markdown("#### Technology & Approach")
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
            tech_baseline_scenario = st.text_input("Baseline practice / fuel", value=tech.get("fuel_baseline", tech.get("baseline_scenario", "")),
                                                key=f"setup_tech_fuel_bl_{project_id}",
                                                placeholder="e.g., Wood, Diesel, Grid electricity")
            _intel_source_label(intake, "technology", "fuel_baseline")
        with tc2:
            tech_model = st.text_input("Model / specification", value=tech.get("model", ""),
                                        key=f"setup_tech_model_{project_id}",
                                        placeholder="e.g., HomeStove 2, V150-4.2MW")
            _intel_source_label(intake, "technology", "model")
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
        lc1, lc2 = st.columns(2)
        with lc1:
            loc_regions = st.text_input("Regions / provinces", value=loc.get("regions", ""),
                                         key=f"setup_loc_regions_{project_id}",
                                         placeholder="e.g., Northern Region, Ashanti Region")
            _intel_source_label(intake, "location", "regions")
            loc_target = st.text_input("Target population", value=loc.get("target_population", ""),
                                        key=f"setup_loc_target_{project_id}",
                                        placeholder="e.g., Rural households")
            _intel_source_label(intake, "location", "target_population")
        with lc2:
            loc_coords = st.text_input("Coordinates (lat, lon)", value=loc.get("coordinates", ""),
                                        key=f"setup_loc_coords_{project_id}",
                                        placeholder="e.g., 7.9465, -1.0232")
            _intel_source_label(intake, "location", "coordinates")
            loc_beneficiaries = st.text_input("Number of beneficiaries", value=loc.get("beneficiaries", ""),
                                               key=f"setup_loc_bene_{project_id}",
                                               placeholder="e.g., 250,000 people")
            _intel_source_label(intake, "location", "beneficiaries")

    with st.container(border=True):
        st.markdown("#### Emission Reductions")
        ec1, ec2 = st.columns(2)
        with ec1:
            er_annual = st.text_input("Annual ER estimate (tCO2e)", value=er.get("annual_er_estimate", ""),
                                       key=f"setup_er_annual_{project_id}",
                                       placeholder="e.g., 150,000")
            _intel_source_label(intake, "emission_reductions", "annual_er_estimate")
        with ec2:
            er_total = st.text_input("Total ER estimate (tCO2e)", value=er.get("total_er_estimate", ""),
                                      key=f"setup_er_total_{project_id}",
                                      placeholder="e.g., 1,050,000")
            _intel_source_label(intake, "emission_reductions", "total_er_estimate")

    sdg_list = _render_sdg_section(project_id, sdgs_data)

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
            "target_population": loc_target, "beneficiaries": loc_beneficiaries,
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
            "annual_er_estimate": er_annual, "total_er_estimate": er_total,
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

    sdg_list = _render_sdg_section(project_id, sdgs_data)

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


def _render_sdg_section(project_id, sdgs_data):
    with st.container(border=True):
        st.markdown("#### SDGs & Co-benefits")
        st.caption("Select the Sustainable Development Goals this project contributes to.")
        existing_sdgs = sdgs_data.get("selected_sdgs", [])
        sdg_list = []
        sdg_goals = [
            "1 - No Poverty", "2 - Zero Hunger", "3 - Good Health and Well-being",
            "4 - Quality Education", "5 - Gender Equality", "6 - Clean Water and Sanitation",
            "7 - Affordable and Clean Energy", "8 - Decent Work and Economic Growth",
            "9 - Industry, Innovation and Infrastructure", "10 - Reduced Inequalities",
            "11 - Sustainable Cities and Communities", "12 - Responsible Consumption and Production",
            "13 - Climate Action", "14 - Life Below Water", "15 - Life on Land",
            "16 - Peace, Justice and Strong Institutions", "17 - Partnerships for the Goals",
        ]
        existing_map = {str(s.get("goal_number", "")): s.get("contribution_description", "") for s in existing_sdgs}
        for goal in sdg_goals:
            goal_num = goal.split(" - ")[0].strip()
            is_selected = st.checkbox(goal, value=goal_num in existing_map,
                                       key=f"setup_sdg_{project_id}_{goal_num}")
            if is_selected:
                contrib = st.text_input(
                    f"SDG {goal_num} contribution",
                    value=existing_map.get(goal_num, ""),
                    key=f"setup_sdg_contrib_{project_id}_{goal_num}",
                    placeholder=f"How does the project contribute to SDG {goal_num}?",
                )
                sdg_list.append({"goal_number": goal_num, "contribution_description": contrib})
    return sdg_list


def _render_project_settings(project):
    project_id = project["id"]
    project_type = project.get("project_type", "standalone_pdd")
    intake = project.get("project_intake") or {}
    if isinstance(intake, str):
        import json as _json
        intake = _json.loads(intake)

    st.subheader("Project Setup")
    st.caption("Fill in the details below. This data will be used by the AI when drafting and reviewing your documents.")

    with st.container(border=True):
        st.markdown("#### About Your Project")
        new_name = st.text_input("Project name", value=project.get("name", ""),
                                  key=f"setup_name_{project_id}")
        c1, c2 = st.columns(2)
        with c1:
            new_standard = st.selectbox("Standard", STANDARD_OPTIONS,
                                         index=STANDARD_OPTIONS.index(project.get("standard", "GoldStandard"))
                                         if project.get("standard") in STANDARD_OPTIONS else 0,
                                         key=f"setup_standard_{project_id}")
        with c2:
            new_country = st.text_input("Country", value=project.get("country", "") or "",
                                         key=f"setup_country_{project_id}")
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

    intake_data = _render_intake_by_type(project_id, project_type, intake, standard=new_standard)

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
        key=f"setup_cp_start_{project_id}",
    )
    cp_years = st.number_input(
        "Crediting period (years)",
        min_value=1, max_value=30,
        value=project.get("crediting_period_years") or 7,
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
    methodology = project.get("methodology")
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

    new_country = st.text_input("Country", value=project.get("country", "") or "",
                                 key=f"settings_country_{project_id}")
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


def _render_chat_widget():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "chat_open" not in st.session_state:
        st.session_state.chat_open = False

    project_id = st.session_state.get("selected_project_id")
    project_name = ""
    if project_id:
        proj = _fetch(f"/projects/{project_id}")
        if proj:
            project_name = proj.get("name", "")

    col_spacer, col_chat_toggle = st.columns([5, 1])
    with col_chat_toggle:
        toggle_label = "Close Assistant" if st.session_state.chat_open else "AI Assistant"
        if st.button(toggle_label, key="chat_toggle_btn", type="primary" if not st.session_state.chat_open else "secondary", use_container_width=True):
            st.session_state.chat_open = not st.session_state.chat_open
            st.rerun()

    if not st.session_state.chat_open:
        return

    context_badge = ""
    if project_name:
        context_badge = f'<span class="chat-context-badge">Project: {project_name}</span>'

    st.markdown("---")

    st.markdown(f"""
    <div class="chat-container">
        <div class="chat-header">
            <div class="chat-header-icon">AI</div>
            CarbonGPT Assistant{context_badge}
        </div>
    </div>
    """, unsafe_allow_html=True)

    chat_container = st.container(height=400)
    with chat_container:
        if not st.session_state.chat_history:
            greeting = "Hello! I'm your CarbonGPT Assistant. I can help with:"
            if project_name:
                greeting += f"\n- Questions about **{project_name}**"
            greeting += (
                "\n- Carbon market concepts and terminology"
                "\n- Methodology guidance (Gold Standard, Verra VCS, CDM)"
                "\n- PDD/MR writing best practices"
                "\n- Emission reduction calculations"
                "\n- Validation and verification processes"
                "\n\nHow can I help you?"
            )
            st.markdown(f"""<div style="padding:8px 0;">
                <div class="chat-msg chat-msg-assistant">{greeting.replace(chr(10), '<br>')}</div>
            </div>""", unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            css_class = "chat-msg-user" if role == "user" else "chat-msg-assistant"
            if role == "assistant":
                import re
                formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
                formatted = formatted.replace("\n", "<br>")
            else:
                formatted = content.replace("\n", "<br>")
            st.markdown(f"""<div style="padding:2px 0;display:flex;{'justify-content:flex-end' if role == 'user' else 'justify-content:flex-start'};">
                <div class="chat-msg {css_class}">{formatted}</div>
            </div>""", unsafe_allow_html=True)

    ic1, ic2, ic3 = st.columns([5, 0.7, 0.7])
    with ic1:
        user_input = st.text_input(
            "Message",
            key="chat_input",
            placeholder="Ask about carbon markets, your project, methodologies...",
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

            // Find Streamlit's input element and set the value
            const inputs = window.parent.document.querySelectorAll('input[aria-label="Message"]');
            if (inputs.length > 0) {
                const input = inputs[inputs.length - 1];
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(input, transcript);
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                // Focus and trigger Streamlit update
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
        st.rerun()

    if send_clicked and user_input and user_input.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})

        with st.spinner("Thinking..."):
            response = _fetch(
                "/projects/chat",
                method="POST",
                json={
                    "message": user_input.strip(),
                    "project_id": project_id,
                    "history": st.session_state.chat_history[-10:],
                },
                timeout=60,
            )

        if response and response.get("reply"):
            st.session_state.chat_history.append({"role": "assistant", "content": response["reply"]})
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
elif page == "Admin":
    render_repository()

_render_chat_widget()
