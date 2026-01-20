#!/usr/bin/env python3
"""
Real Data Comparison Test
Compares actual detected traffic signs from video with OSM ground truth.

This script requires:
1. traffic_signs.csv - YOLO detections with pixel coordinates
2. osm.xml - OSM ground truth GPS coordinates
3. Vehicle GPS/heading data for each frame (to be provided)
"""

import csv
import sys
sys.path.insert(0, '/Users/boyangli/Repo/Mapping')

from compare_gps import parse_osm_xml, osm_nodes_to_coordinates, compare_gps_lists, print_results, save_results_to_csv
from pixel_to_distance import pixel_to_distance
from get_object_gps import get_object_gps


def load_detected_signs(csv_file):
    """Load detected traffic signs from CSV file."""
    detections = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            detections.append({
                'frame': int(row['frame_number']),
                'timestamp': float(row['timestamp_sec']),
                'u': float(row['u']),
                'v': float(row['v']),
                'confidence': float(row['confidence']),
                'class': row['class_name']
            })
    return detections


def convert_detections_to_gps(detections, vehicle_gps_data, H=1440, h=1.4, v_fov=92):
    """
    Convert pixel coordinates to GPS coordinates.
    
    Args:
        detections: List of detection dictionaries with 'frame', 'u', 'v'
        vehicle_gps_data: Dict mapping frame_number to (lat, lon, heading)
        H: Image height in pixels
        h: Camera height in meters
        v_fov: Vertical field of view in degrees
    
    Returns:
        List of (lat, lon) tuples for detected objects
    """
    gps_coordinates = []
    
    for detection in detections:
        frame = detection['frame']
        v_pixel = detection['v']
        
        # Get vehicle GPS and heading for this frame
        if frame not in vehicle_gps_data:
            print(f"Warning: No GPS data for frame {frame}, skipping...")
            continue
        
        vehicle_lat, vehicle_lon, heading = vehicle_gps_data[frame]
        
        # Convert pixel to distance
        distance = pixel_to_distance(v_pixel, H=H, h=h, v_fov=v_fov)
        
        # Skip if object is above horizon (infinite distance)
        if distance == float('inf'):
            continue
        
        # Convert to GPS coordinates
        object_lat, object_lon = get_object_gps(vehicle_lat, vehicle_lon, heading, distance)
        gps_coordinates.append((object_lat, object_lon))
        
        # Optional: store the GPS in the detection dict for reference
        detection['gps_lat'] = object_lat
        detection['gps_lon'] = object_lon
        detection['distance_m'] = distance
    
    return gps_coordinates


if __name__ == "__main__":
    print("="*80)
    print("REAL DATA COMPARISON TEST")
    print("="*80)
    
    # Step 1: Load detected traffic signs from CSV
    print("\n1. Loading detected traffic signs from video...")
    detections = load_detected_signs('/Users/boyangli/Repo/Mapping/traffic_signs.csv')
    print(f"   Loaded {len(detections)} detections")
    print(f"   Classes: {set(d['class'] for d in detections)}")
    print(f"   Frames: {min(d['frame'] for d in detections)} to {max(d['frame'] for d in detections)}")
    
    # Step 2: Load OSM ground truth
    print("\n2. Loading OSM ground truth...")
    osm_nodes = parse_osm_xml('/Users/boyangli/Repo/Mapping/osm.xml', 'traffic_sign', None)
    osm_ground_truth = osm_nodes_to_coordinates(osm_nodes)
    print(f"   Loaded {len(osm_ground_truth)} traffic signs from OSM")
    for i, (lat, lon) in enumerate(osm_ground_truth, 1):
        print(f"   {i}. ({lat:.6f}, {lon:.6f})")
    
    # Step 3: Check for vehicle GPS/heading data
    print("\n3. Loading vehicle GPS/heading data...")
    print("   ⚠️  WARNING: Vehicle GPS/heading data not available!")
    print("   To complete the comparison, you need a file or source with:")
    print("   - Vehicle latitude for each frame")
    print("   - Vehicle longitude for each frame")
    print("   - Vehicle heading (0-360°) for each frame")
    print()
    print("   Creating SIMULATED vehicle GPS data for demonstration...")
    
    # SIMULATED: Create fake vehicle GPS data
    # In reality, this would come from your vehicle's GPS log
    # Assuming vehicle is near Toronto (where OSM data is from)
    vehicle_gps_data = {}
    base_lat = 43.7900  # Starting latitude
    base_lon = -79.3140  # Starting longitude
    base_heading = 0  # North
    
    # Simulate vehicle moving slowly north
    for detection in detections:
        frame = detection['frame']
        # Simulate slight movement (very rough approximation)
        lat_offset = frame * 0.00001  # Small incremental movement
        vehicle_gps_data[frame] = (base_lat + lat_offset, base_lon, base_heading)
    
    print(f"   Simulated GPS data for {len(vehicle_gps_data)} frames")
    print(f"   Starting position: ({base_lat}, {base_lon}), heading: {base_heading}°")
    
    # Step 4: Convert detections to GPS coordinates
    print("\n4. Converting pixel coordinates to GPS...")
    
    gps_coordinates = []  # Initialize here
    
    # Check v-pixel distribution
    v_values = [d['v'] for d in detections]
    below_horizon = sum(1 for v in v_values if v > 720)
    above_horizon = sum(1 for v in v_values if v <= 720)
    
    print(f"   V-pixel distribution:")
    print(f"   - Min v: {min(v_values):.1f}, Max v: {max(v_values):.1f}")
    print(f"   - Horizon at v=720 (H/2)")
    print(f"   - Below horizon (v > 720): {below_horizon} detections")
    print(f"   - Above horizon (v <= 720): {above_horizon} detections")
    
    if above_horizon == len(detections):
        print(f"\n   ⚠️  ALL detections are above the horizon!")
        print(f"   This means all traffic signs are elevated (on poles).")
        print(f"   The current pixel_to_distance() function assumes ground-level objects.")
        print(f"\n   Options:")
        print(f"   1. Use a fixed assumed distance (e.g., 20m, 50m)")
        print(f"   2. Modify the distance calculation for elevated objects")
        print(f"   3. Use only horizontal position for approximate matching")
        print(f"\n   Using FIXED DISTANCE of 30 meters for demonstration...")
        
        # Use fixed distance for all detections
        fixed_distance = 30.0
        for detection in detections:
            frame = detection['frame']
            if frame not in vehicle_gps_data:
                continue
            
            vehicle_lat, vehicle_lon, heading = vehicle_gps_data[frame]
            object_lat, object_lon = get_object_gps(vehicle_lat, vehicle_lon, heading, fixed_distance)
            gps_coordinates.append((object_lat, object_lon))
            detection['gps_lat'] = object_lat
            detection['gps_lon'] = object_lon
            detection['distance_m'] = fixed_distance
        
        detected_gps = gps_coordinates
    else:
        detected_gps = convert_detections_to_gps(detections, vehicle_gps_data)
    
    print(f"   Converted {len(detected_gps)} detections to GPS coordinates")
    
    # Show sample conversions
    print("\n   Sample conversions:")
    for i in range(min(5, len(detections))):
        det = detections[i]
        if 'gps_lat' in det:
            print(f"   Frame {det['frame']}: v={det['v']:.0f}px → "
                  f"dist={det['distance_m']:.1f}m → "
                  f"GPS=({det['gps_lat']:.6f}, {det['gps_lon']:.6f})")
    
    # Step 5: Compare with OSM ground truth
    print("\n5. Comparing detected signs with OSM ground truth...")
    print("="*80)
    
    results = compare_gps_lists(detected_gps, osm_ground_truth)
    
    # Print results
    print_results(results)
    
    # Save to CSV
    save_results_to_csv(results, 'real_comparison_results.csv')
    
    print("\n" + "="*80)
    print("NOTE: This comparison uses SIMULATED vehicle GPS data!")
    print("For accurate results, provide real GPS/heading data for each frame.")
    print("="*80)
