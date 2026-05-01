import numpy as np

CRITERIA = [
    "Embodied Emissions (Tons)",
    "Operational Emissions (Tons/yr)",
    "Material Reuse (%)",
    "Renewable Energy (%)",
    "Waste Minimization (%)",
    "Water Efficiency (%)",
    "IEQ Index",
    "Green Material Source (%)",
    "Lifecycle Cost Impact ($/m2)"
]

WEIGHTS = np.array([0.15, 0.15, 0.10, 0.15, 0.10, 0.10, 0.05, 0.10, 0.10])
IMPACTS = np.array([-1, -1, 1, 1, 1, 1, 1, 1, -1])

# For a single location, TOPSIS requires a comparison matrix.
# We will use industry benchmarks as the comparison matrix to evaluate a single project.
INDUSTRY_BENCHMARKS = np.array([
    [2000, 500, 20, 10, 30, 40, 60, 20, 1500], # Bad
    [1000, 250, 50, 40, 60, 70, 80, 50, 1000], # Average
    [500,  100, 80, 80, 90, 95, 95, 80, 800]   # Excellent
])

def calculate_topsis_score(project_metrics: list) -> dict:
    """
    Calculates TOPSIS score for a single project by comparing it to industry benchmarks.
    project_metrics must be a list of 9 values corresponding to CRITERIA.
    """
    matrix = np.vstack([INDUSTRY_BENCHMARKS, project_metrics])
    
    # MinMax Normalize
    col_min = matrix.min(axis=0)
    col_max = matrix.max(axis=0)
    
    # Avoid div by zero
    diff = col_max - col_min
    diff[diff == 0] = 1 
    norm_matrix = (matrix - col_min) / diff
    
    # Weighted
    weighted_matrix = norm_matrix * WEIGHTS
    
    # Ideal & Anti-Ideal
    ideal_solution = np.zeros(len(CRITERIA))
    anti_ideal_solution = np.zeros(len(CRITERIA))
    
    for i, impact in enumerate(IMPACTS):
        if impact == 1:
            ideal_solution[i] = np.max(weighted_matrix[:, i])
            anti_ideal_solution[i] = np.min(weighted_matrix[:, i])
        else:
            ideal_solution[i] = np.min(weighted_matrix[:, i])
            anti_ideal_solution[i] = np.max(weighted_matrix[:, i])
            
    # Distance
    dist_to_ideal = np.sqrt(np.sum((weighted_matrix - ideal_solution) ** 2, axis=1))
    dist_to_anti_ideal = np.sqrt(np.sum((weighted_matrix - anti_ideal_solution) ** 2, axis=1))
    
    total_dist = dist_to_ideal + dist_to_anti_ideal
    total_dist[total_dist == 0] = 1e-10
    
    topsis_scores = dist_to_anti_ideal / total_dist
    project_score = topsis_scores[-1] # The last row is our project
    
    if project_score < 0.45:
        classification = "Low"
    elif project_score < 0.75:
        classification = "Medium"
    else:
        classification = "High"
        
    return {
        "score": float(project_score),
        "classification": classification
    }
