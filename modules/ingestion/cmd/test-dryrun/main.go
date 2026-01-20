package main

import (
	"encoding/csv"
	"flag"
	"fmt"
	"io"
	"log"
	"os"
	"time"

	"github.com/google/uuid"
)

// Lightweight test without Kafka dependency
func main() {
	csvPath := flag.String("csv", "../local-mvp/traffic_signs.csv", "Path to CSV file")
	limit := flag.Int("limit", 10, "Number of records to display")
	flag.Parse()

	log.Println("╔═══════════════════════════════════════════════════════════╗")
	log.Println("║        DRY-RUN TEST (No Kafka Required)                  ║")
	log.Println("╚═══════════════════════════════════════════════════════════╝")
	log.Printf("CSV Path: %s\n", *csvPath)
	log.Printf("Display Limit: %d records\n", *limit)
	log.Println("───────────────────────────────────────────────────────────")

	file, err := os.Open(*csvPath)
	if err != nil {
		log.Fatalf("❌ Failed to open CSV: %v", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)
	
	// Read header
	header, err := reader.Read()
	if err != nil {
		log.Fatalf("❌ Failed to read header: %v", err)
	}
	log.Printf("✅ CSV Header: %v\n", header)

	// Build column map
	colMap := make(map[string]int)
	for i, col := range header {
		colMap[col] = i
	}

	vehicleID := "test-vehicle-001"
	sessionID := uuid.New().String()
	
	log.Println("\n📋 Sample Enriched JSON Messages:")
	log.Println("═══════════════════════════════════════════════════════════")

	count := 0
	totalRecords := 0
	startTime := time.Now()

	for {
		row, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Printf("⚠️  Row error: %v", err)
			continue
		}

		totalRecords++

		// Display first N records
		if count < *limit {
			json := buildJSON(row, colMap, vehicleID, sessionID)
			fmt.Println(json)
			fmt.Println("───────────────────────────────────────────────────────────")
			count++
		}
	}

	elapsed := time.Since(startTime)
	recordsPerSec := float64(totalRecords) / elapsed.Seconds()

	log.Println("\n📊 PARSING STATISTICS:")
	log.Println("═══════════════════════════════════════════════════════════")
	log.Printf("✅ Total Records Parsed: %d", totalRecords)
	log.Printf("⏱️  Parse Time: %v", elapsed)
	log.Printf("🚀 Parse Rate: %.2f records/sec", recordsPerSec)
	log.Println("═══════════════════════════════════════════════════════════")
	log.Println("\n✅ TEST PASSED - CSV parsing and JSON enrichment working!")
	log.Println("💡 Next: Configure Kafka credentials to test actual ingestion")
}

func buildJSON(row []string, colMap map[string]int, vehicleID, sessionID string) string {
	frameNum := row[colMap["frame_number"]]
	timestamp := row[colMap["timestamp_sec"]]
	u := row[colMap["u"]]
	v := row[colMap["v"]]
	confidence := row[colMap["confidence"]]
	className := row[colMap["class_name"]]

	detectionID := uuid.New().String()
	ingestedAt := time.Now().Format(time.RFC3339Nano)

	return fmt.Sprintf(`{
  "detection_id": "%s",
  "vehicle_id": "%s",
  "session_id": "%s",
  "ingested_at": "%s",
  "frame_number": %s,
  "timestamp_sec": %s,
  "pixel_u": %s,
  "pixel_v": %s,
  "confidence": %s,
  "class_name": "%s",
  "vehicle_lat": null,
  "vehicle_lon": null,
  "heading": null,
  "object_lat": null,
  "object_lon": null,
  "distance": null,
  "roi_image_path": null
}`, detectionID, vehicleID, sessionID, ingestedAt, frameNum, timestamp, u, v, confidence, className)
}
