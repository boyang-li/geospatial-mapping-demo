package main

import (
	"flag"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/boyangli/sentinelmap-producer/config"
	"github.com/boyangli/sentinelmap-producer/ingestion"
	"github.com/boyangli/sentinelmap-producer/models"
	"github.com/boyangli/sentinelmap-producer/producer"
	"github.com/google/uuid"
	"github.com/joho/godotenv"
)

func main() {
	// Load .env file
	if err := godotenv.Load(); err != nil {
		log.Printf("⚠️  No .env file found, using environment variables")
	}
	
	// Command-line flags
	csvPath := flag.String("csv", "../../data/detections/detections.csv", "Path to detection CSV file")
	vehicleID := flag.String("vehicle", "vehicle-001", "Vehicle ID")
	sessionID := flag.String("session", "", "Session ID (auto-generated if empty)")
	workers := flag.Int("workers", 10, "Number of concurrent goroutines for streaming")
	batchMode := flag.Bool("batch", false, "Use batch mode instead of streaming")
	flag.Parse()
	
	// Generate session ID if not provided
	if *sessionID == "" {
		*sessionID = uuid.New().String()
	}
	
	log.Println("╔═══════════════════════════════════════════════════════════╗")
	log.Println("║   SentinelMap - High-Performance Kafka Producer          ║")
	log.Println("╚═══════════════════════════════════════════════════════════╝")
	log.Printf("Vehicle ID: %s", *vehicleID)
	log.Printf("Session ID: %s", *sessionID)
	log.Printf("CSV Path: %s", *csvPath)
	log.Printf("Workers: %d", *workers)
	log.Printf("Mode: %s", getMode(*batchMode))
	log.Println("───────────────────────────────────────────────────────────")
	
	// Initialize Kafka configuration
	kafkaConfig := config.NewKafkaConfig()
	
	// Create Kafka producer
	kafkaProducer, err := producer.NewKafkaProducer(kafkaConfig)
	if err != nil {
		log.Fatalf("❌ Failed to create Kafka producer: %v", err)
	}
	defer kafkaProducer.Close()
	
	// Setup graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	
	go func() {
		<-sigChan
		log.Println("\n🛑 Received shutdown signal")
		kafkaProducer.Close()
		os.Exit(0)
	}()
	
	// Create CSV reader
	csvReader := ingestion.NewCSVReader(*csvPath, *vehicleID, *sessionID)
	
	startTime := time.Now()
	
	if *batchMode {
		// Batch mode: Read all and send in parallel
		log.Println("📦 Running in BATCH mode...")
		detections, err := csvReader.ReadAll()
		if err != nil {
			log.Fatalf("❌ Failed to read CSV: %v", err)
		}
		
		if err := kafkaProducer.SendDetectionBatch(detections, *workers); err != nil {
			log.Printf("⚠️  Batch send errors: %v", err)
		}
		
		// Flush and wait (90s for large batches)
		kafkaProducer.Flush(90 * time.Second)
		
	} else {
		// Streaming mode: Continuous channel-based streaming
		log.Println("🌊 Running in STREAMING mode...")
		detectionChan := make(chan *models.Detection, 1000)
		
		// Start CSV reader in separate goroutine
		go func() {
			if err := csvReader.StreamToChannel(detectionChan); err != nil {
				log.Printf("❌ CSV streaming error: %v", err)
			}
			close(detectionChan)
		}()
		
		// Stream to Kafka
		if err := kafkaProducer.StreamFromChannel(detectionChan, *workers); err != nil {
			log.Printf("⚠️  Stream errors: %v", err)
		}
		
		// Flush remaining messages (90s for large batches)
		kafkaProducer.Flush(90 * time.Second)
	}
	
	elapsed := time.Since(startTime)
	
	// Final metrics
	log.Println("\n═══════════════════════════════════════════════════════════")
	log.Println("                    FINAL REPORT")
	log.Println("═══════════════════════════════════════════════════════════")
	kafkaProducer.LogMetrics()
	
	metrics := kafkaProducer.GetMetrics()
	tps := float64(metrics["messages_acked"]) / elapsed.Seconds()
	
	log.Printf("⏱️  Total Time: %v", elapsed)
	log.Printf("🚀 Throughput: %.2f messages/sec", tps)
	log.Printf("✅ Success Rate: %.2f%%", 
		float64(metrics["messages_acked"])/float64(metrics["messages_sent"])*100)
	log.Println("═══════════════════════════════════════════════════════════")
}

func getMode(batchMode bool) string {
	if batchMode {
		return "BATCH"
	}
	return "STREAMING"
}
