-- Copy and run these commands in Snowflake (requires ACCOUNTADMIN role)

USE ROLE ACCOUNTADMIN;

-- Allow dbt to create schemas (DBT_DEV, STAGING, CORE, MARTS)
GRANT CREATE SCHEMA ON DATABASE SENTINEL_MAP TO ROLE SENTINEL_ROLE;

-- Allow dbt to create tables/views in schemas it creates
GRANT ALL PRIVILEGES ON FUTURE SCHEMAS IN DATABASE SENTINEL_MAP TO ROLE SENTINEL_ROLE;

-- Allow dbt to use warehouse compute
GRANT OPERATE ON WAREHOUSE SENTINEL_WH TO ROLE SENTINEL_ROLE;
