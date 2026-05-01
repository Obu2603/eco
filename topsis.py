import pandas as pd
import numpy as np

# 9 Sustainability Criteria
CRITERIA = [
    "Embodied Emissions (Tons)",          # Cost (-)
    "Operational Emissions (Tons/yr)",    # Cost (-)
    "Material Reuse (%)",                 # Benefit (+)
    "Renewable Energy (%)",               # Benefit (+)
    "Waste Minimization (%)",             # Benefit (+)
    "Water Efficiency (%)",               # Benefit (+)
    "IEQ Index",                          # Benefit (+)
    "Green Material Source (%)",          # Benefit (+)
    "Lifecycle Cost Impact ($/m2)"        # Cost (-)
]

# Weights for criteria (must sum to 1)
WEIGHTS = [0.15, 0.15, 0.10, 0.15, 0.10, 0.10, 0.05, 0.10, 0.10]

# Impacts: 1 for Benefit (maximize), -1 for Cost (minimize)
IMPACTS = [-1, -1, 1, 1, 1, 1, 1, 1, -1]

def apply_topsis(data_df):
    """
    Applies the TOPSIS algorithm on the given DataFrame.
    Returns the DataFrame with additional columns: 
    'TOPSIS Score', 'Classification', 'Recommendations'
    """
    if data_df.empty:
        return data_df
        
    df = data_df.copy()
    
    # Extract criteria matrix
    matrix = df[CRITERIA].values
    
    if len(matrix) == 0:
        return df

    # 1. Normalize data using manual MinMax Scaling to save bundle size
    try:
        col_min = matrix.min(axis=0)
        col_max = matrix.max(axis=0)
        # Avoid division by zero
        range_val = col_max - col_min
        range_val[range_val == 0] = 1e-10
        norm_matrix = (matrix - col_min) / range_val
    except Exception:
        norm_matrix = matrix
    weight_array = np.array(WEIGHTS)
    weighted_matrix = norm_matrix * weight_array

    # 3. Determine Ideal and Anti-Ideal solutions
    ideal_solution = np.zeros(len(CRITERIA))
    anti_ideal_solution = np.zeros(len(CRITERIA))
    
    for i, impact in enumerate(IMPACTS):
        if impact == 1:
            ideal_solution[i] = np.max(weighted_matrix[:, i]) if len(weighted_matrix) > 0 else 0
            anti_ideal_solution[i] = np.min(weighted_matrix[:, i]) if len(weighted_matrix) > 0 else 0
        else: # -1
            ideal_solution[i] = np.min(weighted_matrix[:, i]) if len(weighted_matrix) > 0 else 0
            anti_ideal_solution[i] = np.max(weighted_matrix[:, i]) if len(weighted_matrix) > 0 else 0

    # 4. Calculate Distance to Ideal and Anti-Ideal
    dist_to_ideal = np.sqrt(np.sum((weighted_matrix - ideal_solution) ** 2, axis=1))
    dist_to_anti_ideal = np.sqrt(np.sum((weighted_matrix - anti_ideal_solution) ** 2, axis=1))

    # 5. Calculate TOPSIS Score
    total_dist = dist_to_ideal + dist_to_anti_ideal
    total_dist[total_dist == 0] = 1e-10
    
    topsis_score = dist_to_anti_ideal / total_dist

    # 6. Apply Classification and AI Recommendations
    df['TOPSIS Score'] = topsis_score
    df['Classification'] = pd.cut(
        df['TOPSIS Score'],
        bins=[-np.inf, 0.45, 0.75, np.inf],
        labels=['Low', 'Medium', 'High']
    )
    
    # Generate recommendations per row
    recommendations = []
    for index, row in df.iterrows():
        rec = generate_recommendations(row['Classification'], row)
        recommendations.append(rec)
        
    df['Recommendations'] = recommendations
    return df

def detect_risks(project_data):
    """
    Detects environmental risks based on project metrics.
    Returns a list of risks with severity.
    """
    risks = []
    
    # 1. Embodied Carbon Risk
    emb = project_data.get('Embodied Emissions (Tons)', 0)
    if emb > 2500:
        risks.append({"level": "High", "msg": "Critical: Massive Embodied Carbon footprint detected."})
    elif emb > 1500:
        risks.append({"level": "Moderate", "msg": "Warning: High embodied emissions for project scale."})
        
    # 2. Renewable Energy Risk
    ren = project_data.get('Renewable Energy (%)', 0)
    if ren < 10:
        risks.append({"level": "High", "msg": "Critical: Near-zero renewable energy usage."})
    elif ren < 30:
        risks.append({"level": "Moderate", "msg": "Warning: Low renewable energy adoption."})
        
    # 3. Waste Risk
    wst = project_data.get('Waste Minimization (%)', 0)
    if wst < 30:
        risks.append({"level": "High", "msg": "Critical: Poor waste management strategy."})
    elif wst < 50:
        risks.append({"level": "Moderate", "msg": "Warning: Sub-optimal waste minimization."})
        
    # 4. Water Risk
    wat = project_data.get('Water Efficiency (%)', 0)
    if wat < 40:
        risks.append({"level": "Moderate", "msg": "Warning: Water efficiency is below industry standards."})

    return risks

def get_optimized_suggestions(project_data, current_score):
    """
    Simulates impact of improving each benefit criterion by 10%
    to find the most effective improvement.
    """
    benefits = [
        "Material Reuse (%)", "Renewable Energy (%)", 
        "Waste Minimization (%)", "Water Efficiency (%)", 
        "Green Material Source (%)"
    ]
    
    impacts = []
    
    for criterion in benefits:
        temp_data = project_data.copy()
        temp_data[criterion] = min(100, temp_data[criterion] + 15)
        
        idx = CRITERIA.index(criterion)
        weight = WEIGHTS[idx]
        delta = (15 / 100) * weight
        
        impacts.append({
            "criterion": criterion,
            "potential_gain": delta,
            "action": f"Increase {criterion.split(' (')[0]} to {temp_data[criterion]}%"
        })
        
    # Sort by impact
    sorted_impacts = sorted(impacts, key=lambda x: x['potential_gain'], reverse=True)
    return sorted_impacts[:3]

def generate_recommendations(classification, project_data):
    """
    Generates rule-based AI recommendations based on the classification and project metrics.
    """
    recs = []
    if classification == 'Low':
        recs.append("CRITICAL: The sustainability score is in the lower third.")
        if project_data['Renewable Energy (%)'] < 30:
            recs.append("Action: Increase renewable energy sources (currently very low). Consider solar panels or procuring green energy.")
        if project_data['Waste Minimization (%)'] < 50:
            recs.append("Action: Implement strict waste reduction protocols on-site.")
        if project_data['Embodied Emissions (Tons)'] > 1500:
             recs.append("Action: Conduct a thorough carbon audit to reduce overall emissions.")
             
    elif classification == 'Medium':
        recs.append("MODERATE: The project has average sustainability performance.")
        if project_data['Material Reuse (%)'] < 50:
            recs.append("Action: Optimize material reuse; target using at least 50% recycled or salvaged materials.")
        if project_data['Water Efficiency (%)'] < 60:
            recs.append("Action: Integrate rainwater harvesting and high-efficiency fixtures.")
            
    else: # High
        recs.append("EXCELLENT: The project demonstrates high sustainability.")
        recs.append("Action: Maintain current performance levels.")
        recs.append("Action: Look into advanced carbon reduction technologies (e.g. carbon-curing concrete) to push toward net-zero.")
        
    return " | ".join(recs)
