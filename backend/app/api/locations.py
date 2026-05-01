from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from ..db import database, models
from ..schemas import schemas
from .auth import get_current_user
from ..core.report_pdf import generate_pdf_report
import random
import httpx

from ..ml.image_processor import process_image
from ..ml.emission_predictor import predictor
from ..ml.topsis_logic import calculate_topsis_score
from ..ml.recommendation_engine import generate_recommendations

router = APIRouter(prefix="/locations", tags=["Locations"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.LocationResponse)
def create_location(
    location: schemas.LocationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_location = models.Location(
        name=location.name,
        latitude=location.latitude,
        longitude=location.longitude,
        user_id=current_user.id
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

@router.post("/{location_id}/analyze", response_model=schemas.LocationResponse)
async def analyze_location(
    location_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
        
    image_bytes = await file.read()
    
    # 1. Process Image
    cv_data = process_image(image_bytes)
    
    # 2. Mock live environmental data
    aqi = round(random.uniform(20.0, 150.0), 2)
    temp = round(random.uniform(15.0, 35.0), 2)
    humidity = round(random.uniform(30.0, 90.0), 2)
    wind_speed = round(random.uniform(0.0, 25.0), 2)
    pollution_level = round(random.uniform(10.0, 100.0), 2)
    
    # 3. Predict Emissions
    features = {
        "green_cover_pct": cv_data['green_cover_pct'],
        "building_density": cv_data['building_density'],
        "road_traffic": cv_data['road_traffic'],
        "temperature": temp
    }
    predicted_emission = predictor.predict(features)
    
    # 4. TOPSIS Score
    # Map data to the 9 criteria for TOPSIS
    # ["Embodied Emissions", "Op Emissions", "Material Reuse", "Renewable Energy", "Waste Min", "Water Eff", "IEQ", "Green Mat", "Lifecycle Cost"]
    # We will derive these somewhat deterministically from our random base to make it interesting
    project_metrics = [
        predicted_emission * 2, # Embodied
        predicted_emission, # Operational
        cv_data['green_cover_pct'], # Reusing green cover as proxy for material reuse for demo
        random.uniform(10, 80), # Renewable
        random.uniform(20, 90), # Waste Min
        random.uniform(30, 95), # Water Eff
        80.0 - (aqi * 0.2), # IEQ
        cv_data['green_cover_pct'] + 10, # Green Mat
        1000 + (predicted_emission * 0.5) # Lifecycle cost
    ]
    
    topsis_result = calculate_topsis_score(project_metrics)
    recs = generate_recommendations(topsis_result['classification'], {
        'Renewable Energy (%)': project_metrics[3],
        'Waste Minimization (%)': project_metrics[4],
        'Material Reuse (%)': project_metrics[2],
        'Green Cover (%)': cv_data['green_cover_pct'],
        'Traffic Level': cv_data['road_traffic']
    }, predicted_emission)
    
    # Save Environmental Data
    env_data = models.EnvironmentalData(
        location_id=location.id,
        aqi=aqi,
        temperature=temp,
        humidity=humidity,
        wind_speed=wind_speed,
        pollution_level=pollution_level,
        green_cover_pct=cv_data['green_cover_pct'],
        building_density=cv_data['building_density'],
        road_traffic=cv_data['road_traffic'],
        water_bodies_pct=cv_data['water_bodies_pct'],
        predicted_carbon_emissions=predicted_emission,
        topsis_score=topsis_result['score'],
        sustainability_class=topsis_result['classification'],
        recommendation=recs,
        ai_confidence_score=round(random.uniform(0.7, 0.99), 2)
    )
    db.add(env_data)
    
    # Save Risk Data
    risk_data = models.RiskData(
        location_id=location.id,
        flood_risk=round(random.uniform(0, 1), 2),
        heat_zone=round(random.uniform(0, 1), 2),
        future_pollution_growth=round(random.uniform(-0.5, 0.5), 2)
    )
    db.add(risk_data)
    
    db.commit()
    db.refresh(location)
    
    return location

@router.get("/", response_model=list[schemas.LocationResponse])
def get_locations(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    locations = db.query(models.Location)\
        .options(joinedload(models.Location.environmental_data))\
        .filter(models.Location.user_id == current_user.id).all()
    return locations

@router.post("/simulate")
def simulate_location(req: schemas.ManualAnalysisRequest, current_user: models.User = Depends(get_current_user)):
    # 1. Predict Emissions
    features = {
        "green_cover_pct": req.green_cover_pct,
        "building_density": req.building_density,
        "road_traffic": req.road_traffic,
        "temperature": req.temperature,
        "energy_usage_estimate": req.energy_usage_estimate,
        "material_reuse_pct": req.material_reuse_pct
    }
    predicted_emission = predictor.predict(features)
    
    # 2. TOPSIS Score
    project_metrics = [
        predicted_emission * 2, # Embodied
        predicted_emission, # Operational
        req.material_reuse_pct, 
        random.uniform(10, 80), # Renewable
        random.uniform(20, 90), # Waste Min
        req.water_bodies_pct, # Water Eff
        80.0 - (req.aqi * 0.2), # IEQ
        req.green_cover_pct + 10, # Green Mat
        1000 + (predicted_emission * 0.5) # Lifecycle cost
    ]
    
    topsis_result = calculate_topsis_score(project_metrics)
    recs = generate_recommendations(topsis_result['classification'], {
        'Renewable Energy (%)': project_metrics[3],
        'Waste Minimization (%)': project_metrics[4],
        'Material Reuse (%)': project_metrics[2],
        'Green Cover (%)': req.green_cover_pct,
        'Traffic Level': req.road_traffic
    }, predicted_emission)
    
    return {
        "score": topsis_result['score'],
        "classification": topsis_result['classification'],
        "predicted_emission": predicted_emission,
        "recommendation": recs
    }

@router.post("/analyze-manual", response_model=schemas.LocationResponse)
def manual_analyze_location(req: schemas.ManualAnalysisRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Run the exact same logic as simulate to get values
    sim_result = simulate_location(req, current_user)
    
    # Create location
    location = models.Location(
        name=f"Manual Analysis: {req.city or 'Unspecified Location'}",
        latitude=req.latitude or 0.0,
        longitude=req.longitude or 0.0,
        user_id=current_user.id,
        project_type=req.project_type
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    
    # Create EnvironmentalData
    env_data = models.EnvironmentalData(
        location_id=location.id,
        aqi=req.aqi,
        temperature=req.temperature,
        humidity=req.humidity,
        wind_speed=0.0,
        pollution_level=req.aqi,
        green_cover_pct=req.green_cover_pct,
        building_density=req.building_density,
        road_traffic=req.road_traffic,
        water_bodies_pct=req.water_bodies_pct,
        energy_usage_estimate=req.energy_usage_estimate,
        material_reuse_pct=req.material_reuse_pct,
        predicted_carbon_emissions=sim_result["predicted_emission"],
        topsis_score=sim_result["score"],
        sustainability_class=sim_result["classification"],
        recommendation=sim_result["recommendation"],
        ai_confidence_score=0.95
    )
    db.add(env_data)
    
    # Create mock RiskData
    risk_data = models.RiskData(
        location_id=location.id,
        flood_risk=round(random.uniform(0, 1), 2),
        heat_zone=round(random.uniform(0, 1), 2),
        future_pollution_growth=round(random.uniform(-0.5, 0.5), 2)
    )
    db.add(risk_data)
    
    db.commit()
    db.refresh(location)
    
    return location

@router.get("/fetch-environment")
async def fetch_environmental_data(lat: float, lng: float):
    # Fetch real-time weather and AQI
    # Using Open-Meteo for free weather and AQI
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current_weather=true&hourly=relativehumidity_2m"
    aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lng}&current=us_aqi"
    
    import asyncio
    try:
        async with httpx.AsyncClient() as client:
            weather_resp, aqi_resp = await asyncio.gather(
                client.get(weather_url),
                client.get(aqi_url)
            )
            
            weather_data = weather_resp.json()
            aqi_data = aqi_resp.json()
            
            current_weather = weather_data.get('current_weather', {})
            temp = current_weather.get('temperature', 25)
            wind_speed = current_weather.get('windspeed', 10)
            
            # approximate humidity from hourly if available
            humidity_arr = weather_data.get('hourly', {}).get('relativehumidity_2m', [])
            humidity = humidity_arr[0] if humidity_arr else 50
            
            current_aqi_data = aqi_data.get('current', {})
            aqi = current_aqi_data.get('us_aqi', 50)
            
            return {
                "temperature": temp,
                "wind_speed": wind_speed,
                "humidity": humidity,
                "aqi": aqi,
                "pollution_level": aqi # approximate
            }
    except Exception as e:
        # Fallback if API fails
        return {
            "temperature": 25,
            "wind_speed": 10,
            "humidity": 50,
            "aqi": 50,
            "pollution_level": 50
        }

@router.delete("/{location_id}")
def delete_location(location_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    location = db.query(models.Location).filter(models.Location.id == location_id, models.Location.user_id == current_user.id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    db.delete(location)
    db.commit()
    return {"message": "Location deleted successfully"}

@router.get("/{location_id}/pdf")
async def get_location_pdf(location_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    location = db.query(models.Location).filter(models.Location.id == location_id, models.Location.user_id == current_user.id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    pdf_buffer = generate_pdf_report(location)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=EcoVision_Report_{location_id}.pdf"}
    )

