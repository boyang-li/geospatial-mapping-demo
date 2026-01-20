package config

import (
	"fmt"
	"os"
)

// KafkaConfig holds Kafka connection configuration
type KafkaConfig struct {
	BootstrapServers string
	SecurityProtocol string
	SASLMechanism    string
	SASLUsername     string
	SASLPassword     string
	Topic            string
	CompressionType  string
	Acks             string
	MaxInFlight      int
	LingerMS         int
	BatchSize        int
}

// NewKafkaConfig creates a new Kafka configuration from environment variables
func NewKafkaConfig() *KafkaConfig {
	return &KafkaConfig{
		BootstrapServers: getEnv("KAFKA_BOOTSTRAP_SERVERS", "pkc-xxxxx.us-east-1.aws.confluent.cloud:9092"),
		SecurityProtocol: getEnv("KAFKA_SECURITY_PROTOCOL", "SASL_SSL"),
		SASLMechanism:    getEnv("KAFKA_SASL_MECHANISM", "PLAIN"),
		SASLUsername:     getEnv("KAFKA_SASL_USERNAME", ""),
		SASLPassword:     getEnv("KAFKA_SASL_PASSWORD", ""),
		Topic:            getEnv("KAFKA_TOPIC", "traffic-sign-detections"),
		CompressionType:  getEnv("KAFKA_COMPRESSION_TYPE", "snappy"),
		Acks:             getEnv("KAFKA_ACKS", "all"),
		MaxInFlight:      getEnvInt("KAFKA_MAX_IN_FLIGHT", 5),
		LingerMS:         getEnvInt("KAFKA_LINGER_MS", 10),
		BatchSize:        getEnvInt("KAFKA_BATCH_SIZE", 16384),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		var intValue int
		if _, err := fmt.Sscanf(value, "%d", &intValue); err == nil {
			return intValue
		}
	}
	return defaultValue
}
