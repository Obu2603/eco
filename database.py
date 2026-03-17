import os
from pymongo import MongoClient
import streamlit as st

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
        
    # Local fallback only if not explicitly on Cloud
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
        # Short timeout to detect if DB is actually reachable
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

# Check connectivity once at startup
get_database()

# UI Feedback for connection status
if not DB_AVAILABLE:
    is_cloud = os.getenv("STREAMLIT_SERVER_GATHER_USAGE_STATS") == "true" or os.getenv("STREAMLIT_SHARING_MODE") == "on"
    if is_cloud:
        st.info("ℹ️ **Offline Mode**: Running without database connection. Global analytics are disabled.")

# --- Data Functions ---

def insert_projects(projects):
    """Inserts a list of project dictionaries into the collection."""
    collection = get_collection()
    if collection is not None and projects:
        try:
            collection.insert_many(projects)
        except Exception: pass

def save_evaluated_project(project_data):
    """Saves a single evaluated project with TOPSIS score and coordinates to MongoDB."""
    collection = get_collection()
    if collection is None:
        return
        
    # Try to add coordinates if missing (e.g., from UI input)
    if "Latitude" not in project_data or "Longitude" not in project_data:
        try:
            from data_generator import get_lat_lon
            lat, lon = get_lat_lon(project_data.get("Project Location", "Unknown"))
            project_data["Latitude"] = lat
            project_data["Longitude"] = lon
        except Exception: pass
        
    try:
        collection.insert_one(project_data)
    except Exception: pass

@st.cache_data(ttl=300)
def get_similar_projects(project_type, location, limit=5):
    """Fetches similar projects from MongoDB based on type and location."""
    try:
        collection = get_collection()
        if collection is None: return []
        
        query = {"Project Type": project_type, "Project Location": location}
        cursor = collection.find(query, {"_id": 0}).sort("TOPSIS Score", -1).limit(limit)
        return list(cursor)
    except Exception:
        return []

@st.cache_data(ttl=300)
def get_top_projects(limit=10, search_query=None, project_type=None, classification=None):
    """Fetches projects with advanced filtering and search."""
    try:
        collection = get_collection()
        if collection is None: return []
        
        query = {"TOPSIS Score": {"$exists": True}}
        if search_query:
            query["$or"] = [
                {"Project Location": {"$regex": search_query, "$options": "i"}},
                {"Project Type": {"$regex": search_query, "$options": "i"}}
            ]
        
        if project_type and project_type != "All":
            query["Project Type"] = project_type
            
        if classification and classification != "All":
            query["Classification"] = classification

        cursor = collection.find(query, {"_id": 0}).sort("TOPSIS Score", -1).limit(limit)
        return list(cursor)
    except Exception:
        return []

@st.cache_data(ttl=600)
def get_sustainability_stats():
    """Returns counts of projects by classification and total."""
    try:
        collection = get_collection()
        if collection is None:
            return {"total": 0, "high": 0, "medium": 0, "low": 0}
            
        return {
            "total": collection.count_documents({"TOPSIS Score": {"$exists": True}}),
            "high": collection.count_documents({"Classification": "High"}),
            "medium": collection.count_documents({"Classification": "Medium"}),
            "low": collection.count_documents({"Classification": "Low"})
        }
    except Exception:
        return {"total": 0, "high": 0, "medium": 0, "low": 0}

@st.cache_data(ttl=3600)
def get_metadata():
    """Returns unique project types and locations for filters."""
    try:
        collection = get_collection()
        if collection is None:
             return {"types": ["Residential", "Commercial", "Industrial", "Institutional", "Mixed-Use"]}
        return {"types": collection.distinct("Project Type")}
    except Exception:
        return {"types": ["Residential", "Commercial", "Industrial", "Institutional", "Mixed-Use"]}

@st.cache_data(ttl=60)
def count_projects():
    """Returns the total number of projects in the database."""
    try:
        collection = get_collection()
        return collection.count_documents({}) if collection is not None else 0
    except Exception:
        return 0
