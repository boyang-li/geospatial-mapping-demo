# Module Integration Test Results

**Date**: 2026-01-20  
**Test**: End-to-End Pipeline (Module A → Module B → Kafka)

---

## Test Summary

✅ **Module A: Perception Layer**
- **Input Video**: `data/videos/20260118191513_035087.MP4` (563MB)
- **Video Stats**: 5,400 frames @ 30 FPS (3 minutes)
- **Sampling**: 1 FPS (180 frames processed)
- **Total Detections**: 58 traffic lights
- **Processing Time**: 16.49s
- **Throughput**: 10.92 FPS average
- **Inference Time**: 44.85ms average per frame
- **Hardware**: M4 MacBook Pro with MPS acceleration

✅ **Module B: Ingestion Layer**
- **Input CSV**: 58 detections from Module A
- **Parse Rate**: 143,668 records/sec
- **Kafka Topic**: `sentinel_map_detections`
- **Messages Sent**: 58
- **Messages Acknowledged**: 58 (100% success)
- **Throughput**: 74.17 msg/sec
- **Total Time**: 782ms

✅ **Data Outputs**
- **Detection CSV**: `data/detections/detections.csv` (59 lines including header)
- **ROI Patches**: 58 images (256×256 JPEG) in `data/roi_patches/`
- **Kafka Messages**: 58 JSON records in Confluent Cloud

---

## Pipeline Performance

| Stage | Input | Output | Time | Throughput |
|-------|-------|--------|------|------------|
| Perception (Module A) | 563MB video | 58 detections | 16.49s | 10.92 FPS |
| Ingestion (Module B) | 58 CSV rows | 58 Kafka msgs | 0.78s | 74.17 msg/sec |
| **Total** | Video → Cloud | **58 records** | **17.27s** | **3.36 rec/sec** |

---

## Sample Detection Data

### CSV Output (Module A)
```csv
frame_number,timestamp_sec,u,v,confidence,class_name,vehicle_lat,vehicle_lon,heading
120,4.000,1290.50,571.00,0.6863,traffic light,43.790001,-79.313999,48.0
150,5.000,682.00,516.00,0.7473,traffic light,43.790002,-79.313998,48.8
180,6.000,1349.00,295.00,0.8522,traffic light,43.790002,-79.313998,49.5
```

### Kafka JSON (Module B → Confluent Cloud)
```json
{
  "detection_id": "550e8400-e29b-41d4-a716-446655440000",
  "vehicle_id": "vehicle-001",
  "session_id": "test-20260120-000241",
  "ingested_at": "2026-01-20T00:02:41Z",
  "frame_number": 120,
  "timestamp_sec": 4.0,
  "pixel_u": 1290.50,
  "pixel_v": 571.00,
  "confidence": 0.6863,
  "class_name": "traffic light",
  "vehicle_lat": 43.790001,
  "vehicle_lon": -79.313999,
  "heading": 48.0
}
```

---

## Validation Checklist

- [x] YOLOv8 model downloads automatically (yolov8n.pt)
- [x] M4 MPS acceleration works correctly
- [x] GPS simulation generates realistic coordinates
- [x] ROI patches extracted as 256×256 JPEG
- [x] CSV schema matches Module B expectations
- [x] Go producer reads CSV from new data directory
- [x] Kafka messages delivered to Confluent Cloud
- [x] 100% delivery success rate
- [x] No data loss in pipeline
- [x] Modular structure works correctly

---

## Performance Observations

### Module A (Perception)
- **Inference Speed**: ~45ms per frame is slower than expected ~10ms
  - Possible cause: YOLOv8n model on MPS might need optimization
  - Expected improvement: Fine-tune for traffic signs only
- **Sampling**: 1 FPS reduces 5,400 frames → 180 frames (96.7% reduction)
- **Detection Rate**: 58 detections / 180 frames = 32% frame hit rate

### Module B (Ingestion)
- **Parse Rate**: 143K rec/sec excellent for streaming CSV
- **Kafka Throughput**: 74 msg/sec (limited by small batch size)
  - Expected: 5K-15K msg/sec with larger datasets
- **Success Rate**: 100% with exponential backoff retry

---

## Next Steps

1. **Optimize YOLOv8 Inference**
   - Test with YOLOv8s (small) vs YOLOv8n (nano)
   - Fine-tune on traffic sign dataset
   - Explore TensorRT optimization

2. **Implement GPS OCR**
   - Replace simulated GPS with pytesseract extraction
   - Parse overlay text from frame bottom-left corner
   - Validate GPS accuracy

3. **Scale Testing**
   - Process 256GB dataset (100 hours video)
   - Benchmark throughput with 500K detections
   - Monitor Confluent Cloud metrics

4. **Add Stop Sign Detection**
   - Current: Only traffic lights detected
   - Expected: Add "stop sign" class
   - Fine-tune confidence threshold

---

## Conclusion

✅ **Both modules successfully integrated and tested end-to-end**

The modular architecture separates concerns effectively:
- Module A focuses on computer vision (Python/YOLOv8)
- Module B focuses on data streaming (Golang/Kafka)
- Data handoff via standardized CSV schema
- Clean directory structure with `modules/` and `data/`

**Status**: Production-ready for scaling tests
