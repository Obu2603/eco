from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
import enum
import datetime
from .database import Base

class RoleEnum(str, enum.Enum):
    USER = "User"
    ENGINEER = "Engineer"
    GOVERNMENT = "Government"
    ADMIN = "Admin"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(Enum(RoleEnum), default=RoleEnum.USER)
    is_active = Column(Boolean, default=True)

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    project_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    owner = relationship("User")
    environmental_data = relationship("EnvironmentalData", back_populates="location", uselist=False)
    risk_data = relationship("RiskData", back_populates="location", uselist=False)

class EnvironmentalData(Base):
    __tablename__ = "environmental_data"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    
    # Live/Scraped Data
    aqi = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    wind_speed = Column(Float)
    pollution_level = Column(Float)
    
    # ML Extracted Data / Manual Data
    green_cover_pct = Column(Float)
    building_density = Column(Float)
    road_traffic = Column(Float)
    water_bodies_pct = Column(Float)
    energy_usage_estimate = Column(Float, nullable=True)
    material_reuse_pct = Column(Float, nullable=True)
    
    # Predicted Data
    predicted_carbon_emissions = Column(Float)
    topsis_score = Column(Float)
    sustainability_class = Column(String) # Low, Medium, High
    recommendation = Column(String)
    ai_confidence_score = Column(Float, nullable=True)
    
    location = relationship("Location", back_populates="environmental_data")

class RiskData(Base):
    __tablename__ = "risk_data"
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    
    flood_risk = Column(Float) # 0 to 1
    heat_zone = Column(Float) # 0 to 1
    future_pollution_growth = Column(Float)
    
    location = relationship("Location", back_populates="risk_data")
