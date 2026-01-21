#!/usr/bin/env python3
"""
OSM Ground Truth Ingestion to Snowflake
Parses local osm.xml and uploads to REF_OSM_NODES table with GEOGRAPHY type
"""

import xml.etree.ElementTree as ET
import snowflake.connector
import json
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_osm_xml(xml_file: str) -> list:
    """
    Parse OSM XML file and extract traffic sign nodes
    
    Args:
        xml_file: Path to osm.xml file
    
    Returns:
        List of dicts with OSM node data
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    nodes = []
    
    for node in root.findall('.//node'):
        # Extract basic attributes
        osm_id = node.get('id')
        lat = float(node.get('lat'))
        lon = float(node.get('lon'))
        
        # Extract all tags
        tags = {}
        for tag in node.findall('tag'):
            tags[tag.get('k')] = tag.get('v')
        
        # Filter for traffic signs
        if 'traffic_sign' in tags or 'highway' in tags:
            osm_type = tags.get('traffic_sign') or tags.get('highway', 'unknown')
            
            nodes.append({
                'osm_id': osm_id,
                'osm_type': osm_type,
                'lat': lat,
                'lon': lon,
                'tags': tags
            })
    
    return nodes

def create_geography_point(lat: float, lon: float) -> str:
    """
    Create Snowflake GEOGRAPHY point from lat/lon
    GEOGRAPHY uses (lon, lat) order per WGS84 standard
    """
    return f"ST_POINT({lon}, {lat})"

def upload_to_snowflake(nodes: list, source_file: str):
    """
    Upload OSM nodes to Snowflake REF_OSM_NODES table
    
    Args:
        nodes: List of parsed OSM nodes
        source_file: Original XML file name for tracking
    """
    # Connect to Snowflake
    conn = snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),  # Or use key-pair auth
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse='SENTINEL_WH',
        database='SENTINEL_MAP',
        schema='RAW'
    )
    
    cursor = conn.cursor()
    
    try:
        print(f"🚀 Uploading {len(nodes)} OSM nodes to Snowflake...")
        
        # Use executemany with batching for best performance
        batch_size = 16384  # Snowflake's max batch size
        total_inserted = 0
        
        insert_sql = """
        INSERT INTO REF_OSM_NODES 
        (OSM_ID, OSM_TYPE, LATITUDE, LONGITUDE, TAGS, UPLOADED_AT, SOURCE_FILE)
        SELECT column1, column2, column3, column4, PARSE_JSON(column5), CURRENT_TIMESTAMP(), column6
        FROM VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i+batch_size]
            
            # Prepare batch data
            batch_data = [
                (
                    node['osm_id'],
                    node['osm_type'],
                    node['lat'],
                    node['lon'],
                    json.dumps(node['tags']),
                    source_file
                )
                for node in batch
            ]
            
            cursor.executemany(insert_sql, batch_data)
            total_inserted += len(batch)
            
            print(f"✅ Inserted {total_inserted}/{len(nodes)} nodes")
        
        conn.commit()
        
        # Verify insertion
        cursor.execute("SELECT COUNT(*), COUNT(DISTINCT OSM_TYPE) FROM REF_OSM_NODES")
        total, types = cursor.fetchone()
        print(f"\n📊 Upload Summary:")
        print(f"   Total nodes: {total}")
        print(f"   Unique types: {types}")
        
        # Sample spatial query
        cursor.execute("""
        SELECT 
            OSM_ID,
            OSM_TYPE,
            LATITUDE,
            LONGITUDE
        FROM REF_OSM_NODES
        LIMIT 3
        """)
        
        print(f"\n🗺️  Sample Records:")
        for row in cursor:
            print(f"   ID: {row[0]}, Type: {row[1]}, Lat: {row[2]}, Lon: {row[3]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    
    finally:
        cursor.close()
        conn.close()

def main():
    # Path to your OSM XML file
    osm_file = Path('/Users/boyangli/Repo/sentinel-map/modules/local-mvp/toronto_traffic.xml')
    
    if not osm_file.exists():
        print(f"❌ File not found: {osm_file}")
        # Try relative path as fallback
        osm_file = Path(__file__).parent.parent / 'local-mvp' / 'toronto_traffic.xml'
        if not osm_file.exists():
            print(f"❌ Also tried: {osm_file}")
            return
    
    print(f"📖 Parsing {osm_file}...")
    nodes = parse_osm_xml(str(osm_file))
    
    print(f"✅ Found {len(nodes)} traffic infrastructure nodes")
    
    # Upload to Snowflake
    upload_to_snowflake(nodes, osm_file.name)
    
    print("\n✨ OSM ingestion complete!")

if __name__ == "__main__":
    main()
