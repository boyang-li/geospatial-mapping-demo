package ingestion

import (
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"os"
	"strconv"
	"time"

	"github.com/boyangli/sentinelmap-producer/models"
	"github.com/boyangli/sentinelmap-producer/producer"
)

// CSVReader handles streaming detection data from CSV files
type CSVReader struct {
	filePath  string
	vehicleID string
	sessionID string
}

// NewCSVReader creates a new CSV reader
func NewCSVReader(filePath, vehicleID, sessionID string) *CSVReader {
	return &CSVReader{
		filePath:  filePath,
		vehicleID: vehicleID,
		sessionID: sessionID,
	}
}

// StreamToChannel reads CSV and sends detections to a channel
func (cr *CSVReader) StreamToChannel(detectionChan chan<- *models.Detection) error {
	file, err := os.Open(cr.filePath)
	if err != nil {
		return fmt.Errorf("failed to open CSV file: %w", err)
	}
	defer file.Close()
	
	reader := csv.NewReader(file)
	
	// Read header
	header, err := reader.Read()
	if err != nil {
		return fmt.Errorf("failed to read CSV header: %w", err)
	}
	
	log.Printf("📄 CSV Header: %v", header)
	
	// Column indices
	colMap := make(map[string]int)
	for i, col := range header {
		colMap[col] = i
	}
	
	lineCount := 0
	startTime := time.Now()
	
	for {
		row, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("⚠️  Error reading CSV row: %v", err)
			continue
		}
		
		detection, err := cr.parseRow(row, colMap)
		if err != nil {
			log.Printf("⚠️  Error parsing row: %v", err)
			continue
		}
		
		detectionChan <- detection
		lineCount++
		
		if lineCount%10000 == 0 {
			elapsed := time.Since(startTime)
			rate := float64(lineCount) / elapsed.Seconds()
			log.Printf("📊 Streamed %d records (%.2f records/sec)", lineCount, rate)
		}
	}
	
	elapsed := time.Since(startTime)
	avgRate := float64(lineCount) / elapsed.Seconds()
	log.Printf("✅ CSV streaming complete - %d records in %v (avg: %.2f records/sec)", 
		lineCount, elapsed, avgRate)
	
	return nil
}

// parseRow converts a CSV row to a Detection struct
func (cr *CSVReader) parseRow(row []string, colMap map[string]int) (*models.Detection, error) {
	frameNumber, err := strconv.Atoi(row[colMap["frame_number"]])
	if err != nil {
		return nil, fmt.Errorf("invalid frame_number: %w", err)
	}
	
	timestampSec, err := strconv.ParseFloat(row[colMap["timestamp_sec"]], 64)
	if err != nil {
		return nil, fmt.Errorf("invalid timestamp_sec: %w", err)
	}
	
	// Support both u/v (centroid) and bbox_x1/y1/x2/y2 (bounding box)
	var u, v float64
	if uIdx, ok := colMap["u"]; ok && uIdx < len(row) {
		u, err = strconv.ParseFloat(row[uIdx], 64)
		if err != nil {
			return nil, fmt.Errorf("invalid u: %w", err)
		}
		v, err = strconv.ParseFloat(row[colMap["v"]], 64)
		if err != nil {
			return nil, fmt.Errorf("invalid v: %w", err)
		}
	} else if x1Idx, ok := colMap["bbox_x1"]; ok && x1Idx < len(row) {
		// Calculate centroid from bounding box
		x1, err := strconv.ParseFloat(row[colMap["bbox_x1"]], 64)
		if err != nil {
			return nil, fmt.Errorf("invalid bbox_x1: %w", err)
		}
		y1, err := strconv.ParseFloat(row[colMap["bbox_y1"]], 64)
		if err != nil {
			return nil, fmt.Errorf("invalid bbox_y1: %w", err)
		}
		x2, err := strconv.ParseFloat(row[colMap["bbox_x2"]], 64)
		if err != nil {
			return nil, fmt.Errorf("invalid bbox_x2: %w", err)
		}
		y2, err := strconv.ParseFloat(row[colMap["bbox_y2"]], 64)
		if err != nil {
			return nil, fmt.Errorf("invalid bbox_y2: %w", err)
		}
		u = (x1 + x2) / 2.0
		v = (y1 + y2) / 2.0
	} else {
		return nil, fmt.Errorf("missing pixel coordinates (expected u/v or bbox_x1/y1/x2/y2)")
	}
	
	confidence, err := strconv.ParseFloat(row[colMap["confidence"]], 64)
	if err != nil {
		return nil, fmt.Errorf("invalid confidence: %w", err)
	}
	
	className := row[colMap["class_name"]]
	
	// Parse video_name (if present)
	var videoName string
	if vnIdx, ok := colMap["video_name"]; ok && vnIdx < len(row) {
		videoName = row[vnIdx]
	}
	
	// Parse GPS fields (if present)
	var vehicleLat, vehicleLon *float64
	var recordingTimestamp *string
	if latIdx, ok := colMap["vehicle_lat"]; ok && latIdx < len(row) && row[latIdx] != "" {
		if lat, err := strconv.ParseFloat(row[latIdx], 64); err == nil {
			vehicleLat = &lat
		}
	}
	if lonIdx, ok := colMap["vehicle_lon"]; ok && lonIdx < len(row) && row[lonIdx] != "" {
		if lon, err := strconv.ParseFloat(row[lonIdx], 64); err == nil {
			vehicleLon = &lon
		}
	}
	if tsIdx, ok := colMap["recording_timestamp"]; ok && tsIdx < len(row) && row[tsIdx] != "" {
		ts := row[tsIdx]
		recordingTimestamp = &ts
	}
	
	return &models.Detection{
		DetectionID:  producer.GenerateDetectionID(),
		VehicleID:    cr.vehicleID,
		SessionID:    cr.sessionID,
		IngestedAt:   time.Now(),
		VideoName:    videoName,
		FrameNumber:  frameNumber,
		TimestampSec: timestampSec,
		PixelU:       u,
		PixelV:       v,
		Confidence:   confidence,
		ClassName:    className,
		VehicleLat:   vehicleLat,
		VehicleLon:   vehicleLon,
		RecordingTimestamp: recordingTimestamp,
	}, nil
}

// ReadAll reads entire CSV and returns all detections (use for smaller files)
func (cr *CSVReader) ReadAll() ([]*models.Detection, error) {
	file, err := os.Open(cr.filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open CSV file: %w", err)
	}
	defer file.Close()
	
	reader := csv.NewReader(file)
	
	// Read header
	header, err := reader.Read()
	if err != nil {
		return nil, fmt.Errorf("failed to read CSV header: %w", err)
	}
	
	// Column indices
	colMap := make(map[string]int)
	for i, col := range header {
		colMap[col] = i
	}
	
	var detections []*models.Detection
	
	for {
		row, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("⚠️  Error reading CSV row: %v", err)
			continue
		}
		
		detection, err := cr.parseRow(row, colMap)
		if err != nil {
			log.Printf("⚠️  Error parsing row: %v", err)
			continue
		}
		
		detections = append(detections, detection)
	}
	
	log.Printf("✅ Loaded %d detections from CSV", len(detections))
	return detections, nil
}
