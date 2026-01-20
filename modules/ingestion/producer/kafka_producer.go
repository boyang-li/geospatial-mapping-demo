package producer

import (
	"context"
	"fmt"
	"log"
	"sync"
	"sync/atomic"
	"time"

	"github.com/boyangli/sentinelmap-producer/config"
	"github.com/boyangli/sentinelmap-producer/models"
	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"github.com/google/uuid"
)

// KafkaProducer manages high-throughput Kafka message production
type KafkaProducer struct {
	producer       *kafka.Producer
	config         *config.KafkaConfig
	deliveryChan   chan kafka.Event
	
	// Metrics
	messagesSent   atomic.Int64
	messagesAcked  atomic.Int64
	messagesFailed atomic.Int64
	
	// Thread safety
	wg             sync.WaitGroup
	ctx            context.Context
	cancel         context.CancelFunc
	
	// Retry configuration
	maxRetries     int
	baseBackoff    time.Duration
}

// NewKafkaProducer creates a new thread-safe Kafka producer
func NewKafkaProducer(cfg *config.KafkaConfig) (*KafkaProducer, error) {
	// Build producer configuration
	producerConfig := &kafka.ConfigMap{
		"bootstrap.servers": cfg.BootstrapServers,
		"security.protocol": cfg.SecurityProtocol,
		"sasl.mechanism":    cfg.SASLMechanism,
		"sasl.username":     cfg.SASLUsername,
		"sasl.password":     cfg.SASLPassword,
		
		// Performance tuning for high throughput
		"compression.type":          cfg.CompressionType,
		"acks":                      cfg.Acks,
		"max.in.flight.requests.per.connection": cfg.MaxInFlight,
		"linger.ms":                 cfg.LingerMS,
		"batch.size":                cfg.BatchSize,
		
		// Idempotence for exactly-once semantics
		"enable.idempotence": true,
		
		// Request timeout
		"request.timeout.ms": 30000,
		"delivery.timeout.ms": 120000,
	}
	
	p, err := kafka.NewProducer(producerConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to create producer: %w", err)
	}
	
	ctx, cancel := context.WithCancel(context.Background())
	
	kp := &KafkaProducer{
		producer:     p,
		config:       cfg,
		deliveryChan: make(chan kafka.Event, 10000),
		ctx:          ctx,
		cancel:       cancel,
		maxRetries:   5,
		baseBackoff:  100 * time.Millisecond,
	}
	
	// Start delivery report handler
	kp.wg.Add(1)
	go kp.handleDeliveryReports()
	
	log.Printf("✅ Kafka producer initialized - Topic: %s, Servers: %s", cfg.Topic, cfg.BootstrapServers)
	return kp, nil
}

// handleDeliveryReports processes delivery confirmations in a separate goroutine
func (kp *KafkaProducer) handleDeliveryReports() {
	defer kp.wg.Done()
	
	for {
		select {
		case <-kp.ctx.Done():
			log.Println("Delivery report handler shutting down")
			return
		case e := <-kp.deliveryChan:
			m, ok := e.(*kafka.Message)
			if !ok {
				continue
			}
			
			if m.TopicPartition.Error != nil {
				kp.messagesFailed.Add(1)
				log.Printf("❌ Delivery failed: %v (offset: %v)", m.TopicPartition.Error, m.TopicPartition.Offset)
			} else {
				kp.messagesAcked.Add(1)
				if kp.messagesAcked.Load()%1000 == 0 {
					log.Printf("✅ Message delivered [%d/%d] - Partition: %d, Offset: %v", 
						kp.messagesAcked.Load(), kp.messagesSent.Load(), 
						m.TopicPartition.Partition, m.TopicPartition.Offset)
				}
			}
		}
	}
}

// SendDetection sends a single detection to Kafka with retry logic
func (kp *KafkaProducer) SendDetection(detection *models.Detection) error {
	payload, err := detection.ToJSON()
	if err != nil {
		return fmt.Errorf("failed to serialize detection: %w", err)
	}
	
	message := &kafka.Message{
		TopicPartition: kafka.TopicPartition{
			Topic:     &kp.config.Topic,
			Partition: kafka.PartitionAny,
		},
		Key:   []byte(detection.DetectionID),
		Value: payload,
		Headers: []kafka.Header{
			{Key: "vehicle_id", Value: []byte(detection.VehicleID)},
			{Key: "session_id", Value: []byte(detection.SessionID)},
			{Key: "class_name", Value: []byte(detection.ClassName)},
		},
	}
	
	// Exponential backoff retry
	var lastErr error
	for attempt := 0; attempt <= kp.maxRetries; attempt++ {
		if attempt > 0 {
			backoff := kp.baseBackoff * time.Duration(1<<uint(attempt-1))
			log.Printf("🔄 Retry attempt %d/%d after %v", attempt, kp.maxRetries, backoff)
			time.Sleep(backoff)
		}
		
		err := kp.producer.Produce(message, kp.deliveryChan)
		if err == nil {
			kp.messagesSent.Add(1)
			return nil
		}
		
		lastErr = err
		
		// Check if it's a retriable error
		if kafkaErr, ok := err.(kafka.Error); ok {
			if !kafkaErr.IsRetriable() {
				return fmt.Errorf("non-retriable error: %w", err)
			}
		}
	}
	
	kp.messagesFailed.Add(1)
	return fmt.Errorf("failed after %d retries: %w", kp.maxRetries, lastErr)
}

// SendDetectionBatch sends multiple detections concurrently using goroutines
func (kp *KafkaProducer) SendDetectionBatch(detections []*models.Detection, workerCount int) error {
	if len(detections) == 0 {
		return nil
	}
	
	log.Printf("📤 Sending batch of %d detections with %d workers", len(detections), workerCount)
	
	// Create job channel
	jobs := make(chan *models.Detection, len(detections))
	errors := make(chan error, len(detections))
	
	// Create worker pool
	var workerWg sync.WaitGroup
	for i := 0; i < workerCount; i++ {
		workerWg.Add(1)
		go func(workerID int) {
			defer workerWg.Done()
			for detection := range jobs {
				if err := kp.SendDetection(detection); err != nil {
					errors <- fmt.Errorf("worker %d failed: %w", workerID, err)
				}
			}
		}(i)
	}
	
	// Queue jobs
	for _, detection := range detections {
		jobs <- detection
	}
	close(jobs)
	
	// Wait for workers to complete
	workerWg.Wait()
	close(errors)
	
	// Collect errors
	var errs []error
	for err := range errors {
		errs = append(errs, err)
	}
	
	if len(errs) > 0 {
		return fmt.Errorf("batch send completed with %d errors (first error: %v)", len(errs), errs[0])
	}
	
	log.Printf("✅ Batch send complete - %d messages queued", len(detections))
	return nil
}

// StreamFromChannel continuously reads detections from a channel and sends to Kafka
func (kp *KafkaProducer) StreamFromChannel(detectionChan <-chan *models.Detection, workerCount int) error {
	log.Printf("🚀 Starting stream ingestion with %d workers", workerCount)
	
	var streamWg sync.WaitGroup
	errors := make(chan error, workerCount)
	
	// Spawn worker goroutines
	for i := 0; i < workerCount; i++ {
		streamWg.Add(1)
		go func(workerID int) {
			defer streamWg.Done()
			for {
				select {
				case <-kp.ctx.Done():
					log.Printf("Worker %d shutting down", workerID)
					return
				case detection, ok := <-detectionChan:
					if !ok {
						log.Printf("Worker %d: channel closed", workerID)
						return
					}
					
					if err := kp.SendDetection(detection); err != nil {
						errors <- fmt.Errorf("worker %d: %w", workerID, err)
					}
				}
			}
		}(i)
	}
	
	// Wait for all workers
	streamWg.Wait()
	close(errors)
	
	// Log any errors
	errorCount := 0
	for err := range errors {
		log.Printf("Stream error: %v", err)
		errorCount++
	}
	
	if errorCount > 0 {
		return fmt.Errorf("stream completed with %d errors", errorCount)
	}
	
	return nil
}

// Flush waits for all pending messages to be delivered
func (kp *KafkaProducer) Flush(timeout time.Duration) {
	log.Printf("🔄 Flushing producer (timeout: %v)...", timeout)
	remaining := kp.producer.Flush(int(timeout.Milliseconds()))
	if remaining > 0 {
		log.Printf("⚠️  %d messages still in queue after flush timeout", remaining)
	} else {
		log.Println("✅ All messages flushed successfully")
	}
}

// GetMetrics returns current producer metrics
func (kp *KafkaProducer) GetMetrics() map[string]int64 {
	return map[string]int64{
		"messages_sent":   kp.messagesSent.Load(),
		"messages_acked":  kp.messagesAcked.Load(),
		"messages_failed": kp.messagesFailed.Load(),
		"messages_pending": kp.messagesSent.Load() - kp.messagesAcked.Load() - kp.messagesFailed.Load(),
	}
}

// LogMetrics prints current metrics
func (kp *KafkaProducer) LogMetrics() {
	metrics := kp.GetMetrics()
	log.Printf("📊 Metrics - Sent: %d | Acked: %d | Failed: %d | Pending: %d",
		metrics["messages_sent"],
		metrics["messages_acked"],
		metrics["messages_failed"],
		metrics["messages_pending"])
}

// Close gracefully shuts down the producer
func (kp *KafkaProducer) Close() {
	log.Println("🛑 Shutting down Kafka producer...")
	
	// Cancel context to stop workers
	kp.cancel()
	
	// Flush remaining messages
	kp.Flush(30 * time.Second)
	
	// Wait for delivery reports
	kp.wg.Wait()
	
	// Close producer
	kp.producer.Close()
	
	// Final metrics
	kp.LogMetrics()
	log.Println("✅ Kafka producer closed")
}

// GenerateDetectionID creates a unique detection ID
func GenerateDetectionID() string {
	return uuid.New().String()
}
