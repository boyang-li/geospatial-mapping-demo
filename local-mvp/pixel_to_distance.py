#!/usr/bin/env python3
"""
Pixel to Distance Conversion
Calculates distance to an object based on its vertical pixel position in the image.
"""

import math


def pixel_to_distance(v_pixel, H=1440, h=1.4, v_fov=92, v_horizon=None):
    """
    Calculate distance to an object based on its vertical pixel position.
    
    Args:
        v_pixel: Vertical pixel coordinate (y-coordinate, with origin at top)
        H: Image height in pixels (default: 1440)
        h: Camera height above ground in meters (default: 1.4)
        v_fov: Vertical field of view in degrees (default: 92)
        v_horizon: Vertical pixel position of the horizon (default: H/2 if not specified)
    
    Returns:
        Distance to object in meters, or float('inf') if above horizon
    """
    # Use H/2 as horizon if not specified
    if v_horizon is None:
        v_horizon = H / 2
    
    # Calculate vertical offset from horizon
    delta_v = v_pixel - v_horizon
    
    # If delta_v <= 0, the object is above the horizon
    if delta_v <= 0:
        return float('inf')
    
    # Calculate the angle below the horizon
    alpha = math.atan((delta_v / (H / 2)) * math.tan(math.radians(v_fov / 2)))
    
    # Calculate distance using camera height and angle
    D = h / math.tan(alpha)
    
    return D


if __name__ == "__main__":
    # Test with v_pixel = 761 (sign bottom) and horizon at H/2 = 720
    v_pixel_test = 761
    distance = pixel_to_distance(v_pixel_test)
    
    print(f"Testing pixel_to_distance function:")
    print(f"  v_pixel = {v_pixel_test} (sign bottom)")
    print(f"  v_horizon = 720 (H/2, camera parallel to ground)")
    print(f"  H = 1440 (image height)")
    print(f"  h = 1.4 m (camera height)")
    print(f"  v_fov = 92° (vertical field of view)")
    print(f"\nCalculation:")
    print(f"  delta_v = {v_pixel_test} - 720 = {v_pixel_test - 720}")
    if math.isinf(distance):
        print(f"  Distance D = infinity (above horizon)")
    else:
        print(f"  Distance D = {distance:.2f} meters")
    
    # Additional test cases with horizon at H/2 = 720
    print(f"\n--- Additional test cases (with horizon at H/2 = 720) ---")
    test_cases = [
        (720, "At horizon"),
        (500, "Above horizon"),
        (761, "Sign bottom"),
        (900, "Below horizon"),
        (1000, "Further below horizon"),
        (1440, "Bottom of image"),
    ]
    
    for v_pix, description in test_cases:
        dist = pixel_to_distance(v_pix)
        if math.isinf(dist):
            print(f"  v_pixel={v_pix:4d} -> {description:25s} : infinity (above horizon)")
        else:
            print(f"  v_pixel={v_pix:4d} -> {description:25s} : {dist:8.2f} m")
