# SentinelMap Analytics (dbt Cloud)

This directory contains the dbt models for transforming raw perception data into actionable insights.

## Architecture

- **Staging Layer**: Flattens VARIANT JSON and normalizes OSM data
- **Core Layer**: Performs spatial joins and audit classification  
- **Marts Layer**: Aggregated metrics and review queues

## Quick Start

1. Push this directory to your GitHub repo
2. In dbt Cloud, configure development environment pointing to this project
3. Run `dbt build` to create all models and run tests
4. View lineage with `dbt docs generate`

## Models

- `stg_perception_data`: Flattened detections with GEOGRAPHY points
- `stg_osm_ground_truth`: Normalized OSM reference data
- `fct_map_audit`: Core fact table with spatial matching (≤10m threshold)
- `audit_summary_metrics`: Daily aggregations by class and status
- `discrepancy_details`: Prioritized review queue (HIGH/MEDIUM/LOW)

## Custom Tests

- `assert_high_verification_rate`: Ensures ≥30% of high-confidence detections verified
- `assert_no_future_dates`: Detects system clock issues

## Configuration

Edit `dbt_project.yml` to adjust:
- `audit_threshold_meters`: Distance threshold for VERIFIED status (default: 10m)
