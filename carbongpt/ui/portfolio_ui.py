import streamlit as st
from carbongpt.core.lifecycle_manager import get_portfolio_summary


def render_portfolio_dashboard():
    st.header("Portfolio Dashboard")

    try:
        portfolio = get_portfolio_summary()
    except Exception as e:
        st.error(f"Could not load portfolio data: {e}")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Projects", portfolio.get("total_projects", 0))
    with col2:
        st.metric("Countries", portfolio.get("countries", 0))
    with col3:
        st.metric("Methodologies", portfolio.get("methodologies", 0))
    with col4:
        total_er = portfolio.get("total_projected_er", 0)
        st.metric("Projected ER", f"{total_er:,.0f} tCO2e")

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Projects by Status**")
        by_status = portfolio.get("by_status", [])
        if by_status:
            status_data = {row["status"]: row["count"] for row in by_status}
            st.bar_chart(data=status_data)
        else:
            st.info("No project status data available")

    with chart_col2:
        st.markdown("**Projects by Methodology**")
        by_meth = portfolio.get("by_methodology", [])
        if by_meth:
            meth_data = {row["methodology"]: row["count"] for row in by_meth}
            st.bar_chart(data=meth_data)
        else:
            st.info("No methodology data available")

    st.markdown("---")

    st.markdown("**Projects by Country**")
    by_country = portfolio.get("by_country", [])
    if by_country:
        for row in by_country:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(row["country"])
            with col2:
                st.write(row["count"])

    st.markdown("---")

    st.markdown("**All Projects**")
    projects = portfolio.get("projects", [])
    if projects:
        table_data = []
        for p in projects:
            table_data.append({
                "Name": p.get("name", ""),
                "Standard": p.get("standard", ""),
                "Methodology": p.get("methodology", ""),
                "Country": p.get("country", ""),
                "Status": p.get("status", ""),
                "Projected ER": f"{p.get('projected_er', 0):,.0f}",
            })
        st.table(table_data)
    else:
        st.info("No projects found")
