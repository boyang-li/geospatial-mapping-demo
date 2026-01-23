import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

def get_snowflake_connection():
    """Create Snowflake connection using environment variables."""
    return snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA'),
        role=os.getenv('SNOWFLAKE_ROLE')
    )

def get_config():
    """Get dashboard configuration from environment variables."""
    return {
        'refresh_interval': int(os.getenv('REFRESH_INTERVAL_SECONDS', 30)),
        'map_center_lat': float(os.getenv('MAP_CENTER_LAT', 43.790)),
        'map_center_lon': float(os.getenv('MAP_CENTER_LON', -79.314)),
        'map_zoom': int(os.getenv('MAP_ZOOM', 11))
    }
