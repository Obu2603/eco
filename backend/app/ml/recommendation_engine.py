def generate_recommendations(classification: str, metrics: dict, carbon_emissions: float) -> str:
    """
    Generates advanced, prioritized recommendations based on the sustainability classification
    and specific metrics (like Renewable Energy, Waste Minimization, Material Reuse, etc.)
    and absolute carbon emissions.
    """
    recommendations = []
    
    # 1. Carbon Offset Recommendation (Based on total emissions)
    # Average tree offsets ~20kg CO2 per year = 0.02 tons
    trees_needed = int(carbon_emissions / 0.02)
    if carbon_emissions > 5000:
        recommendations.append(f"[HIGH PRIORITY] Massive Carbon Footprint: Recommend planting ~{trees_needed:,} trees over the project lifecycle to offset {carbon_emissions:,.0f} tons of CO2.")
    elif carbon_emissions > 1000:
        recommendations.append(f"[MEDIUM PRIORITY] Carbon Offset: Plant ~{trees_needed:,} trees to neutralize {carbon_emissions:,.0f} tons of CO2.")
    
    # 2. Renewable Energy
    renewable = metrics.get('Renewable Energy (%)', 0)
    if renewable < 30:
        recommendations.append("[HIGH PRIORITY] Energy: Switch to solar/wind. Current renewable energy usage is below 30%. Aim for at least 50% to significantly improve sustainability.")
    elif renewable < 60:
        recommendations.append("[MEDIUM PRIORITY] Energy: Consider expanding solar panel footprint or purchasing green energy credits to push renewable usage above 60%.")
        
    # 3. Material Reuse & Eco-friendly materials
    reuse = metrics.get('Material Reuse (%)', 0)
    if reuse < 25:
        recommendations.append("[HIGH PRIORITY] Materials: Use recycled steel and low-carbon concrete. Your material reuse is dangerously low.")
    elif reuse < 50:
        recommendations.append("[MEDIUM PRIORITY] Materials: Good start. Increase use of locally sourced, recycled eco-friendly materials to reach 50% reuse.")
        
    # 4. Green Cover
    green_cover = metrics.get('Green Cover (%)', 0)
    if green_cover < 20:
        recommendations.append("[HIGH PRIORITY] Zoning: Increase green cover! Add rooftop gardens or vertical forests to improve local AQI and insulation.")
        
    # 5. Waste Minimization
    waste = metrics.get('Waste Minimization (%)', 0)
    if waste < 40:
        recommendations.append("[HIGH PRIORITY] Construction Waste: Implement strict lean construction principles. Current waste minimization is inefficient.")

    # 6. Traffic & Zoning
    traffic = metrics.get('Traffic Level', 0)
    if traffic > 70:
        recommendations.append("[HIGH PRIORITY] Traffic/Zoning: High traffic impact detected. Suggest implementing staggered construction hours and optimized logistics routes.")

    if not recommendations:
        recommendations.append("[LOW PRIORITY] Excellent baseline. Continue monitoring environmental impact and maintain current practices.")
        
    return " | ".join(recommendations)
