import random

def process_image(image_bytes: bytes) -> dict:
    """
    Mock implementation of CV model (YOLO/ResNet) that would normally:
    1. Load image via OpenCV
    2. Pass through PyTorch/TF model to detect greenery, buildings, water
    3. Calculate percentages
    """
    # In a real scenario, we would use cv2.imdecode(np.frombuffer(image_bytes, np.uint8), -1)
    
    # Simulate realistic-looking data
    green_cover_pct = round(random.uniform(10.0, 60.0), 2)
    building_density = round(random.uniform(20.0, 80.0), 2)
    water_bodies_pct = round(random.uniform(0.0, 15.0), 2)
    road_traffic = round(random.uniform(10.0, 50.0), 2)
    
    return {
        "green_cover_pct": green_cover_pct,
        "building_density": building_density,
        "water_bodies_pct": water_bodies_pct,
        "road_traffic": road_traffic
    }
