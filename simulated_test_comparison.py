#!/usr/bin/env python3
"""
Test script to compare detected traffic signs with OSM ground truth.
"""

import sys
sys.path.insert(0, '/Users/boyangli/Repo/Mapping')

from compare_gps import parse_osm_xml, osm_nodes_to_coordinates, compare_gps_lists, print_results, save_results_to_csv

# Parse OSM ground truth
print("Loading OSM ground truth data...")
osm_nodes = parse_osm_xml('/Users/boyangli/Repo/Mapping/osm.xml', 'traffic_sign', None)
osm_ground_truth = osm_nodes_to_coordinates(osm_nodes)

print(f"Loaded {len(osm_ground_truth)} traffic signs from OSM:")
for i, (lat, lon) in enumerate(osm_ground_truth, 1):
    print(f"  {i}. ({lat:.6f}, {lon:.6f})")

# Simulated detected objects
# In reality, these would come from:
# 1. YOLO detection (traffic_signs.csv) -> pixel coordinates (u, v)
# 2. pixel_to_distance() -> distance in meters
# 3. get_object_gps() -> GPS coordinates (lat, lon)
# 
# For this test, we'll use simulated coordinates near the OSM locations

print("\n" + "="*80)
print("SIMULATED DETECTION TEST")
print("="*80)
print("\nSimulating detected traffic signs with GPS coordinates...")

# Simulated detections:
# - 2 close to OSM points (should be verified)
# - 1 far from any OSM point (new sign detected)
# - OSM points 3 and 4 will have no matches (missing signs)
detected_objects = [
    (43.7991350, -79.3168040),  # Very close to OSM point 1 (~0.6m)
    (43.7854800, -79.3113680),  # Very close to OSM point 2 (~0.8m)
    (43.7920000, -79.3150000),  # Far from any OSM point (~2km away - new sign)
]

print(f"Simulated {len(detected_objects)} detected objects:")
for i, (lat, lon) in enumerate(detected_objects, 1):
    print(f"  {i}. ({lat:.6f}, {lon:.6f})")

# Run comparison
print("\n" + "="*80)
print("Running GPS comparison...")
print("="*80 + "\n")

results = compare_gps_lists(detected_objects, osm_ground_truth)

# Print detailed results
print_results(results)

# Save to CSV
save_results_to_csv(results, 'simulated_comparison_results.csv')

print("\n" + "="*80)
print("EXPECTED RESULTS:")
print("="*80)
print("✓ 2 verified matches (detected objects 1 & 2 match OSM points 1 & 2)")
print("⚠ 1 new sign detected (detected object 3 is far from all OSM points)")
print("✗ 2 missing signs (OSM points 3 & 4 have no nearby detections)")
print("="*80)
