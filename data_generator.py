import random
import pandas as pd
import numpy as np
from database import get_collection

# Configuration
NUM_PROJECTS = 100000
BATCH_SIZE = 10000

LOCATIONS = [
    # Tamil Nadu
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem", "Tirunelveli", 
    "Tiruppur", "Vellore", "Erode", "Thoothukudi", "Dindigul", "Thanjavur",
    "Kanchipuram", "Kanyakumari", "Ooty", "Pudukkottai", "Hosur", "Sivakasi",
    
    # Karnataka
    "Bengaluru", "Mysuru", "Hubballi", "Mangaluru", "Belagavi", "Kalaburagi",
    "Ballari", "Vijayapura", "Shivamogga", "Tumakuru", "Udupi", "Chikkamagaluru",
    
    # Kerala
    "Kochi", "Thiruvananthapuram", "Kozhikode", "Thrissur", "Kollam", "Alappuzha",
    "Palakkad", "Kottayam", "Malappuram", "Kannur",
    
    # Andhra Pradesh & Telangana
    "Hyderabad", "Visakhapatnam", "Vijayawada", "Guntur", "Warangal", "Nellore",
    "Kurnool", "Nizamabad", "Tirupati", "Rajamahendravaram", "Kakinada",
    
    # Maharashtra
    "Mumbai", "Pune", "Nagpur", "Thane", "Pimpri-Chinchwad", "Nashik", "Kalyan-Dombivli",
    "Vasai-Virar", "Aurangabad", "Navi Mumbai", "Solapur", "Mira-Bhayandar", "Kolhapur",
    
    # North India
    "Delhi", "Gurugram", "Noida", "Faridabad", "Chandigarh", "Ludhiana", "Amritsar",
    "Jalandhar", "Lucknow", "Kanpur", "Ghaziabad", "Agra", "Meerut", "Varanasi",
    "Allahabad", "Ambala", "Dehradun", "Shimla", "Srinagar", "Jammu",
    
    # Central & West India
    "Ahmedabad", "Surat", "Vadodara", "Rajkot", "Bhavnagar", "Jamnagar",
    "Indore", "Bhopal", "Jabalpur", "Gwalior", "Ujjain", "Jaipur", "Jodhpur",
    "Kota", "Bikaner", "Ajmer", "Udaipur", "Raipur", "Bilaspur",
    
    # East & North East India
    "Kolkata", "Howrah", "Asansol", "Patna", "Gaya", "Bhagalpur", "Ranchi",
    "Jamshedpur", "Dhanbad", "Bhubaneswar", "Cuttack", "Rourkela", "Guwahati",
    "Imphal", "Shillong", "Agartala", "Aizawl", "Gangtok"
]

# Coordinate lookup for major Indian cities
COORDINATES = {
    "Chennai": [13.0827, 80.2707], "Coimbatore": [11.0168, 76.9558], "Madurai": [9.9252, 78.1198],
    "Bengaluru": [12.9716, 77.5946], "Hyderabad": [17.3850, 78.4867], "Mumbai": [19.0760, 72.8777],
    "Delhi": [28.6139, 77.2090], "Kolkata": [22.5726, 88.3639], "Pune": [18.5204, 73.8567],
    "Ahmedabad": [23.0225, 72.5714], "Jaipur": [26.9124, 75.7873], "Surat": [21.1702, 72.8311],
    "Lucknow": [26.8467, 80.9462], "Kanpur": [26.4499, 80.3319], "Nagpur": [21.1458, 79.0882],
    "Indore": [22.7196, 75.8577], "Thane": [19.2183, 72.9781], "Bhopal": [23.2599, 77.4126],
    "Visakhapatnam": [17.6868, 83.2185], "Patna": [25.5941, 85.1376], "Vadodara": [22.3072, 73.1812],
    "Ghaziabad": [28.6692, 77.4538], "Kochi": [9.9312, 76.2673], "Thiruvananthapuram": [8.5241, 76.9366],
    "Chandigarh": [30.7333, 76.7794], "Guwahati": [26.1158, 91.7086], "Bhubaneswar": [20.2961, 85.8245],
    "Noida": [28.5355, 77.3910], "Gurugram": [28.4595, 77.0266], "Faridabad": [28.4089, 77.3178],
    "Nashik": [19.9975, 73.7898], "Ranchi": [23.3441, 85.3096], "Meerut": [28.9845, 77.7064],
    "Rajkot": [22.3039, 70.8022], "Varanasi": [25.3176, 83.0061], "Srinagar": [34.0837, 74.7973],
    "Gwalior": [26.2183, 78.1828], "Jabalpur": [23.1815, 79.9864], "Raipur": [21.2514, 81.6296],
    "Kota": [25.2138, 75.8648], "Solapur": [17.6599, 75.9064], "Hubli": [15.3647, 75.1240],
    "Jodhpur": [26.2389, 73.0243], "Vijayawada": [16.5062, 80.6480], "Mysuru": [12.2958, 76.6394],
    "Kozhikode": [11.2588, 75.7804], "Dehradun": [30.3165, 78.0322], "Shimla": [31.1048, 77.1734]
}
# Default for other cities (Jitter around Center of India if not found)
def get_lat_lon(city):
    return COORDINATES.get(city, [21.0 + random.uniform(-5, 5), 78.0 + random.uniform(-5, 5)])
PROJECT_TYPES = ["Residential", "Commercial", "Industrial", "Institutional", "Mixed-Use"]
CERTIFICATION_LEVELS = ["None", "Bronze", "Silver", "Gold", "Platinum"]
POLICY_INTERVENTIONS = ["None", "Renewable Mandate", "Emission Cap", "Tax Incentive"]
LIFECYCLE_PHASES = ["Design", "Construction", "Operation", "Renovation", "Demolition"]

def generate_synthetic_data(num_samples):
    data = []
    
    for _ in range(num_samples):
        location = random.choice(LOCATIONS)
        project_type = random.choice(PROJECT_TYPES)
        building_area = round(random.uniform(500, 50000), 2)  # m2
        cert_level = random.choice(CERTIFICATION_LEVELS)
        policy = random.choice(POLICY_INTERVENTIONS)
        lifecycle = random.choice(LIFECYCLE_PHASES)
        
        # Base realistic values based on area
        # Embodied Emissions (kg CO2e / m2) * Area
        embodied_emissions = round((random.uniform(200, 800) * building_area) / 1000, 2) # Tons
        
        # Operational Emissions (kg CO2e / m2 / yr) * Area
        operational_emissions = round((random.uniform(50, 200) * building_area) / 1000, 2) # Tons/year
        
        # Percentages
        material_reuse = round(random.uniform(10, 80), 2)
        renewable_energy = round(random.uniform(5, 100), 2)
        waste_minimization = round(random.uniform(20, 95), 2)
        
        # Additional criteria for TOPSIS (Total 9)
        # 1. Embodied Emissions (Minimize)
        # 2. Operational Emissions (Minimize)
        # 3. Material Reuse % (Maximize)
        # 4. Renewable Energy % (Maximize)
        # 5. Waste Minimization % (Maximize)
        # 6. Water Efficiency % (Maximize)
        water_efficiency = round(random.uniform(10, 90), 2)
        
        # 7. Indoor Environmental Quality Index (1-10) (Maximize)
        ieq = round(random.uniform(4, 10), 1)
        
        # 8. Green Material Source % (Maximize)
        green_material = round(random.uniform(5, 75), 2)
        
        # 9. Lifecycle Cost Impact (USD / m2) (Minimize)
        cost_impact = round(random.uniform(50, 300), 2)

        lat, lon = get_lat_lon(location)

        project = {
            "Project Location": location,
            "Latitude": lat,
            "Longitude": lon,
            "Project Type": project_type,
            "Building Area (m2)": building_area,
            "Green Certification Level": cert_level,
            "Policy Intervention": policy,
            "Lifecycle Phase": lifecycle,
            "Embodied Emissions (Tons)": embodied_emissions,
            "Operational Emissions (Tons/yr)": operational_emissions,
            "Material Reuse (%)": material_reuse,
            "Renewable Energy (%)": renewable_energy,
            "Waste Minimization (%)": waste_minimization,
            "Water Efficiency (%)": water_efficiency,
            "IEQ Index": ieq,
            "Green Material Source (%)": green_material,
            "Lifecycle Cost Impact ($/m2)": cost_impact
        }

        # Simplified Score Calculation (Heuristic for initial data)
        score = (material_reuse*0.15 + renewable_energy*0.2 + waste_minimization*0.15 + water_efficiency*0.1 + ieq*5 + green_material*0.1) / 100
        score = min(score, 1.0)
        classification = "High" if score >= 0.75 else "Medium" if score >= 0.45 else "Low"
        
        project["TOPSIS Score"] = score
        project["Classification"] = classification
        data.append(project)
        
    return data

def main():
    print(f"Generating {NUM_PROJECTS} synthetic construction projects...")
    collection = get_collection()
    
    # Optional: Clear existing data
    collection.delete_many({})
    print("Cleared existing projects in the collection.")
    
    for i in range(0, NUM_PROJECTS, BATCH_SIZE):
        batch = generate_synthetic_data(BATCH_SIZE)
        collection.insert_many(batch)
        print(f"Inserted {i + BATCH_SIZE} / {NUM_PROJECTS} records...")
        
    print("Data generation and insertion complete!")

if __name__ == "__main__":
    main()
