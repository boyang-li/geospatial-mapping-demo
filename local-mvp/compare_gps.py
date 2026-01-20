#!/usr/bin/env python3
"""
GPS Coordinate Comparison Script
Compares detected objects with OpenStreetMap ground truth data.
"""

import math
import csv
import xml.etree.ElementTree as ET
from typing import List, Tuple, Dict


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on Earth.
    
    Args:
        lat1, lon1: Coordinates of first point in decimal degrees
        lat2, lon2: Coordinates of second point in decimal degrees
    
    Returns:
        Distance in meters
    """
    # Earth's radius in meters
    R = 6371000.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def find_nearest(point, point_list):
    """
    Find the nearest point in a list to a given point.
    
    Args:
        point: Tuple (lat, lon) of the reference point
        point_list: List of tuples [(lat, lon), ...]
    
    Returns:
        Tuple (nearest_point, distance, index)
    """
    if not point_list:
        return None, float('inf'), -1
    
    min_distance = float('inf')
    nearest_point = None
    nearest_index = -1
    
    for idx, other_point in enumerate(point_list):
        dist = haversine_distance(point[0], point[1], other_point[0], other_point[1])
        if dist < min_distance:
            min_distance = dist
            nearest_point = other_point
            nearest_index = idx
    
    return nearest_point, min_distance, nearest_index


def parse_osm_xml(osm_file_path, tag_key='highway', tag_value='traffic_signals'):
    """
    Parse an OSM XML file and extract nodes with specific tags.
    
    Args:
        osm_file_path: Path to the OSM XML file
        tag_key: The tag key to search for (default: 'highway')
        tag_value: The tag value to match (default: 'traffic_signals'). 
                   Use None to match any value for the tag_key.
    
    Returns:
        List of dictionaries with 'id', 'lat', 'lon' for each matching node
    """
    nodes = []
    
    try:
        tree = ET.parse(osm_file_path)
        root = tree.getroot()
        
        # Find all node elements
        for node in root.findall('.//node'):
            # Check if this node has the specified tag
            for tag in node.findall('tag'):
                if tag_value is None:
                    # Match any value for the tag_key
                    if tag.get('k') == tag_key:
                        node_data = {
                            'id': node.get('id'),
                            'lat': float(node.get('lat')),
                            'lon': float(node.get('lon')),
                            'type': tag.get('v')
                        }
                        nodes.append(node_data)
                        break
                else:
                    # Match specific tag_key and tag_value
                    if tag.get('k') == tag_key and tag.get('v') == tag_value:
                        node_data = {
                            'id': node.get('id'),
                            'lat': float(node.get('lat')),
                            'lon': float(node.get('lon'))
                        }
                        nodes.append(node_data)
                        break  # Found matching tag, no need to check other tags
        
    except Exception as e:
        print(f"Error parsing OSM file: {e}")
        return []
    
    return nodes


def osm_nodes_to_coordinates(osm_nodes):
    """
    Convert list of OSM node dictionaries to list of (lat, lon) tuples.
    
    Args:
        osm_nodes: List of dictionaries with 'lat' and 'lon' keys
    
    Returns:
        List of tuples [(lat, lon), ...]
    """
    return [(node['lat'], node['lon']) for node in osm_nodes]


def compare_gps_lists(detected_objects, osm_ground_truth, verify_threshold=10.0, missing_threshold=15.0):
    """
    Compare detected objects with OSM ground truth.
    
    Args:
        detected_objects: List of tuples [(lat, lon), ...]
        osm_ground_truth: List of tuples [(lat, lon), ...]
        verify_threshold: Distance in meters to consider a match as verified (default: 10)
        missing_threshold: Distance in meters to search for missing signs (default: 15)
    
    Returns:
        Dict with 'verified', 'new_signs', and 'missing_signs' lists
    """
    results = {
        'verified': [],
        'new_signs': [],
        'missing_signs': []
    }
    
    # Track which OSM points have been matched
    osm_matched = [False] * len(osm_ground_truth)
    
    # Process each detected object
    for det_idx, detected_point in enumerate(detected_objects):
        nearest_osm, distance, osm_idx = find_nearest(detected_point, osm_ground_truth)
        
        if distance < verify_threshold:
            # Verified match
            results['verified'].append({
                'detected_point': detected_point,
                'osm_point': nearest_osm,
                'distance': distance,
                'detected_index': det_idx,
                'osm_index': osm_idx
            })
            osm_matched[osm_idx] = True
        else:
            # New sign detected
            results['new_signs'].append({
                'detected_point': detected_point,
                'nearest_osm': nearest_osm,
                'distance': distance,
                'detected_index': det_idx
            })
    
    # Find missing signs (OSM points not matched within threshold)
    for osm_idx, osm_point in enumerate(osm_ground_truth):
        # Check if this OSM point has any detected object within missing_threshold
        nearest_det, distance, det_idx = find_nearest(osm_point, detected_objects)
        
        if distance >= missing_threshold:
            results['missing_signs'].append({
                'osm_point': osm_point,
                'nearest_detected': nearest_det,
                'distance': distance,
                'osm_index': osm_idx
            })
    
    return results


def print_results(results):
    """Print comparison results in a formatted way."""
    print("=" * 80)
    print("GPS COORDINATE COMPARISON RESULTS")
    print("=" * 80)
    
    print(f"\n✓ VERIFIED SIGNS ({len(results['verified'])} matches)")
    print("-" * 80)
    if results['verified']:
        for item in results['verified']:
            print(f"  Detected: ({item['detected_point'][0]:.6f}, {item['detected_point'][1]:.6f})")
            print(f"  OSM:      ({item['osm_point'][0]:.6f}, {item['osm_point'][1]:.6f})")
            print(f"  Distance: {item['distance']:.2f} meters")
            print()
    else:
        print("  No verified matches found.\n")
    
    print(f"⚠ NEW SIGNS DETECTED ({len(results['new_signs'])} objects)")
    print("-" * 80)
    if results['new_signs']:
        for item in results['new_signs']:
            print(f"  Detected: ({item['detected_point'][0]:.6f}, {item['detected_point'][1]:.6f})")
            if item['nearest_osm']:
                print(f"  Nearest OSM: ({item['nearest_osm'][0]:.6f}, {item['nearest_osm'][1]:.6f})")
                print(f"  Distance: {item['distance']:.2f} meters (> 10m threshold)")
            else:
                print(f"  No OSM points available for comparison")
            print()
    else:
        print("  No new signs detected.\n")
    
    print(f"✗ MISSING SIGNS ON ROAD ({len(results['missing_signs'])} from OSM)")
    print("-" * 80)
    if results['missing_signs']:
        for item in results['missing_signs']:
            print(f"  OSM Point: ({item['osm_point'][0]:.6f}, {item['osm_point'][1]:.6f})")
            if item['nearest_detected']:
                print(f"  Nearest Detected: ({item['nearest_detected'][0]:.6f}, {item['nearest_detected'][1]:.6f})")
                print(f"  Distance: {item['distance']:.2f} meters (> 15m threshold)")
            else:
                print(f"  No detected objects found")
            print()
    else:
        print("  All OSM signs were detected.\n")
    
    print("=" * 80)
    print(f"Summary: {len(results['verified'])} verified, "
          f"{len(results['new_signs'])} new, "
          f"{len(results['missing_signs'])} missing")
    print("=" * 80)


def save_results_to_csv(results, output_file='comparison_results.csv'):
    """Save comparison results to CSV file."""
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Status', 'Detected_Lat', 'Detected_Lon', 'OSM_Lat', 'OSM_Lon', 'Distance_m'])
        
        for item in results['verified']:
            writer.writerow([
                'Verified',
                f"{item['detected_point'][0]:.6f}",
                f"{item['detected_point'][1]:.6f}",
                f"{item['osm_point'][0]:.6f}",
                f"{item['osm_point'][1]:.6f}",
                f"{item['distance']:.2f}"
            ])
        
        for item in results['new_signs']:
            writer.writerow([
                'New Sign Detected',
                f"{item['detected_point'][0]:.6f}",
                f"{item['detected_point'][1]:.6f}",
                f"{item['nearest_osm'][0]:.6f}" if item['nearest_osm'] else '',
                f"{item['nearest_osm'][1]:.6f}" if item['nearest_osm'] else '',
                f"{item['distance']:.2f}" if item['nearest_osm'] else 'N/A'
            ])
        
        for item in results['missing_signs']:
            det_lat = item['nearest_detected'][0] if item['nearest_detected'] else ''
            det_lon = item['nearest_detected'][1] if item['nearest_detected'] else ''
            writer.writerow([
                'Missing Sign on Road',
                det_lat,
                det_lon,
                f"{item['osm_point'][0]:.6f}",
                f"{item['osm_point'][1]:.6f}",
                f"{item['distance']:.2f}" if item['nearest_detected'] else 'N/A'
            ])
    
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    import sys
    
    # Check if OSM file is provided
    if len(sys.argv) > 1:
        osm_file = sys.argv[1]
        
        # Optional: tag key and value can be provided as arguments
        tag_key = sys.argv[2] if len(sys.argv) > 2 else 'traffic_sign'
        tag_value = sys.argv[3] if len(sys.argv) > 3 else None  # None = any value
        
        print(f"Parsing OSM file: {osm_file}")
        if tag_value:
            print(f"Looking for: {tag_key}={tag_value}\n")
        else:
            print(f"Looking for any nodes with tag: {tag_key}\n")
        
        # Parse OSM XML file
        if tag_value:
            osm_nodes = parse_osm_xml(osm_file, tag_key, tag_value)
        else:
            # Modified to accept any value for the tag
            osm_nodes = []
            try:
                tree = ET.parse(osm_file)
                root = tree.getroot()
                for node in root.findall('.//node'):
                    for tag in node.findall('tag'):
                        if tag.get('k') == tag_key:
                            node_data = {
                                'id': node.get('id'),
                                'lat': float(node.get('lat')),
                                'lon': float(node.get('lon')),
                                'type': tag.get('v')
                            }
                            osm_nodes.append(node_data)
                            break
            except Exception as e:
                print(f"Error parsing OSM file: {e}")
        
        print("=" * 80)
        print("OSM TRAFFIC SIGNS EXTRACTION")
        print("=" * 80)
        print(f"Total signs found: {len(osm_nodes)}\n")
        
        if osm_nodes:
            print("Traffic sign coordinates:")
            for i, node in enumerate(osm_nodes, 1):
                type_info = f" (Type: {node.get('type', 'N/A')})" if 'type' in node else ""
                print(f"  {i}. ID: {node['id']:15s}{type_info} - ({node['lat']:.6f}, {node['lon']:.6f})")
            
            # Convert to coordinates for comparison
            osm_ground_truth = osm_nodes_to_coordinates(osm_nodes)
            
            print("\n" + "=" * 80)
            print("Ready for GPS comparison!")
            print("=" * 80)
            print(f"OSM ground truth list has {len(osm_ground_truth)} coordinate pairs")
            print("\nTo use this data, import and call:")
            print("  from compare_gps import compare_gps_lists")
            print("  results = compare_gps_lists(detected_objects, osm_ground_truth)")
        else:
            print("No traffic signs found in the OSM file.")
        
        sys.exit(0)
    
    # Original test data if no OSM file provided
    print("No OSM file provided. Running with test data...\n")
    
    # Test data: Simulated detected objects and OSM ground truth
    # (Replace with actual data from your detection and OSM queries)
    
    # Detected objects (from YOLO detection + GPS calculation)
    detected_objects = [
        (37.7749, -122.4194),   # Matches OSM point 1 closely
        (37.7750, -122.4195),   # Matches OSM point 2 closely
        (37.7755, -122.4200),   # New sign (far from any OSM point)
        (37.7760, -122.4205),   # Matches OSM point 3 with ~8m error
    ]
    
    # OSM ground truth data
    osm_ground_truth = [
        (37.77492, -122.41938),  # Close to detected 1
        (37.77501, -122.41952),  # Close to detected 2
        (37.77595, -122.42048),  # Close to detected 4
        (37.7770, -122.4210),    # Missing (no detection within 15m)
    ]
    
    print("Running GPS coordinate comparison...\n")
    print(f"Detected objects: {len(detected_objects)}")
    print(f"OSM ground truth: {len(osm_ground_truth)}")
    print()
    
    # Compare the lists
    results = compare_gps_lists(detected_objects, osm_ground_truth)
    
    # Print results
    print_results(results)
    
    # Save to CSV
    save_results_to_csv(results)
