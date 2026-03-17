import os
from pymongo import MongoClient
import streamlit as st

# Use Streamlit secrets for deployment, fallback to environment variable or local MongoDB
# Check multiple possible secret keys for flexibility
MONGO_URI = st.secrets.get("MONGO_URI") or os.getenv("MONGO_URI")

if not MONGO_URI:
    MONGO_URI = "mongodb://localhost:27017/"
    # If we are likely running on Cloud, warn the user
    if os.environ.get("STREAMLIT_SERVER_PORT") or os.environ.get("DYNO"):
        st.warning("⚠️ MONGO_URI secret missing. Defaulting to localhost (which usually fail in deployment). Please add MONGO_URI to your Streamlit Secrets.")
DB_NAME = "eco_build_ai"
COLLECTION_NAME = "projects"

def get_database():
    """Returns the MongoDB database instance."""
    # Add a 5-second timeout to prevent the UI from hanging on deployment
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return client[DB_NAME]

def get_collection():
    """Returns the MongoDB collection instance."""
    db = get_database()
    return db[COLLECTION_NAME]

def insert_projects(projects):
    """Inserts a list of project dictionaries into the collection."""
    collection = get_collection()
    if projects:
        collection.insert_many(projects)

def save_evaluated_project(project_data):
    """Saves a single evaluated project with TOPSIS score and coordinates to MongoDB."""
    collection = get_collection()
    
    # Try to add coordinates if missing (e.g., from UI input)
    if "Latitude" not in project_data or "Longitude" not in project_data:
        # Import here to avoid circular dependency if any
        from data_generator import get_lat_lon
        lat, lon = get_lat_lon(project_data.get("Project Location", "Unknown"))
        project_data["Latitude"] = lat
        project_data["Longitude"] = lon
        
    collection.insert_one(project_data)

@st.cache_data(ttl=300)
def get_similar_projects(project_type, location, limit=5):
    """Fetches similar projects from MongoDB based on type and location."""
    try:
        collection = get_collection()
        query = {"Project Type": project_type, "Project Location": location}
        
        # Sort by TOPSIS Score descending to get the best similar projects
        cursor = collection.find(query, {"_id": 0}).sort("TOPSIS Score", -1).limit(limit)
        return list(cursor)
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return []

@st.cache_data(ttl=300)
def get_top_projects(limit=10, search_query=None, project_type=None, classification=None):
    """Fetches projects with advanced filtering and search."""
    try:
        collection = get_collection()
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
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return []

@st.cache_data(ttl=600)
def get_sustainability_stats():
    """Returns counts of projects by classification and total."""
    try:
        collection = get_collection()
        total = collection.count_documents({"TOPSIS Score": {"$exists": True}})
        high = collection.count_documents({"Classification": "High"})
        medium = collection.count_documents({"Classification": "Medium"})
        low = collection.count_documents({"Classification": "Low"})
        
        return {
            "total": total,
            "high": high,
            "medium": medium,
            "low": low
        }
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return {"total": 0, "high": 0, "medium": 0, "low": 0}

@st.cache_data(ttl=3600)
def get_metadata():
    """Returns unique project types and locations for filters."""
    try:
        collection = get_collection()
        types = collection.distinct("Project Type")
        return {"types": types}
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return {"types": ["Residential", "Commercial", "Industrial", "Institutional", "Mixed-Use"]}

@st.cache_data(ttl=60)
def count_projects():
    """Returns the total number of projects in the database."""
    try:
        return get_collection().count_documents({})
    except Exception as e:
        print(f"Database connection error: {e}")
        return 0
