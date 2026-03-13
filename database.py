import os
from pymongo import MongoClient

# Use local MongoDB by default
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "eco_build_ai"
COLLECTION_NAME = "projects"

def get_database():
    """Returns the MongoDB database instance."""
    client = MongoClient(MONGO_URI)
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

def get_similar_projects(project_type, location, limit=5):
    """Fetches similar projects from MongoDB based on type and location."""
    collection = get_collection()
    query = {"Project Type": project_type, "Project Location": location}
    
    # Sort by TOPSIS Score descending to get the best similar projects
    cursor = collection.find(query).sort("TOPSIS Score", -1).limit(limit)
    return list(cursor)

def get_top_projects(limit=10, search_query=None, project_type=None, classification=None):
    """Fetches projects with advanced filtering and search."""
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

    cursor = collection.find(query).sort("TOPSIS Score", -1).limit(limit)
    return list(cursor)

def get_sustainability_stats():
    """Returns counts of projects by classification and total."""
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

def get_metadata():
    """Returns unique project types and locations for filters."""
    collection = get_collection()
    types = collection.distinct("Project Type")
    return {"types": types}

def count_projects():
    """Returns the total number of projects in the database."""
    return get_collection().count_documents({})
