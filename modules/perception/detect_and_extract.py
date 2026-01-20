#!/usr/bin/env python3
"""
Module A: Perception Layer - Traffic Sign Detection & ROI Extraction

This module processes dashcam videos to:
1. Detect traffic signs using YOLOv8
2. Extract GPS coordinates from frame overlays
3. Extract 256x256 ROI patches around detections
4. Generate CSV metadata for ingestion layer

Hardware: Optimized for M4 MacBook Pro with MPS acceleration
"""

import argparse
import csv
import os
import time
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import numpy as np
from ultralytics import YOLO


class PerceptionPipeline:
    """End-to-end perception pipeline for traffic sign detection"""
    
    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        device: str = "mps",
        conf_threshold: float = 0.25,
        target_classes: List[str] = None
    ):
        """Initialize YOLOv8 model and configuration
        
        Args:
            model_path: Path to YOLOv8 weights
            device: 'mps' for M4, 'cuda' for GPU, 'cpu' for CPU
            conf_threshold: Minimum detection confidence
            target_classes: List of classes to detect (default: traffic signs)
        """
        print(f"🚀 Loading YOLOv8 model on {device}...")
        self.model = YOLO(model_path)
        self.device = device
        self.conf_threshold = conf_threshold
        self.target_classes = target_classes or ["stop sign", "traffic light"]
        
        # Performance metrics
        self.total_frames = 0
        self.total_detections = 0
        self.inference_times = []
        
    def extract_gps_from_frame(self, frame: np.ndarray, frame_number: int) -> Tuple[float, float, float]:
        """Extract GPS coordinates from frame overlay (bottom-left corner)
        
        TODO: Implement OCR-based extraction with pytesseract
        Current: Simulates GPS drift for testing
        
        Args:
            frame: Video frame (numpy array)
            frame_number: Current frame index
            
        Returns:
            (latitude, longitude, heading) tuple
        """
        # Simulated GPS drift (replace with OCR extraction)
        base_lat = 43.7900
        base_lon = -79.3140
        base_heading = 45.0
        
        # Simulate 0.0001 degree drift per 100 frames (~10 meters)
        lat = base_lat + (frame_number / 10000) * 0.0001
        lon = base_lon + (frame_number / 10000) * 0.0001
        heading = (base_heading + (frame_number / 100) * 2.5) % 360
        
        return lat, lon, heading
    
    def extract_roi_patch(
        self,
        frame: np.ndarray,
        bbox: Tuple[int, int, int, int],
        patch_size: int = 256
    ) -> np.ndarray:
        """Extract centered ROI patch around detection
        
        Args:
            frame: Original video frame
            bbox: Bounding box (x1, y1, x2, y2)
            patch_size: Output patch size (default 256x256)
            
        Returns:
            Cropped and resized patch
        """
        x1, y1, x2, y2 = bbox
        
        # Calculate center and square crop
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        half_size = max(x2 - x1, y2 - y1) // 2
        
        # Extract patch with boundary checks
        h, w = frame.shape[:2]
        crop_x1 = max(0, center_x - half_size)
        crop_y1 = max(0, center_y - half_size)
        crop_x2 = min(w, center_x + half_size)
        crop_y2 = min(h, center_y + half_size)
        
        patch = frame[crop_y1:crop_y2, crop_x1:crop_x2]
        
        # Resize to standard size
        patch_resized = cv2.resize(patch, (patch_size, patch_size))
        
        return patch_resized
    
    def process_video(
        self,
        video_path: str,
        output_csv: str,
        output_patches_dir: str,
        sample_fps: int = 1
    ) -> dict:
        """Process video and generate detections
        
        Args:
            video_path: Path to input video
            output_csv: Path to output CSV file
            output_patches_dir: Directory to save ROI patches
            sample_fps: Sampling rate (process 1 frame every N fps)
            
        Returns:
            Processing statistics
        """
        print(f"📹 Processing video: {video_path}")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        video_fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_interval = max(1, video_fps // sample_fps)
        
        print(f"🎬 Video FPS: {video_fps}, Total Frames: {total_frames}")
        print(f"⏱️  Sampling: 1 frame every {frame_interval} frames ({sample_fps} FPS)")
        
        # Create output directory
        os.makedirs(output_patches_dir, exist_ok=True)
        
        # Open CSV writer
        csv_file = open(output_csv, 'w', newline='')
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow([
            'frame_number', 'timestamp_sec', 'u', 'v',
            'confidence', 'class_name',
            'vehicle_lat', 'vehicle_lon', 'heading'
        ])
        
        frame_count = 0
        processed_count = 0
        detection_count = 0
        
        start_time = time.time()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Sample frames
            if frame_count % frame_interval != 0:
                frame_count += 1
                continue
            
            # Extract GPS from frame overlay
            vehicle_lat, vehicle_lon, heading = self.extract_gps_from_frame(frame, frame_count)
            
            # Run YOLOv8 inference
            inference_start = time.time()
            results = self.model(frame, conf=self.conf_threshold, device=self.device, verbose=False)
            inference_time = time.time() - inference_start
            self.inference_times.append(inference_time)
            
            # Process detections
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get detection data
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    class_name = result.names[class_id]
                    
                    # Filter by target classes
                    if class_name not in self.target_classes:
                        continue
                    
                    # Calculate bottom-center pixel coordinates
                    u = (x1 + x2) / 2
                    v = y2  # Bottom edge
                    
                    # Extract ROI patch
                    patch = self.extract_roi_patch(frame, (x1, y1, x2, y2))
                    patch_filename = f"frame_{frame_count:06d}_det_{detection_count:04d}.jpg"
                    patch_path = os.path.join(output_patches_dir, patch_filename)
                    cv2.imwrite(patch_path, patch)
                    
                    # Write CSV row
                    timestamp_sec = frame_count / video_fps
                    csv_writer.writerow([
                        frame_count,
                        f"{timestamp_sec:.3f}",
                        f"{u:.2f}",
                        f"{v:.2f}",
                        f"{confidence:.4f}",
                        class_name,
                        f"{vehicle_lat:.6f}",
                        f"{vehicle_lon:.6f}",
                        f"{heading:.1f}"
                    ])
                    
                    detection_count += 1
            
            processed_count += 1
            frame_count += 1
            
            # Progress update
            if processed_count % 100 == 0:
                elapsed = time.time() - start_time
                fps = processed_count / elapsed
                print(f"⏳ Processed {processed_count} frames, {detection_count} detections ({fps:.1f} FPS)")
        
        cap.release()
        csv_file.close()
        
        # Calculate metrics
        elapsed_time = time.time() - start_time
        avg_inference_time = np.mean(self.inference_times) if self.inference_times else 0
        avg_fps = processed_count / elapsed_time if elapsed_time > 0 else 0
        
        stats = {
            'total_frames': frame_count,
            'processed_frames': processed_count,
            'total_detections': detection_count,
            'elapsed_time': elapsed_time,
            'avg_fps': avg_fps,
            'avg_inference_ms': avg_inference_time * 1000,
            'output_csv': output_csv,
            'output_patches_dir': output_patches_dir
        }
        
        print("\n" + "="*60)
        print("✅ Processing Complete!")
        print("="*60)
        print(f"📊 Total Frames: {frame_count}")
        print(f"🔍 Processed Frames: {processed_count}")
        print(f"🎯 Total Detections: {detection_count}")
        print(f"⏱️  Elapsed Time: {elapsed_time:.2f}s")
        print(f"🚀 Average FPS: {avg_fps:.2f}")
        print(f"⚡ Average Inference: {avg_inference_time*1000:.2f}ms")
        print(f"📁 CSV Output: {output_csv}")
        print(f"🖼️  ROI Patches: {output_patches_dir}")
        print("="*60)
        
        return stats


def main():
    parser = argparse.ArgumentParser(
        description="Module A: Perception Layer - Traffic Sign Detection"
    )
    parser.add_argument(
        "--video",
        type=str,
        required=True,
        help="Path to input video file"
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="../../data/detections/detections.csv",
        help="Path to output CSV file (default: ../../data/detections/detections.csv)"
    )
    parser.add_argument(
        "--output-patches",
        type=str,
        default="../../data/roi_patches",
        help="Directory to save ROI patches (default: ../../data/roi_patches)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="Path to YOLOv8 model weights (default: yolov8n.pt)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="mps",
        choices=["mps", "cuda", "cpu"],
        help="Device for inference (default: mps for M4)"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold (default: 0.25)"
    )
    parser.add_argument(
        "--sample-fps",
        type=int,
        default=1,
        help="Sampling rate in FPS (default: 1)"
    )
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = PerceptionPipeline(
        model_path=args.model,
        device=args.device,
        conf_threshold=args.conf
    )
    
    # Process video
    pipeline.process_video(
        video_path=args.video,
        output_csv=args.output_csv,
        output_patches_dir=args.output_patches,
        sample_fps=args.sample_fps
    )


if __name__ == "__main__":
    main()
