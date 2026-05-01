from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from ..db.models import RoleEnum

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: RoleEnum = RoleEnum.USER

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[RoleEnum] = None

class EnvironmentalDataBase(BaseModel):
    aqi: float
    temperature: float
    humidity: float
    wind_speed: float
    pollution_level: float
    green_cover_pct: float
    building_density: float
    road_traffic: float
    water_bodies_pct: float
    energy_usage_estimate: Optional[float] = None
    material_reuse_pct: Optional[float] = None
    predicted_carbon_emissions: float
    topsis_score: float
    sustainability_class: str
    recommendation: str
    ai_confidence_score: Optional[float] = None

class ManualAnalysisRequest(BaseModel):
    aqi: float
    temperature: float
    humidity: float
    green_cover_pct: float
    building_density: float # 0.0 to 100.0
    road_traffic: float
    water_bodies_pct: float
    energy_usage_estimate: float
    material_reuse_pct: float
    project_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    area: Optional[str] = None

class RiskDataBase(BaseModel):
    flood_risk: float
    heat_zone: float
    future_pollution_growth: float

class LocationCreate(BaseModel):
    name: str
    latitude: float
    longitude: float
    project_type: Optional[str] = None

class LocationResponse(LocationCreate):
    id: int
    created_at: datetime
    user_id: int
    environmental_data: Optional[EnvironmentalDataBase] = None
    risk_data: Optional[RiskDataBase] = None

    class Config:
        from_attributes = True
