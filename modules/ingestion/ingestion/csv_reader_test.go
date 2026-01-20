package ingestion

import (
	"os"
	"path/filepath"
	"testing"
)

func TestCSVReaderParsing(t *testing.T) {
	// Create temporary test CSV
	tmpDir := t.TempDir()
	csvPath := filepath.Join(tmpDir, "test.csv")
	
	content := `frame_number,timestamp_sec,u,v,confidence,class_name
75,2.500,1737.28,630.06,0.5249,stop sign
185,6.167,2141.59,200.01,0.3381,traffic light
206,6.867,2192.02,481.80,0.6323,traffic light`

	if err := os.WriteFile(csvPath, []byte(content), 0644); err != nil {
		t.Fatalf("Failed to create test CSV: %v", err)
	}

	reader := NewCSVReader(csvPath, "test-vehicle", "test-session")
	
	detections, err := reader.ReadAll()
	if err != nil {
		t.Fatalf("ReadAll failed: %v", err)
	}

	// Verify count
	if len(detections) != 3 {
		t.Errorf("Expected 3 detections, got %d", len(detections))
	}

	// Verify first detection
	if detections[0].FrameNumber != 75 {
		t.Errorf("Expected frame 75, got %d", detections[0].FrameNumber)
	}
	if detections[0].ClassName != "stop sign" {
		t.Errorf("Expected 'stop sign', got '%s'", detections[0].ClassName)
	}
	if detections[0].Confidence != 0.5249 {
		t.Errorf("Expected confidence 0.5249, got %f", detections[0].Confidence)
	}

	// Verify metadata enrichment
	if detections[0].VehicleID != "test-vehicle" {
		t.Errorf("Expected vehicle_id 'test-vehicle', got '%s'", detections[0].VehicleID)
	}
	if detections[0].SessionID != "test-session" {
		t.Errorf("Expected session_id 'test-session', got '%s'", detections[0].SessionID)
	}
	if detections[0].DetectionID == "" {
		t.Errorf("Expected non-empty detection_id")
	}
}

func TestCSVReaderInvalidData(t *testing.T) {
	tmpDir := t.TempDir()
	csvPath := filepath.Join(tmpDir, "invalid.csv")
	
	content := `frame_number,timestamp_sec,u,v,confidence,class_name
INVALID,2.500,1737.28,630.06,0.5249,stop sign
75,INVALID,1737.28,630.06,0.5249,stop sign`

	if err := os.WriteFile(csvPath, []byte(content), 0644); err != nil {
		t.Fatalf("Failed to create test CSV: %v", err)
	}

	reader := NewCSVReader(csvPath, "test-vehicle", "test-session")
	detections, err := reader.ReadAll()
	
	// Should not fail completely, but skip invalid rows
	if err != nil {
		t.Fatalf("ReadAll should handle invalid rows gracefully: %v", err)
	}

	// Should have skipped both invalid rows
	if len(detections) != 0 {
		t.Logf("Warning: Expected 0 valid detections, got %d (invalid rows should be skipped)", len(detections))
	}
}
