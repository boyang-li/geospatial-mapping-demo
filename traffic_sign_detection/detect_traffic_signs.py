#!/usr/bin/env python3
"""
YOLOv8 Traffic Sign Detection Script
Processes a video to detect traffic signs and extract bottom-center coordinates.
"""

import cv2
import csv
from ultralytics import YOLO
from pathlib import Path


def process_video(video_path, output_csv, model_path='yolov8n.pt', detect_all_signs=False, custom_classes=None):
    """
    Process video to detect traffic signs and save coordinates to CSV.
    
    Args:
        video_path: Path to input video file
        output_csv: Path to output CSV file
        model_path: Path to YOLOv8 model (default: yolov8n.pt)
        detect_all_signs: If True, detect all classes (useful for custom models)
        custom_classes: List of class names to detect (overrides detect_all_signs)
    """
    # Load YOLOv8 model
    print(f"Loading YOLOv8 model: {model_path}")
    model = YOLO(model_path)
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video FPS: {fps}, Total frames: {total_frames}")
    
    # Open CSV file for writing
    with open(output_csv, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write header
        csv_writer.writerow(['frame_number', 'timestamp_sec', 'u', 'v', 'confidence', 'class_name'])
        
        frame_number = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Calculate timestamp in seconds
            timestamp = frame_number / fps if fps > 0 else 0
            
            # Run YOLOv8 detection
            results = model(frame, verbose=False)
            
            # Process detections
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get class name
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    
                    # Determine if we should process this detection
                    should_process = False
                    
                    if custom_classes is not None:
                        # Use custom class list
                        should_process = class_name.lower() in [c.lower() for c in custom_classes]
                    elif detect_all_signs:
                        # Detect all classes (useful for custom traffic sign models)
                        should_process = True
                    else:
                        # Default: COCO classes with 'stop sign' and 'traffic light'
                        traffic_sign_classes = ['stop sign', 'traffic light']
                        should_process = class_name.lower() in traffic_sign_classes
                    
                    if should_process:
                        # Get bounding box coordinates (x1, y1, x2, y2)
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # Calculate bottom-center coordinates
                        u = (x1 + x2) / 2
                        v = y2
                        
                        # Get confidence
                        confidence = float(box.conf[0])
                        
                        # Write to CSV
                        csv_writer.writerow([
                            frame_number,
                            f"{timestamp:.3f}",
                            f"{u:.2f}",
                            f"{v:.2f}",
                            f"{confidence:.4f}",
                            class_name
                        ])
            
            frame_number += 1
            
            # Print progress
            if frame_number % 30 == 0:
                print(f"Processed {frame_number}/{total_frames} frames ({frame_number/total_frames*100:.1f}%)")
    
    cap.release()
    print(f"\nProcessing complete! Results saved to: {output_csv}")
    print(f"Total frames processed: {frame_number}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Detect traffic signs in video using YOLOv8')
    parser.add_argument('--video', type=str, required=True, help='Path to input video file')
    parser.add_argument('--output', type=str, default='traffic_signs.csv', help='Path to output CSV file')
    parser.add_argument('--model', type=str, default='yolov8n.pt', help='YOLOv8 model path (default: yolov8n.pt)')
    parser.add_argument('--all', action='store_true', help='Detect all classes (for custom traffic sign models)')
    parser.add_argument('--classes', type=str, nargs='+', help='Specific class names to detect (e.g., --classes "stop sign" "speed limit")')
    
    args = parser.parse_args()
    
    # Verify video file exists
    if not Path(args.video).exists():
        print(f"Error: Video file not found: {args.video}")
        exit(1)
    
    process_video(args.video, args.output, args.model, args.all, args.classes)
