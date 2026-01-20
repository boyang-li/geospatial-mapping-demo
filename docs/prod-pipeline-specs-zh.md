SentinelMap: 生产级自动地图审计系统 (MVP+) 需求规格书

1. 项目愿景
本项目旨在模拟 Lyft 真实业务场景：利用车辆传感器捕捉视觉特征，通过高并发数据流水线与云原生空间分析，自动检测现实世界与 OpenStreetMap (OSM) 之间的差异。

2. 核心架构与技术栈
- 边缘感知层: Python + YOLOv8 + CoreML (针对 M4 ANE 优化)
- 数据摄取层: Golang (高性能异步 Kafka Producer)
- 消息队列: Confluent Cloud Kafka
- 存储与计算: Snowflake (Geospatial 分析)
- 数据建模: dbt Cloud (T+0 审计报告)

3. 核心功能与工程挑战
A. 异步解耦感知 (Perception)
- 离线推理: 针对 256GB 视频进行离线检测，提取 Frame ID, GPS, 物体类别。
- ROI 提取: 仅提取目标物体的图像切片，模拟生产环境 90% 带宽节省。
- 硬件加速: 利用 MacBook Pro M4 的神经网络引擎 (ANE) 进行量化推理。

B. 高性能摄取 (Ingestion - Golang)
- 高并发推送: 使用 Goroutines 并发推送元数据，模拟大规模车辆同时上传。
- 可靠性: 实现指数退避重试机制与生产吞吐量 (TPS) 性能评估。

C. 空间大数据建模 (Snowflake & dbt)
- 地理感知缓存 (Geospatial Caching): 使用 H3/S2 索引判定区域新鲜度，过滤冗余审计。
- 空间审计逻辑: 调用 ST_DISTANCE 计算视觉点与 OSM 节点偏差。
- 审计结论分类: 自动标记为 Verified (已验证), Missing (地图缺失), New (新增)。

4. 关键 KPI
- 推理吞吐量 (FPS)
- 数据传输 TPS 与 P99 延迟
- 地图差异召回率 (Recall)
- 处理成本 (Cost per Kilometer)