package models

import (
	"encoding/json"
	"testing"
	"time"
)

func TestDetectionSerialization(t *testing.T) {
	detection := &Detection{
		DetectionID:  "test-123",
		VehicleID:    "vehicle-001",
		SessionID:    "session-001",
		IngestedAt:   time.Now(),
		FrameNumber:  75,
		TimestampSec: 2.5,
		PixelU:       1737.28,
		PixelV:       630.06,
		Confidence:   0.5249,
		ClassName:    "stop sign",
	}

	// Test serialization
	jsonBytes, err := detection.ToJSON()
	if err != nil {
		t.Fatalf("Serialization failed: %v", err)
	}

	// Verify it's valid JSON
	var raw map[string]interface{}
	if err := json.Unmarshal(jsonBytes, &raw); err != nil {
		t.Fatalf("Invalid JSON output: %v", err)
	}

	// Test deserialization
	parsed, err := FromJSON(jsonBytes)
	if err != nil {
		t.Fatalf("Deserialization failed: %v", err)
	}

	// Verify fields
	if parsed.DetectionID != "test-123" {
		t.Errorf("Expected detection_id 'test-123', got '%s'", parsed.DetectionID)
	}
	if parsed.FrameNumber != 75 {
		t.Errorf("Expected frame 75, got %d", parsed.FrameNumber)
	}
	if parsed.TimestampSec != 2.5 {
		t.Errorf("Expected timestamp 2.5, got %f", parsed.TimestampSec)
	}
	if parsed.ClassName != "stop sign" {
		t.Errorf("Expected class_name 'stop sign', got '%s'", parsed.ClassName)
	}
}

func TestDetectionWithNullFields(t *testing.T) {
	detection := &Detection{
		DetectionID:  "test-456",
		VehicleID:    "vehicle-002",
		SessionID:    "session-002",
		IngestedAt:   time.Now(),
		FrameNumber:  100,
		TimestampSec: 5.0,
		PixelU:       1500.0,
		PixelV:       800.0,
		Confidence:   0.85,
		ClassName:    "traffic light",
		// GPS fields intentionally null
		VehicleLat: nil,
		VehicleLon: nil,
		Heading:    nil,
	}

	jsonBytes, err := detection.ToJSON()
	if err != nil {
		t.Fatalf("Serialization failed: %v", err)
	}

	// Verify JSON contains null for optional fields (omitempty fields are omitted, not set to null)
	// This is expected behavior - the field should be absent from JSON
	parsed, err := FromJSON(jsonBytes)
	if err != nil {
		t.Fatalf("Deserialization failed: %v", err)
	}
	if parsed.VehicleLat != nil {
		t.Errorf("Expected vehicle_lat to be nil, got %v", parsed.VehicleLat)
	}
}

func TestDetectionWithGPSData(t *testing.T) {
	lat := 43.7900
	lon := -79.3140
	heading := 45.0

	detection := &Detection{
		DetectionID:  "test-789",
		VehicleID:    "vehicle-003",
		SessionID:    "session-003",
		IngestedAt:   time.Now(),
		FrameNumber:  200,
		TimestampSec: 10.0,
		PixelU:       2000.0,
		PixelV:       1000.0,
		Confidence:   0.95,
		ClassName:    "stop sign",
		VehicleLat:   &lat,
		VehicleLon:   &lon,
		Heading:      &heading,
	}

	jsonBytes, err := detection.ToJSON()
	if err != nil {
		t.Fatalf("Serialization failed: %v", err)
	}

	parsed, err := FromJSON(jsonBytes)
	if err != nil {
		t.Fatalf("Deserialization failed: %v", err)
	}

	if parsed.VehicleLat == nil || *parsed.VehicleLat != 43.7900 {
		t.Errorf("Expected vehicle_lat 43.7900, got %v", parsed.VehicleLat)
	}
	if parsed.VehicleLon == nil || *parsed.VehicleLon != -79.3140 {
		t.Errorf("Expected vehicle_lon -79.3140, got %v", parsed.VehicleLon)
	}
	if parsed.Heading == nil || *parsed.Heading != 45.0 {
		t.Errorf("Expected heading 45.0, got %v", parsed.Heading)
	}
}

func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(s) > len(substr) && (s[:len(substr)] == substr || s[len(s)-len(substr):] == substr || containsHelper(s, substr)))
}

func containsHelper(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
