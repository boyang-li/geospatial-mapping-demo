.PHONY: build run test clean deps dry-run

# Build the producer binary
build:
	@echo "🔨 Building producer..."
	go build -o bin/producer cmd/producer/main.go
	@echo "✅ Build complete: bin/producer"

# Build dry-run test (no Kafka required)
build-dryrun:
	@echo "🔨 Building dry-run test..."
	go build -o bin/test-dryrun cmd/test-dryrun/main.go
	@echo "✅ Build complete: bin/test-dryrun"

# Run dry-run test (NO KAFKA REQUIRED)
dry-run: build-dryrun
	@echo "🧪 Running dry-run test (no Kafka required)..."
	./bin/test-dryrun -csv ../../data/detections/detections.csv -limit 5

# Run dry-run test with more output
dry-run-full: build-dryrun
	@echo "🧪 Running dry-run test (showing all records)..."
	./bin/test-dryrun -csv ../../data/detections/detections.csv -limit 473

# Run in streaming mode
run-stream: build
	@echo "🌊 Running in streaming mode..."
	./bin/producer -

# Run tests with coverage
test-coverage:
	@echo "🧪 Running tests with coverage..."
	go test ./... -cover -coverprofile=coverage.out
	go tool cover -html=coverage.out -o coverage.html
	@echo "✅ Coverage report: coverage.html"csv ../local-mvp/traffic_signs.csv -workers 10

# Run in batch mode
run-batch: build
	@echo "📦 Running in batch mode..."
	./bin/producer -csv ../local-mvp/traffic_signs.csv -batch -workers 20

# Download dependencies
deps:
	@echo "📦 Downloading dependencies..."
	go mod download
	go mod tidy

# Run tests
test:
	@echo "🧪 Running tests..."
	go test ./... -v

# Clean build artifacts
clean:
	@echo "🧹 Cleaning..."
	rm -rf bin/
	go clean

# Format code
fmt:
	@echo "🎨 Formatting code..."
	go fmt ./...

# Install development tools
install-tools:
	@echo "🛠️  Installing development tools..."
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Lint code
lint:
	@echo "🔍 Linting code..."
	golangci-lint run

# Run with custom parameters
run-custom: build
	@echo "⚙️dry-run       - 🧪 Test without Kafka (RECOMMENDED FIRST STEP)"
	@echo "  test          - Run unit tests"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  build         - Build the producer binary"
	@echo "  build-dryrun  - Build dry-run test tool"
	@echo "  run-stream    - Run in streaming mode (requires Kafka)"
	@echo "  run-batch     - Run in batch mode (requires Kafka)"
	@echo "  deps          - Download Go dependencie
help:
	@echo "Available targets:"
	@echo "  build         - Build the producer binary"
	@echo "  run-stream    - Run in streaming mode (default)"
	@echo "  run-batch     - Run in batch mode"
	@echo "  deps          - Download Go dependencies"
	@echo "  test          - Run tests"
	@echo "  clean         - Remove build artifacts"
	@echo "  fmt           - Format Go code"
	@echo "  lint          - Run linter"
	@echo "  install-tools - Install development tools"
	@echo "  run-custom    - Run with custom arguments (use ARGS='...')"
