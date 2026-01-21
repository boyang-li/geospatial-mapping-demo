#!/usr/bin/env python3
"""
Test OCR extraction including timestamp from video overlay
"""
import cv2
import numpy as np
import re
from pathlib import Path

def extract_gps_and_timestamp_from_frame(frame: np.ndarray, debug: bool = False) -> tuple:
    """
    Extract GPS coordinates and timestamp from VIOFO A119 V3 frame overlay
    
    Returns:
        (latitude, longitude, heading, timestamp) tuple
    """
    try:
        import pytesseract
    except ImportError:
        print("⚠️  pytesseract not installed")
        return None, None, None, None
    
    h, w = frame.shape[:2]
    
    # Extract bottom-left region (GPS)
    overlay_height = int(h * 0.15)
    overlay_width = int(w * 0.35)
    gps_region = frame[h - overlay_height:h, 0:overlay_width]
    
    # Extract bottom-right region (timestamp)
    timestamp_width = int(w * 0.25)
    timestamp_region = frame[h - overlay_height:h, w - timestamp_width:w]
    
    # Preprocess both regions
    gray_gps = cv2.cvtColor(gps_region, cv2.COLOR_BGR2GRAY)
    _, binary_gps = cv2.threshold(gray_gps, 127, 255, cv2.THRESH_BINARY)
    
    gray_ts = cv2.cvtColor(timestamp_region, cv2.COLOR_BGR2GRAY)
    _, binary_ts = cv2.threshold(gray_ts, 127, 255, cv2.THRESH_BINARY)
    
    # Run OCR
    gps_text = pytesseract.image_to_string(binary_gps, config='--psm 6')
    timestamp_text = pytesseract.image_to_string(binary_ts, config='--psm 6')
    
    if debug:
        print(f"\n📝 GPS OCR: {gps_text.strip()}")
        print(f"📝 Timestamp OCR: {timestamp_text.strip()}")
    
    # Parse GPS coordinates
    lat = None
    lon = None
    heading = None
    
    lat_match = re.search(r'[NS]\s*(\d+\.?\s*\d+)', gps_text, re.IGNORECASE)
    if lat_match:
        lat = float(lat_match.group(1).replace(' ', ''))
        if 'S' in lat_match.group(0).upper():
            lat = -abs(lat)
    
    lon_match = re.search(r'[EW]\s*(\d+\.?\s*\d+)', gps_text, re.IGNORECASE)
    if lon_match:
        lon = float(lon_match.group(1).replace(' ', ''))
        if 'W' in lon_match.group(0).upper():
            lon = -abs(lon)
    
    speed_match = re.search(r'(\d+)\s*KM/H', gps_text, re.IGNORECASE)
    if speed_match:
        heading = float(speed_match.group(1))
    
    # Parse timestamp
    timestamp = None
    ts_patterns = [
        r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})',  # DD/MM/YYYY HH:MM:SS (VIOFO format)
        r'(\d{4}[-/]\d{2}[-/]\d{2}\s+\d{2}:\d{2}:\d{2})',  # YYYY-MM-DD HH:MM:SS or YYYY/MM/DD HH:MM:SS
        r'(\d{2}/\d{2}/\d{4})',  # DD/MM/YYYY (date only)
        r'(\d{4}[-/]\d{2}[-/]\d{2})',  # YYYY-MM-DD or YYYY/MM/DD (date only)
    ]
    for pattern in ts_patterns:
        match = re.search(pattern, timestamp_text)
        if match:
            timestamp = match.group(1)
            break
    
    return lat, lon, heading, timestamp


def main():
    # Test with video frame
    video_path = "/Users/boyangli/Repo/sentinel-map/data/videos/20260118191513_035087.MP4"
    
    print("="*80)
    print("GPS + Timestamp OCR Test")
    print("="*80)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Failed to open video: {video_path}")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"📹 Video: {fps:.1f} FPS")
    
    print(f"\n📍 Testing first 3 frames:")
    print("-"*80)
    
    for i in range(3):
        ret, frame = cap.read()
        if not ret:
            break
        
        import time
        start = time.time()
        lat, lon, heading, timestamp = extract_gps_and_timestamp_from_frame(frame, debug=(i==0))
        elapsed = time.time() - start
        
        ts_str = f"timestamp={timestamp}" if timestamp else "timestamp=None"
        print(f"Frame {i}: lat={lat:.6f}, lon={lon:.6f}, heading={heading:.1f}, {ts_str} ({elapsed:.2f}s)")
    
    cap.release()
    print("\n" + "="*80)
    print("✅ Test complete!")
    print("="*80)


if __name__ == "__main__":
    main()
