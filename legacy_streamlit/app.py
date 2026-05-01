import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from topsis import apply_topsis, detect_risks, get_optimized_suggestions
from database import get_similar_projects, count_projects, get_top_projects, save_evaluated_project, get_sustainability_stats, get_metadata
from fpdf import FPDF
import base64
from datetime import datetime

# App Configuration
st.set_page_config(page_title="Eco Build AI", page_icon="🌿", layout="wide")

# injecting CSS
def inject_custom_css():
    try:
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass 

inject_custom_css()

# --- Sidebar Inputs ---
with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            <h1 style="margin:0; font-size: 24px;">🌿 Eco Build AI</h1>
            <p style="margin:0; font-size: 12px; color: #34d399;">Enterprise Sustainability Analytics</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.header("Project Details")
    location = st.text_input("Project Location", value="Hyderabad", placeholder="Enter city name...").strip().title()
    proj_type = st.selectbox("Project Type", ["Residential", "Commercial", "Industrial", "Institutional", "Mixed-Use"])
    area = st.number_input("Building Area (m²)", min_value=100, max_value=500000, value=5000)
    
    st.header("Assessments & Metrics")
    cert_level = st.selectbox("Green Certification", ["None", "Bronze", "Silver", "Gold", "Platinum"])
    policy = st.selectbox("Policy Intervention", ["None", "Renewable Mandate", "Emission Cap", "Tax Incentive"])
    lifecycle = st.selectbox("Lifecycle Phase", ["Design", "Construction", "Operation", "Renovation", "Demolition"])
    
    st.markdown("### Emissions (Tons)")
    embodied = st.number_input("Embodied Emissions", min_value=0, value=1500)
    operational = st.number_input("Operational Emissions (yr)", min_value=0, value=300)
    
    st.markdown("### Circularity & Efficiency (%)")
    reuse = st.slider("Material Reuse %", 0, 100, 25)
    renewable = st.slider("Renewable Energy %", 0, 100, 40)
    waste_min = st.slider("Waste Minimization %", 0, 100, 60)
    
    st.markdown("### Additional Criteria")
    water_eff = st.slider("Water Efficiency %", 0, 100, 50)
    ieq = st.slider("IEQ Index (1-10)", 1, 10, 7)
    green_mat = st.slider("Green Material Source %", 0, 100, 30)
    cost_impact = st.number_input("Lifecycle Cost Impact ($/m²)", min_value=0, value=150)
    
    submit = st.button("Evaluate Sustainability")

# --- Tabs for Dashboard and Leaderboard ---
tab1, tab2 = st.tabs(["📊 Dashboard", "🏆 Leaderboard"])

with tab1:
    if not submit:
        st.title("🌿 Eco Build AI - Intelligent Sustainability Assessment")
        st.markdown("### 🌍 Building a Greener Future, Scientifically.")
        st.info("Please fill in the project details in the sidebar to generate a comprehensive AI sustainability assessment.")
        
        st.markdown("---")
        st.markdown("### 📊 Platform Statistics")
        
        try:
            total_projects = count_projects()
            c1, c2, c3 = st.columns(3)
            c1.metric("Projects Analyzed", f"{total_projects:,}")
            c2.metric("Sustainability Criteria", "9", "MCDM-TOPSIS")
            c3.metric("Platform Accuracy", "High", "Enterprise Grade")
            
            df_demo = pd.DataFrame({
                "Criteria": ["Embodied Em.", "Op. Em.", "Reuse", "Renewable", "Waste", "Water Eq", "IEQ", "Green Mat", "Cost Impact"],
                "Average %": [40, 60, 50, 45, 75, 55, 80, 40, 65]
            })
            fig_demo = px.bar(df_demo, x="Criteria", y="Average %", title="Global Construction Averages (Benchmark)", color="Average %", color_continuous_scale="Greens")
            st.plotly_chart(fig_demo, width="stretch")
            
        except Exception:
            st.warning("Connect to the database to view live platform statistics.")
            
    else:
        # Initial Assessment Data
        input_data = {
            "Project Location": location, "Project Type": proj_type, "Building Area (m2)": area,
            "Green Certification Level": cert_level, "Policy Intervention": policy, "Lifecycle Phase": lifecycle,
            "Embodied Emissions (Tons)": embodied, "Operational Emissions (Tons/yr)": operational,
            "Material Reuse (%)": reuse, "Renewable Energy (%)": renewable, "Waste Minimization (%)": waste_min,
            "Water Efficiency (%)": water_eff, "IEQ Index": ieq, "Green Material Source (%)": green_mat,
            "Lifecycle Cost Impact ($/m2)": cost_impact
        }
        
        # Pull similar projects for relative TOPSIS
        similar_projs = get_similar_projects(proj_type, location, limit=20)
        df_input = pd.DataFrame([input_data])
        
        if len(similar_projs) > 5:
            df_hist = pd.DataFrame(similar_projs)
            if '_id' in df_hist.columns: df_hist = df_hist.drop(columns=['_id'])
            df_combined = pd.concat([df_input, df_hist], ignore_index=True)
            result_df = apply_topsis(df_combined)
            final_result = result_df.iloc[0]
        else:
            # Fallback heuristic
            score = (reuse*0.15 + renewable*0.2 + waste_min*0.15 + water_eff*0.1 + ieq*5 + green_mat*0.1) / 100
            score = min(score, 1.0)
            classification = "High" if score >= 0.75 else "Medium" if score >= 0.45 else "Low"
            final_result = pd.Series({"TOPSIS Score": score, "Classification": classification, "Recommendations": "Add more data for higher accuracy."})

        score = final_result.get('TOPSIS Score', 0.5)
        classification = final_result.get('Classification', 'Medium')
        recs = final_result.get('Recommendations', '')

        # Save result to database
        db_record = {
            "Project Location": location,
            "Project Type": proj_type,
            "Embodied Emissions (Tons)": embodied,
            "Operational Emissions (Tons/yr)": operational,
            "Material Reuse (%)": reuse,
            "Renewable Energy (%)": renewable,
            "Waste Minimization (%)": waste_min,
            "TOPSIS Score": score,
            "Classification": str(classification)
        }
        try:
            save_evaluated_project(db_record)
        except Exception as e:
            st.error(f"Error saving to database: {e}")

        # --- Dashboard Header ---
        st.title(f"{proj_type} Project Assessment ({location})")
        
        # Animated Score Indicator
        score_pct = int(score * 100)
        st.markdown(f"""
            <div class="score-container">
                <div class="score-circle" style="--percentage: {score_pct}%;" data-score="{score_pct}%"></div>
            </div>
            <div style="text-align: center; margin-top: -30px; margin-bottom: 20px;">
                <h3 style="color: {'#10b981' if classification == 'High' else '#f59e0b' if classification == 'Medium' else '#ef4444'}">{classification.upper()} SUSTAINABILITY</h3>
            </div>
        """, unsafe_allow_html=True)

        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        kpi_col1.metric("Sustainability Index", f"{score:.3f}")
        kpi_col2.metric("Carbon Intensive", "No" if embodied < 1500 else "Yes", delta="Optimal" if embodied < 1000 else "Critical", delta_color="inverse")
        kpi_col3.metric("Green Material", f"{green_mat}%")
        kpi_col4.metric("IEQ Score", f"{ieq}/10")

        # --- Risk Detection ---
        st.markdown("### ⚠️ Sustainability Risk Detection")
        risks = detect_risks(input_data)
        if not risks:
            st.markdown('<div class="success-alert">✅ No critical environmental risks detected.</div>', unsafe_allow_html=True)
        else:
            for risk in risks:
                alert_class = "danger-alert" if risk['level'] == "High" else "warning-alert"
                st.markdown(f'<div class="{alert_class}"><b>{risk["level"]} Risk:</b> {risk["msg"]}</div>', unsafe_allow_html=True)

        # --- Optimizer & Simulator ---
        col_opt, col_sim = st.columns([1, 1])
        
        with col_opt:
            st.markdown("### 💡 AI Sustainability Optimizer")
            opts = get_optimized_suggestions(input_data, score)
            for opt in opts:
                st.markdown(f"""
                <div style="background: white; padding: 10px; border-radius: 8px; border-left: 4px solid #10b981; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <small style="color: #64748b;">Improvement found in {opt['criterion'].split(' (')[0]}</small><br>
                    <b>{opt['action']}</b><br>
                    <span style="color: #10b981; font-size: 0.8rem;">+{(opt['potential_gain']*100):.1f}% potential score increase</span>
                </div>
                """, unsafe_allow_html=True)

        with col_sim:
            st.markdown("### 🎛️ Carbon Reduction Simulation")
            s_ren = st.slider("Simulate Renewable %", 0, 100, int(renewable))
            s_re = st.slider("Simulate Material Reuse %", 0, 100, int(reuse))
            s_wst = st.slider("Simulate Waste Min %", 0, 100, int(waste_min))
            
            # Simple simulation logic
            sim_score = (s_re*0.15 + s_ren*0.2 + s_wst*0.15 + water_eff*0.1 + ieq*5 + green_mat*0.1) / 100
            sim_score = min(sim_score, 1.0)
            
            delta = sim_score - score
            st.metric("Simulated Score", f"{sim_score:.3f}", f"{delta:+.3f}", delta_color="normal")

        # --- Visualizations ---
        st.markdown("---")
        st.markdown("### 📈 Advanced Visualization")
        v_col1, v_col2 = st.columns(2)
        
        with v_col1:
            # Radar Chart
            categories = ['Embodied Em.', 'Op. Em.', 'Reuse %', 'Renewable %', 'Waste Min. %', 'Water Eff. %', 'IEQ', 'Green Mat. %', 'Cost Impact']
            values_radar = [100 - min(100, embodied/20), 100 - min(100, operational/10), reuse, renewable, waste_min, water_eff, ieq*10, green_mat, 100 - min(100, cost_impact/5)]
            
            fig_radar = go.Figure(data=go.Scatterpolar(r=values_radar, theta=categories, fill='toself', marker_color='#10b981'))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), title="Criteria Performance Radar", showlegend=False)
            st.plotly_chart(fig_radar, width="stretch")

        with v_col2:
            # Improvement Graph
            sim_df = pd.DataFrame({"Stage": ["Current", "Target (Optimized)"], "Score": [score, sim_score]})
            fig_imp = px.bar(sim_df, x="Stage", y="Score", text_auto='.3f', color="Stage", color_discrete_sequence=['#94a3b8', '#10b981'])
            fig_imp.update_yaxes(range=[0, 1])
            fig_imp.update_layout(title="Sustainability Improvement Comparison", showlegend=False)
            st.plotly_chart(fig_imp, width="stretch")

        # --- Report Generation ---
        st.markdown("---")
        def generate_report():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 24); pdf.set_text_color(16, 131, 89)
            pdf.cell(0, 20, "Eco Build AI Sustainability Report", ln=True, align='C')
            pdf.set_font("Arial", '', 12); pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Arial", 'B', 14); pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, f"Project: {proj_type} at {location}", ln=True)
            pdf.cell(0, 10, f"Sustainability Score: {score:.4f} ({classification.upper()})", ln=True)
            pdf.ln(5)
            
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Risk Assessment:", ln=True)
            pdf.set_font("Arial", '', 11)
            if not risks: pdf.cell(0,8, "- No critical risks detected.", ln=True)
            for r in risks: pdf.multi_cell(0, 8, f"- [{r['level']}] {r['msg']}")
            
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "AI Recommendations:", ln=True)
            pdf.set_font("Arial", '', 11)
            for r in recs.split(' | '): pdf.multi_cell(0, 8, f"- {r}")
            
            return pdf.output(dest='S').encode('latin-1')

        if st.button("Generate Technical Report"):
            report_bytes = generate_report()
            st.download_button("📥 Download PDF Report", report_bytes, f"Report_{location}.pdf", "application/pdf")

with tab2:
    st.title("🏆 Sustainability Analytics Dashboard")
    
    # 1. Summary Statistics (KPI Cards)
    try:
        stats = get_sustainability_stats()
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.markdown(f"""
                <div class="kpi-card animate-fade-in" style="border-top-color: #3b82f6;">
                    <div class="kpi-value">{stats['total']:,}</div>
                    <div class="kpi-label">Total Projects</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class="kpi-card animate-fade-in" style="border-top-color: #10b981;">
                    <div class="kpi-value" style="background: linear-gradient(45deg, #10b981, #059669); -webkit-background-clip: text;">{stats['high']:,}</div>
                    <div class="kpi-label">High Sustainability</div>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
                <div class="kpi-card animate-fade-in" style="border-top-color: #f59e0b;">
                    <div class="kpi-value" style="background: linear-gradient(45deg, #f59e0b, #d97706); -webkit-background-clip: text;">{stats['medium']:,}</div>
                    <div class="kpi-label">Medium Sustainability</div>
                </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
                <div class="kpi-card animate-fade-in" style="border-top-color: #ef4444;">
                    <div class="kpi-value" style="background: linear-gradient(45deg, #ef4444, #dc2626); -webkit-background-clip: text;">{stats['low']:,}</div>
                    <div class="kpi-label">Low Sustainability</div>
                </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.warning("Stats unavailable. Initialize database to see analytics.")

    st.markdown("---")

    # 2. Search & Filters
    st.markdown("### 🔍 Analytics Explorer")
    f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
    
    with f_col1:
        search_q = st.text_input("Search Project Location or Type...", placeholder="e.g. Chennai, Industrial")
    with f_col2:
        proj_types_meta = ["All"] + get_metadata()["types"]
        f_type = st.selectbox("Filter by Type", proj_types_meta)
    with f_col3:
        f_class = st.selectbox("Filter by Classification", ["All", "High", "Medium", "Low"])

    # 3. Interactive Data Table (Leaderboard)
    try:
        top_projects = get_top_projects(limit=50, search_query=search_q, project_type=f_type, classification=f_class)
        
        if top_projects:
            df_leader = pd.DataFrame(top_projects)
            
            # Ranking and Medal logic
            df_leader.insert(0, "Rank", range(1, len(df_leader) + 1))
            
            def get_rank_display(row):
                rank = row['Rank']
                if rank == 1: return "🥇 Gold"
                if rank == 2: return "🥈 Silver"
                if rank == 3: return "🥉 Bronze"
                return f"#{rank}"
            
            df_leader["Rank"] = df_leader.apply(get_rank_display, axis=1)

            # Custom Score Bar logic
            def render_score_bar(score, classification):
                color_class = "bg-high" if classification == "High" else "bg-medium" if classification == "Medium" else "bg-low"
                pct = score * 100
                return f"""
                <div style="display: flex; align-items: center;">
                    <span style="min-width: 45px; font-weight: bold; margin-right: 10px;">{score:.3f}</span>
                    <div class="score-progress-container">
                        <div class="score-progress-fill {color_class}" style="width: {pct}%;"></div>
                    </div>
                </div>
                """

            # Prepare display dataframe
            display_df = df_leader[["Rank", "Project Type", "Project Location", "TOPSIS Score", "Classification"]].copy()
            display_df = display_df.rename(columns={"TOPSIS Score": "Sustainability Score"})

            # Styling for color-coded progress bars and specific classification text colors
            def style_leaderboard(styler):
                # Color code the Sustainability Score using bars
                # We apply different colors based on the classification row
                high_mask = display_df['Classification'] == 'High'
                med_mask = display_df['Classification'] == 'Medium'
                low_mask = display_df['Classification'] == 'Low'
                
                # Apply bars with color coding
                styler = styler.bar(subset=pd.IndexSlice[display_df[high_mask].index, 'Sustainability Score'], color='#10b981', vmin=0, vmax=1)
                styler = styler.bar(subset=pd.IndexSlice[display_df[med_mask].index, 'Sustainability Score'], color='#f59e0b', vmin=0, vmax=1)
                styler = styler.bar(subset=pd.IndexSlice[display_df[low_mask].index, 'Sustainability Score'], color='#ef4444', vmin=0, vmax=1)
                
                # Highlight classification text
                def color_text(val):
                    color = '#10b981' if val == 'High' else '#f59e0b' if val == 'Medium' else '#ef4444'
                    return f'color: {color}; font-weight: bold;'
                
                styler = styler.map(color_text, subset=['Classification'])
                return styler

            st.dataframe(
                style_leaderboard(display_df.style),
                width="stretch",
                hide_index=True,
                column_config={
                    "Rank": st.column_config.TextColumn("Rank", width="small"),
                    "Sustainability Score": st.column_config.NumberColumn("Score Index", format="%.3f"),
                    "Classification": st.column_config.SelectboxColumn("Classification", options=["High", "Medium", "Low"])
                }
            )

            # 4. Map Visualization
            st.markdown("---")
            st.markdown("### 🗺️ Sustainability Geographic Distribution")
            
            # Check if columns exist AND have non-null values
            has_coords = "Latitude" in df_leader.columns and "Longitude" in df_leader.columns and not df_leader[["Latitude", "Longitude"]].dropna().empty
            
            if has_coords:
                map_data = df_leader[["Latitude", "Longitude", "Project Location", "Project Type", "TOPSIS Score", "Classification"]].dropna()
                
                fig_map = px.scatter_mapbox(
                    map_data, 
                    lat="Latitude", 
                    lon="Longitude", 
                    color="Classification",
                    size="TOPSIS Score",
                    hover_name="Project Location",
                    hover_data=["Project Type", "TOPSIS Score"],
                    color_discrete_map={"High": "#10b981", "Medium": "#f59e0b", "Low": "#ef4444"},
                    zoom=3, 
                    height=500,
                    mapbox_style="carto-darkmatter"
                )
                fig_map.update_layout(
                    margin={"r":0,"t":0,"l":0,"b":0},
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_map, width="stretch")
            else:
                # Fallback Visualization: Top Sustainable Cities Horizontal Bar Chart
                # Group by location and get average score
                city_stats = df_leader.groupby("Project Location")["TOPSIS Score"].mean().reset_index()
                city_stats = city_stats.sort_values("TOPSIS Score", ascending=False).head(10)
                city_stats = city_stats.rename(columns={"TOPSIS Score": "Sustainability Score"})
                
                # Assign levels for discrete color mapping
                city_stats["Level"] = city_stats["Sustainability Score"].apply(
                    lambda x: "High" if x >= 0.75 else "Medium" if x >= 0.45 else "Low"
                )
                
                # Create horizontal bar chart
                fig_fallback = px.bar(
                    city_stats,
                    x="Sustainability Score",
                    y="Project Location",
                    orientation='h',
                    title="Top Sustainable Cities by Sustainability Score",
                    text="Sustainability Score",
                    color="Level",
                    color_discrete_map={"High": "#10b981", "Medium": "#f59e0b", "Low": "#ef4444"},
                    category_orders={"Project Location": city_stats["Project Location"].tolist()}
                )
                
                # Styling and Animations
                fig_fallback.update_traces(
                    texttemplate='%{text:.3f}', 
                    textposition='outside',
                    marker_line_color='rgba(255,255,255,0.2)',
                    marker_line_width=1,
                    opacity=0.9
                )
                
                fig_fallback.update_layout(
                    height=500,
                    xaxis_title="Average Sustainability Score",
                    yaxis_title="",
                    xaxis_range=[0, 1.1], # Extra space for text
                    showlegend=True,
                    legend_title="Sustainability Level",
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#e2e8f0"),
                    title_font=dict(size=22, color="#34d399", family="Inter, sans-serif"),
                    margin=dict(l=20, r=20, t=60, b=40),
                    bargap=0.3
                )
                
                # Add subtle grid for readability
                fig_fallback.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                fig_fallback.update_yaxes(showgrid=False)
                
                st.plotly_chart(fig_fallback, width="stretch")

        else:
            st.info("No projects found matching your criteria.")
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

