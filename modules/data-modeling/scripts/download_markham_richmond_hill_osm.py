#!/usr/bin/env python3
"""
Download OSM traffic infrastructure data for Markham and Richmond Hill
Based on actual detection locations from batch_detections.csv
"""

import requests
import os

# Bounding box covering Markham and Richmond Hill detection areas
# Based on your data: lat 43.79-43.85, lon -79.32 to -79.31
BBOX = {
    'south': 43.78,   # Slightly expanded for coverage
    'north': 43.86,
    'west': -79.33,
    'east': -79.30
}

OUTPUT_FILE = "../../data/markham_richmond_hill_traffic.xml"

# Overpass API query
OVERPASS_QUERY = f"""
[out:xml][timeout:180];
(
  node["highway"="traffic_signals"]({BBOX['south']},{BBOX['west']},{BBOX['north']},{BBOX['east']});
  node["highway"="stop"]({BBOX['south']},{BBOX['west']},{BBOX['north']},{BBOX['east']});
  node["traffic_sign"="stop"]({BBOX['south']},{BBOX['west']},{BBOX['north']},{BBOX['east']});
  node["crossing"="traffic_signals"]({BBOX['south']},{BBOX['west']},{BBOX['north']},{BBOX['east']});
);
out body;
>;
out skel qt;
"""

def download_osm_data():
    """Download OSM data from Overpass API"""
    # Try different Overpass API mirrors
    urls = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
    ]
    
    print(f"📍 Downloading OSM data for Markham & Richmond Hill...")
    print(f"   Bounding box: {BBOX}")
    print(f"   Query types: traffic_signals, stop signs, crossings")
    
    for i, url in enumerate(urls, 1):
        try:
            print(f"\n🔄 Attempt {i}/{len(urls)} using {url.split('/')[2]}...")
            response = requests.post(url, data={'data': OVERPASS_QUERY}, timeout=240)
            response.raise_for_status()
            
            # Create output directory if needed
            os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
            
            # Save to file
            with open(OUTPUT_FILE, 'wb') as f:
                f.write(response.content)
            
            # Get file size
            size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
            
            print(f"\n✅ Download complete!")
            print(f"   File: {OUTPUT_FILE}")
            print(f"   Size: {size_mb:.2f} MB")
            print(f"\nNext steps:")
            print(f"1. Run: python ingest_osm_to_snowflake.py")
            print(f"2. In Snowflake, run: SELECT COUNT(*) FROM RAW.REF_OSM_NODES WHERE SOURCE_FILE LIKE '%markham%';")
            print(f"3. In analytics dir, run: dbt run")
            return
            
        except requests.exceptions.Timeout:
            print(f"   ⏱️  Timeout - trying next mirror...")
            continue
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {e}")
            if i < len(urls):
                print(f"   Trying next mirror...")
                continue
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            break
    
    print("\n❌ All mirrors failed. You can download manually:")
    print(f"   1. Go to: https://overpass-turbo.eu/")
    print(f"   2. Paste the query (printed below)")
    print(f"   3. Click 'Export' → 'Download as raw OSM data'")
    print(f"   4. Save as: {OUTPUT_FILE}")
    print(f"\nQuery:")
    print(OVERPASS_QUERY)

if __name__ == "__main__":
    download_osm_data()
