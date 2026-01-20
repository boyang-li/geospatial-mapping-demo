#!/usr/bin/env python3
"""
Object GPS Position Calculation
Calculates the GPS coordinates of an object given vehicle position, heading, and distance.
"""

import math


def get_object_gps(vehicle_lat, vehicle_lon, heading, distance):
    """
    Calculate GPS coordinates of an object relative to vehicle position.
    
    Uses the inverse Haversine formula (direct geodetic problem) to calculate
    the destination point given a starting point, bearing, and distance.
    
    Args:
        vehicle_lat: Vehicle latitude in decimal degrees
        vehicle_lon: Vehicle longitude in decimal degrees
        heading: Direction in degrees (0 = North, 90 = East, 180 = South, 270 = West)
        distance: Distance to object in meters
    
    Returns:
        Tuple (lat, lon) - GPS coordinates of the object in decimal degrees
    """
    # Earth's radius in meters
    R = 6371000.0
    
    # Convert latitude and heading to radians
    lat_rad = math.radians(vehicle_lat)
    lon_rad = math.radians(vehicle_lon)
    heading_rad = math.radians(heading)
    
    # Angular distance in radians
    angular_distance = distance / R
    
    # Calculate new latitude
    new_lat_rad = math.asin(
        math.sin(lat_rad) * math.cos(angular_distance) +
        math.cos(lat_rad) * math.sin(angular_distance) * math.cos(heading_rad)
    )
    
    # Calculate new longitude
    new_lon_rad = lon_rad + math.atan2(
        math.sin(heading_rad) * math.sin(angular_distance) * math.cos(lat_rad),
        math.cos(angular_distance) - math.sin(lat_rad) * math.sin(new_lat_rad)
    )
    
    # Convert back to degrees
    new_lat = math.degrees(new_lat_rad)
    new_lon = math.degrees(new_lon_rad)
    
    return (new_lat, new_lon)


if __name__ == "__main__":
    # Test case: Vehicle at a known position
    vehicle_lat = 37.7749  # San Francisco latitude
    vehicle_lon = -122.4194  # San Francisco longitude
    heading = 45  # Northeast
    distance = 100  # 100 meters
    
    object_lat, object_lon = get_object_gps(vehicle_lat, vehicle_lon, heading, distance)
    
    print(f"Testing get_object_gps function:")
    print(f"  Vehicle position: ({vehicle_lat:.6f}, {vehicle_lon:.6f})")
    print(f"  Heading: {heading}° (45° = Northeast)")
    print(f"  Distance: {distance} meters")
    print(f"\nResult:")
    print(f"  Object position: ({object_lat:.6f}, {object_lon:.6f})")
    print(f"  Lat offset: {(object_lat - vehicle_lat)*111320:.2f} meters")
    print(f"  Lon offset: {(object_lon - vehicle_lon)*111320*math.cos(math.radians(vehicle_lat)):.2f} meters")
    
    # Additional test cases
    print(f"\n--- Additional test cases ---")
    test_cases = [
        (0, "North"),
        (90, "East"),
        (180, "South"),
        (270, "West"),
        (45, "Northeast"),
    ]
    
    for test_heading, direction in test_cases:
        obj_lat, obj_lon = get_object_gps(vehicle_lat, vehicle_lon, test_heading, 100)
        lat_diff = (obj_lat - vehicle_lat) * 111320  # ~111.32 km per degree latitude
        lon_diff = (obj_lon - vehicle_lon) * 111320 * math.cos(math.radians(vehicle_lat))
        print(f"  Heading {test_heading:3d}° ({direction:9s}): "
              f"Δlat={lat_diff:7.2f}m, Δlon={lon_diff:7.2f}m → "
              f"({obj_lat:.6f}, {obj_lon:.6f})")
