package models

import (
	"encoding/json"
	"time"
)

// Detection represents a single traffic sign detection event
type Detection struct {
	// Metadata
	DetectionID  string    `json:"detection_id"`
	VehicleID    string    `json:"vehicle_id"`
	SessionID    string    `json:"session_id"`
	IngestedAt   time.Time `json:"ingested_at"`
	
	// Frame-level data
	FrameNumber   int       `json:"frame_number"`
	TimestampSec  float64   `json:"timestamp_sec"`
	
	// Detection coordinates (pixel space)
	PixelU        float64   `json:"pixel_u"`
	PixelV        float64   `json:"pixel_v"`
	
	// Detection metadata
	Confidence    float64   `json:"confidence"`
	ClassName     string    `json:"class_name"`
	
	// GPS data (if available)
	VehicleLat    *float64  `json:"vehicle_lat,omitempty"`
	VehicleLon    *float64  `json:"vehicle_lon,omitempty"`
	RecordingTimestamp *string `json:"recording_timestamp,omitempty"`
	
	// Computed geospatial data (optional, computed later in pipeline)
	ObjectLat     *float64  `json:"object_lat,omitempty"`
	ObjectLon     *float64  `json:"object_lon,omitempty"`
	Distance      *float64  `json:"distance,omitempty"`
	
	// ROI reference (for bandwidth optimization)
	ROIImagePath  *string   `json:"roi_image_path,omitempty"`
}

// ToJSON serializes the Detection to JSON
func (d *Detection) ToJSON() ([]byte, error) {
	return json.Marshal(d)
}

// FromJSON deserializes JSON to Detection
func FromJSON(data []byte) (*Detection, error) {
	var d Detection
	err := json.Unmarshal(data, &d)
	return &d, err
}

// CSVRow represents a raw CSV row from detection output
type CSVRow struct {
	FrameNumber  int     `csv:"frame_number"`
	TimestampSec float64 `csv:"timestamp_sec"`
	U            float64 `csv:"u"`
	V            float64 `csv:"v"`
	Confidence   float64 `csv:"confidence"`
	ClassName    string  `csv:"class_name"`
	VehicleLat   float64 `csv:"vehicle_lat"`
	VehicleLon   float64 `csv:"vehicle_lon"`
	RecordingTimestamp string `csv:"recording_timestamp"`
}
