#!/usr/bin/env python3
"""
Batch Video Processing Script
Processes all videos in a directory and aggregates detections into a single CSV
"""

import argparse
import time
from pathlib import Path
from detect_and_extract import PerceptionPipeline
import csv
import os
from datetime import datetime

def process_batch(video_dir: str, output_csv: str, output_patches_dir: str, 
                  conf: float = 0.5, sample_fps: int = 1, device: str = "mps"):
    """
    Process all MP4 videos in a directory
    
    Args:
        video_dir: Directory containing video files
        output_csv: Path to aggregated output CSV
        output_patches_dir: Directory for ROI patches
        conf: Confidence threshold
        sample_fps: Sampling rate
        device: Inference device
    """
    video_path = Path(video_dir)
    
    # Find all video files
    video_files = sorted(video_path.glob("*.MP4"))
    if not video_files:
        video_files = sorted(video_path.glob("*.mp4"))
    
    if not video_files:
        print(f"❌ No video files found in {video_dir}")
        return
    
    print(f"╔═══════════════════════════════════════════════════════════╗")
    print(f"║   SentinelMap - Batch Video Processing                   ║")
    print(f"╚═══════════════════════════════════════════════════════════╝")
    print(f"📁 Video Directory: {video_dir}")
    print(f"🎬 Found {len(video_files)} videos")
    print(f"📊 Output CSV: {output_csv}")
    print(f"🖼️  Output Patches: {output_patches_dir}")
    print(f"⚙️  Confidence: {conf}, Sample FPS: {sample_fps}, Device: {device}")
    print(f"───────────────────────────────────────────────────────────")
    
    # Initialize pipeline once (model loaded only once)
    pipeline = PerceptionPipeline(
        model_path="yolov8n.pt",
        device=device,
        conf_threshold=conf
    )
    
    # Prepare output CSV
    os.makedirs(Path(output_csv).parent, exist_ok=True)
    os.makedirs(output_patches_dir, exist_ok=True)
    
    # Track statistics
    total_detections = 0
    total_frames_processed = 0
    total_time = 0
    video_stats = []
    
    # Open output CSV for writing (append mode)
    with open(output_csv, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        
        # Write header
        csv_writer.writerow([
            'video_name', 'frame_number', 'timestamp_sec', 'u', 'v',
            'confidence', 'class_name',
            'vehicle_lat', 'vehicle_lon', 'recording_timestamp'
        ])
        
        # Process each video
        for idx, video_file in enumerate(video_files, 1):
            print(f"\n🎬 [{idx}/{len(video_files)}] Processing: {video_file.name}")
            
            video_start = time.time()
            
            # Use a temporary CSV for this video
            temp_csv = f"/tmp/temp_{video_file.stem}.csv"
            
            try:
                pipeline.process_video(
                    video_path=str(video_file),
                    output_csv=temp_csv,
                    output_patches_dir=output_patches_dir,
                    sample_fps=sample_fps
                )
                
                video_time = time.time() - video_start
                
                # Read temp CSV and append to main CSV (skip header)
                detections_count = 0
                with open(temp_csv, 'r') as temp_file:
                    temp_reader = csv.reader(temp_file)
                    next(temp_reader)  # Skip header
                    
                    for row in temp_reader:
                        # Prepend video name to each row
                        csv_writer.writerow([video_file.name] + row)
                        detections_count += 1
                
                # Update statistics
                total_detections += detections_count
                total_frames_processed += pipeline.total_detections  # Approximate
                total_time += video_time
                
                video_stats.append({
                    'name': video_file.name,
                    'detections': detections_count,
                    'time': video_time
                })
                
                print(f"✅ {video_file.name}: {detections_count} detections in {video_time:.1f}s")
                
                # Clean up temp file
                os.remove(temp_csv)
                
            except Exception as e:
                print(f"❌ Error processing {video_file.name}: {e}")
                continue
    
    # Print summary
    print(f"\n╔═══════════════════════════════════════════════════════════╗")
    print(f"║                   BATCH PROCESSING COMPLETE               ║")
    print(f"╚═══════════════════════════════════════════════════════════╝")
    print(f"📊 Videos Processed: {len(video_stats)}/{len(video_files)}")
    print(f"🎯 Total Detections: {total_detections}")
    print(f"⏱️  Total Time: {total_time:.1f}s")
    print(f"🚀 Average FPS: {total_frames_processed / total_time:.2f}" if total_time > 0 else "N/A")
    print(f"📈 Detections per Video: {total_detections / len(video_stats):.1f}" if video_stats else "N/A")
    print(f"───────────────────────────────────────────────────────────")
    
    # Top 5 videos by detection count
    if video_stats:
        print(f"\n🏆 Top 5 Videos by Detection Count:")
        sorted_stats = sorted(video_stats, key=lambda x: x['detections'], reverse=True)
        for i, stat in enumerate(sorted_stats[:5], 1):
            print(f"   {i}. {stat['name']}: {stat['detections']} detections ({stat['time']:.1f}s)")
    
    print(f"\n✨ Batch processing complete!")
    print(f"📁 Output CSV: {output_csv}")
    print(f"🖼️  ROI Patches: {output_patches_dir}")


def main():
    parser = argparse.ArgumentParser(description="Batch process multiple videos")
    
    parser.add_argument(
        "--video-dir",
        type=str,
        required=True,
        help="Directory containing video files"
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default="../../data/detections/batch_detections.csv",
        help="Path to output CSV file"
    )
    parser.add_argument(
        "--output-patches",
        type=str,
        default="../../data/roi_patches",
        help="Directory to save ROI patches"
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.5,
        help="Confidence threshold (default: 0.5)"
    )
    parser.add_argument(
        "--sample-fps",
        type=int,
        default=1,
        help="Sampling rate in FPS (default: 1)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="mps",
        choices=["mps", "cuda", "cpu"],
        help="Device for inference (default: mps)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of videos to process (for testing)"
    )
    
    args = parser.parse_args()
    
    process_batch(
        video_dir=args.video_dir,
        output_csv=args.output_csv,
        output_patches_dir=args.output_patches,
        conf=args.conf,
        sample_fps=args.sample_fps,
        device=args.device
    )


if __name__ == "__main__":
    main()
