SentinelMap: Production-Grade Automated Map Audit System (MVP+) Specifications

1. Project Vision
A simulation of Lyft’s real-world mapping pipeline: utilizing vehicle sensors to capture visual features, processed through high-concurrency pipelines and cloud-native spatial analysis to detect discrepancies between reality and OpenStreetMap (OSM).

2. Core Architecture & Tech Stack
- Perception Layer: Python + YOLOv8 + CoreML (Optimized for M4 Apple Neural Engine)
- Ingestion Layer: Golang (High-performance Asynchronous Kafka Producer)
- Messaging: Confluent Cloud Kafka
- Storage & Compute: Snowflake (Geospatial Analytics)
- Modeling: dbt Cloud (T+0 Audit Reports)

3. Core Features & Engineering Challenges
A. Asynchronous Decoupled Perception
- Offline Inference: Process 256GB video offline to extract Frame ID, GPS, and object classes.
- ROI Extraction: Extract image patches of targets to simulate a 90% reduction in bandwidth costs.
- Hardware Acceleration: Utilize M4 ANE for quantized inference.

B. High-Performance Ingestion (Golang)
- Concurrent Streaming: Use Goroutines for high-throughput metadata streaming, simulating a large-scale fleet.
- Reliability: Implement Exponential Backoff and benchmarking for TPS (Transactions Per Second).

C. Geospatial Big Data Modeling (Snowflake & dbt)
- Geospatial-Aware Caching: Use H3/S2 indexing to determine area "freshness" and filter redundant audits.
- Spatial Audit Logic: Use ST_DISTANCE to calculate deviation between visual detections and OSM nodes.
- Discrepancy Classification: Automated labeling as Verified, Missing, or New Discovery.

4. Key KPIs
- Inference Throughput (FPS)
- Data Ingestion TPS and P99 Latency
- Map Discrepancy Recall
- Cost-per-Kilometer Analysis