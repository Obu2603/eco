import os
from pymongo import MongoClient
import streamlit as st
import random

# --- Database Configuration ---
DB_NAME = "eco_build_ai"
COLLECTION_NAME = "projects"

def load_mongo_uri():
    """Attempts to find a MongoDB URI in secrets or environment."""
    try:
        if "MONGO_URI" in st.secrets:
            return st.secrets["MONGO_URI"]
        if "connections" in st.secrets and "mongodb" in st.secrets["connections"]:
            return st.secrets["connections"]["mongodb"].get("uri") or st.secrets["connections"]["mongodb"].get("url")
    except Exception:
        pass
    
    env_uri = os.getenv("MONGO_URI")
    if env_uri:
        return env_uri
        
    is_cloud = os.getenv("STREAMLIT_SERVER_GATHER_USAGE_STATS") == "true" or os.getenv("STREAMLIT_SHARING_MODE") == "on"
    if not is_cloud:
        return "mongodb://localhost:27017/"
    return None

MONGO_URI = load_mongo_uri()
DB_AVAILABLE = False

def get_database():
    """Returns the MongoDB database instance or None if unavailable."""
    global DB_AVAILABLE
    if not MONGO_URI:
        DB_AVAILABLE = False
        return None
    
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.admin.command('ping') 
        DB_AVAILABLE = True
        return client[DB_NAME]
    except Exception:
        DB_AVAILABLE = False
        return None

def get_collection():
    """Returns the MongoDB collection instance or None."""
    db = get_database()
    return db[COLLECTION_NAME] if db is not None else None

# Initial check
get_database()

# --- Mock Data for Demo Mode ---
def get_mock_projects(limit=50):
    """Generates a list of mock projects for Demo Mode."""
    projects = []
    locations = ["Chennai", "Bengaluru", "Hyderabad", "Mumbai", "Delhi", "Pune", "Kolkata", "Ahmedabad"]
    types = ["Residential", "Commercial", "Industrial", "Institutional", "Mixed-Use"]
    
    for i in range(limit):
        score = random.uniform(0.3, 0.95)
        classification = "High" if score >= 0.75 else "Medium" if score >= 0.45 else "Low"
        projects.append({
            "Project Location": random.choice(locations),
            "Project Type": random.choice(types),
            "TOPSIS Score": score,
            "Classification": classification,
            "Embodied Emissions (Tons)": random.randint(500, 3000),
            "Operational Emissions (Tons/yr)": random.randint(100, 800),
            "Material Reuse (%)": random.randint(10, 80),
            "Renewable Energy (%)": random.randint(5, 95),
            "Waste Minimization (%)": random.randint(30, 90)
        })
    return sorted(projects, key=lambda x: x["TOPSIS Score"], reverse=True)

# UI Feedback
if not DB_AVAILABLE:
    is_cloud = os.getenv("STREAMLIT_SERVER_GATHER_USAGE_STATS") == "true" or os.getenv("STREAMLIT_SHARING_MODE") == "on"
    if is_cloud:
        st.info("💡 **Demo Mode**: Database not connected. Displaying sample data for preview.")

# --- Data Functions ---

def insert_projects(projects):
    collection = get_collection()
    if collection is not None and projects:
        try: collection.insert_many(projects)
        except Exception: pass

def save_evaluated_project(project_data):
    collection = get_collection()
    if collection is None: return
    try: collection.insert_one(project_data)
    except Exception: pass

@st.cache_data(ttl=300)
def get_similar_projects(project_type, location, limit=5):
    collection = get_collection()
    if collection is None:
        return [p for p in get_mock_projects(20) if p["Project Type"] == project_type][:limit]
    try:
        query = {"Project Type": project_type, "Project Location": location}
        return list(collection.find(query, {"_id": 0}).sort("TOPSIS Score", -1).limit(limit))
    except Exception: return []

@st.cache_data(ttl=300)
def get_top_projects(limit=10, search_query=None, project_type=None, classification=None):
    collection = get_collection()
    if collection is None:
        data = get_mock_projects(50)
        if search_query:
            data = [p for p in data if search_query.lower() in p["Project Location"].lower() or search_query.lower() in p["Project Type"].lower()]
        if project_type and project_type != "All":
            data = [p for p in data if p["Project Type"] == project_type]
        if classification and classification != "All":
            data = [p for p in data if p["Classification"] == classification]
        return data[:limit]
        
    try:
        query = {"TOPSIS Score": {"$exists": True}}
        if search_query:
            query["$or"] = [{"Project Location": {"$regex": search_query, "$options": "i"}}, {"Project Type": {"$regex": search_query, "$options": "i"}}]
        if project_type and project_type != "All": query["Project Type"] = project_type
        if classification and classification != "All": query["Classification"] = classification
        return list(collection.find(query, {"_id": 0}).sort("TOPSIS Score", -1).limit(limit))
    except Exception: return []

@st.cache_data(ttl=600)
def get_sustainability_stats():
    collection = get_collection()
    if collection is None:
        data = get_mock_projects(50)
        return {
            "total": len(data),
            "high": len([p for p in data if p["Classification"] == "High"]),
            "medium": len([p for p in data if p["Classification"] == "Medium"]),
            "low": len([p for p in data if p["Classification"] == "Low"])
        }
    try:
        return {
            "total": collection.count_documents({"TOPSIS Score": {"$exists": True}}),
            "high": collection.count_documents({"Classification": "High"}),
            "medium": collection.count_documents({"Classification": "Medium"}),
            "low": collection.count_documents({"Classification": "Low"})
        }
    except Exception: return {"total": 0, "high": 0, "medium": 0, "low": 0}

@st.cache_data(ttl=3600)
def get_metadata():
    collection = get_collection()
    if collection is None:
        return {"types": ["Residential", "Commercial", "Industrial", "Institutional", "Mixed-Use"]}
    try: return {"types": collection.distinct("Project Type")}
    except Exception: return {"types": ["Residential", "Commercial", "Industrial", "Institutional", "Mixed-Use"]}

@st.cache_data(ttl=60)
def count_projects():
    collection = get_collection()
    if collection is None: return 50
    try: return collection.count_documents({})
    except Exception: return 0
