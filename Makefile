# Voice AI Agent - Development Makefile
# Automates common development tasks for the monorepo

.PHONY: help setup proto build dev test clean install-deps docker-up docker-down db-migrate db-reset logs

# Default shell
SHELL := /bin/bash

# Colors for output
COLOR_RESET   = \033[0m
COLOR_INFO    = \033[36m
COLOR_SUCCESS = \033[32m
COLOR_WARNING = \033[33m
COLOR_ERROR   = \033[31m

help:
	@echo "$(COLOR_INFO)=================================="
	@echo "Voice AI Agent - Development Commands"
	@echo "==================================$(COLOR_RESET)"
	@echo ""
	@echo "  $(COLOR_SUCCESS)make setup$(COLOR_RESET)          - Initialize project and dependencies"
	@echo "  $(COLOR_SUCCESS)make proto$(COLOR_RESET)          - Generate gRPC code from .proto files"
	@echo "  $(COLOR_SUCCESS)make build$(COLOR_RESET)          - Build all services"
	@echo "  $(COLOR_SUCCESS)make dev$(COLOR_RESET)            - Start development environment"
	@echo "  $(COLOR_SUCCESS)make test$(COLOR_RESET)           - Run all tests"
	@echo "  $(COLOR_SUCCESS)make clean$(COLOR_RESET)          - Clean build artifacts"
	@echo ""
	@echo "  $(COLOR_INFO)Docker:$(COLOR_RESET)"
	@echo "  $(COLOR_SUCCESS)make docker-up$(COLOR_RESET)      - Start Docker containers"
	@echo "  $(COLOR_SUCCESS)make docker-down$(COLOR_RESET)    - Stop Docker containers"
	@echo "  $(COLOR_SUCCESS)make logs$(COLOR_RESET)           - Show Docker logs"
	@echo ""
	@echo "  $(COLOR_INFO)Database:$(COLOR_RESET)"
	@echo "  $(COLOR_SUCCESS)make db-migrate$(COLOR_RESET)     - Run database migrations"
	@echo "  $(COLOR_SUCCESS)make db-reset$(COLOR_RESET)       - Reset database (WARNING: deletes data)"
	@echo ""
	@echo "  $(COLOR_INFO)Dependencies:$(COLOR_RESET)"
	@echo "  $(COLOR_SUCCESS)make install-deps$(COLOR_RESET)   - Install all dependencies"
	@echo ""

# ============================================================================
# SETUP
# ============================================================================

setup: check-env
	@echo "$(COLOR_INFO)Setting up Voice AI Agent...$(COLOR_RESET)"
	@if [ ! -f .env ]; then \
		echo "$(COLOR_WARNING)Creating .env from .env.example$(COLOR_RESET)"; \
		cp .env.example .env; \
		echo "$(COLOR_WARNING)⚠️  Please edit .env with your configuration$(COLOR_RESET)"; \
	fi
	@echo "$(COLOR_INFO)Starting infrastructure (PostgreSQL, Redis)...$(COLOR_RESET)"
	docker-compose -f infra/docker-compose.yml up -d postgres redis
	@echo "$(COLOR_INFO)Waiting for PostgreSQL to be ready...$(COLOR_RESET)"
	@timeout=30; \
	while ! docker exec voice-agent-postgres pg_isready -U agent -d voice_agent > /dev/null 2>&1; do \
		timeout=$$((timeout - 1)); \
		if [ $$timeout -le 0 ]; then \
			echo "$(COLOR_ERROR)PostgreSQL failed to start$(COLOR_RESET)"; \
			exit 1; \
		fi; \
		sleep 1; \
	done
	@echo "$(COLOR_SUCCESS)✓ PostgreSQL is ready$(COLOR_RESET)"
	@echo "$(COLOR_INFO)Waiting for Redis to be ready...$(COLOR_RESET)"
	@timeout=30; \
	while ! docker exec voice-agent-redis redis-cli ping > /dev/null 2>&1; do \
		timeout=$$((timeout - 1)); \
		if [ $$timeout -le 0 ]; then \
			echo "$(COLOR_ERROR)Redis failed to start$(COLOR_RESET)"; \
			exit 1; \
		fi; \
		sleep 1; \
	done
	@echo "$(COLOR_SUCCESS)✓ Redis is ready$(COLOR_RESET)"
	@echo "$(COLOR_INFO)Generating gRPC protocol buffers...$(COLOR_RESET)"
	$(MAKE) proto
	@echo ""
	@echo "$(COLOR_SUCCESS)=================================="
	@echo "✓ Setup complete!"
	@echo "==================================$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_INFO)Next steps:$(COLOR_RESET)"
	@echo "  1. Edit .env with your configuration"
	@echo "  2. Run 'make dev' to start development environment"
	@echo "  3. Run 'make test' to verify installation"
	@echo ""

check-env:
	@command -v docker >/dev/null 2>&1 || { echo "$(COLOR_ERROR)Error: docker is not installed$(COLOR_RESET)"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "$(COLOR_ERROR)Error: docker-compose is not installed$(COLOR_RESET)"; exit 1; }
	@command -v python >/dev/null 2>&1 || { echo "$(COLOR_ERROR)Error: python is not installed$(COLOR_RESET)"; exit 1; }
	@python_version=$$(python --version 2>&1 | sed 's/Python //;s/\..*//' ); \
	if [ "$$python_version" -lt 3 ]; then \
		echo "$(COLOR_ERROR)Error: Python 3.11+ is required$(COLOR_RESET)"; \
		exit 1; \
	fi
	@echo "$(COLOR_SUCCESS)✓ Prerequisites check passed$(COLOR_RESET)"

# ============================================================================
# PROTOCOL BUFFERS
# ============================================================================

proto:
	@echo "$(COLOR_INFO)Generating gRPC protocol buffers...$(COLOR_RESET)"
	@if command -v python >/dev/null 2>&1; then \
		python -m pip install --quiet grpcio-tools 2>/dev/null || true; \
		cd shared/proto && chmod +x build.sh && bash build.sh; \
		echo "$(COLOR_SUCCESS)✓ Protocol buffers generated$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_ERROR)Python not found$(COLOR_RESET)"; \
		exit 1; \
	fi

# ============================================================================
# BUILD
# ============================================================================

build: proto
	@echo "$(COLOR_INFO)Building all services...$(COLOR_RESET)"
	@echo "$(COLOR_INFO)Building Python services...$(COLOR_RESET)"
	# Phase 2+: Add Python service builds
	@echo "$(COLOR_WARNING)  Python services not yet implemented (Phase 2+)$(COLOR_RESET)"
	@echo "$(COLOR_INFO)Building Rust services...$(COLOR_RESET)"
	# Phase 4+: Add Rust service builds
	@echo "$(COLOR_WARNING)  Rust services not yet implemented (Phase 4+)$(COLOR_RESET)"
	@echo "$(COLOR_SUCCESS)✓ Build complete$(COLOR_RESET)"

# ============================================================================
# DEVELOPMENT
# ============================================================================

dev: docker-up
	@echo "$(COLOR_SUCCESS)Development environment is running$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_INFO)Available services:$(COLOR_RESET)"
	@echo "  PostgreSQL: localhost:5432"
	@echo "  Redis:      localhost:6379"
	@echo ""
	@echo "$(COLOR_INFO)To view logs:$(COLOR_RESET) make logs"
	@echo "$(COLOR_INFO)To stop:$(COLOR_RESET)      make docker-down"
	@echo ""

docker-up:
	@echo "$(COLOR_INFO)Starting Docker services...$(COLOR_RESET)"
	docker-compose -f infra/docker-compose.yml up -d
	@echo "$(COLOR_SUCCESS)✓ Services started$(COLOR_RESET)"

docker-down:
	@echo "$(COLOR_INFO)Stopping Docker services...$(COLOR_RESET)"
	docker-compose -f infra/docker-compose.yml down
	@echo "$(COLOR_SUCCESS)✓ Services stopped$(COLOR_RESET)"

logs:
	docker-compose -f infra/docker-compose.yml logs -f

# ============================================================================
# DATABASE
# ============================================================================

db-migrate:
	@echo "$(COLOR_INFO)Running database migrations...$(COLOR_RESET)"
	@echo "$(COLOR_WARNING)Migration system not yet implemented (Phase 2)$(COLOR_RESET)"

db-reset:
	@echo "$(COLOR_WARNING)⚠️  This will DELETE ALL DATA in the database!$(COLOR_RESET)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(COLOR_INFO)Resetting database...$(COLOR_RESET)"; \
		docker-compose -f infra/docker-compose.yml down -v; \
		docker-compose -f infra/docker-compose.yml up -d postgres redis; \
		sleep 5; \
		echo "$(COLOR_SUCCESS)✓ Database reset complete$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_INFO)Cancelled$(COLOR_RESET)"; \
	fi

# ============================================================================
# TESTING
# ============================================================================

test:
	@echo "$(COLOR_INFO)Running tests...$(COLOR_RESET)"
	@if [ -d "tests" ]; then \
		if command -v pytest >/dev/null 2>&1; then \
			pytest tests/ -v --tb=short; \
		else \
			echo "$(COLOR_WARNING)pytest not installed. Install with: pip install pytest$(COLOR_RESET)"; \
			exit 1; \
		fi; \
	else \
		echo "$(COLOR_WARNING)No tests found (tests will be added in Phase 2+)$(COLOR_RESET)"; \
	fi

test-unit:
	@echo "$(COLOR_INFO)Running unit tests...$(COLOR_RESET)"
	pytest tests/unit -v

test-integration:
	@echo "$(COLOR_INFO)Running integration tests...$(COLOR_RESET)"
	pytest tests/integration -v

test-e2e:
	@echo "$(COLOR_INFO)Running end-to-end tests...$(COLOR_RESET)"
	pytest tests/e2e -v

test-coverage:
	@echo "$(COLOR_INFO)Running tests with coverage...$(COLOR_RESET)"
	pytest tests/ --cov=services --cov-report=html --cov-report=term
	@echo "$(COLOR_INFO)Coverage report generated in htmlcov/$(COLOR_RESET)"

# ============================================================================
# DEPENDENCIES
# ============================================================================

install-deps:
	@echo "$(COLOR_INFO)Installing Python dependencies...$(COLOR_RESET)"
	pip install grpcio-tools pytest pytest-cov pytest-asyncio
	@echo "$(COLOR_SUCCESS)✓ Python dependencies installed$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_INFO)Checking Rust installation...$(COLOR_RESET)"
	@if command -v cargo >/dev/null 2>&1; then \
		echo "$(COLOR_SUCCESS)✓ Rust is installed: $$(rustc --version)$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_WARNING)Rust not found. Install from: https://rustup.rs/$(COLOR_RESET)"; \
	fi

# ============================================================================
# CLEANUP
# ============================================================================

clean:
	@echo "$(COLOR_INFO)Cleaning build artifacts...$(COLOR_RESET)"
	docker-compose -f infra/docker-compose.yml down -v
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "target" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage 2>/dev/null || true
	@echo "$(COLOR_SUCCESS)✓ Cleanup complete$(COLOR_RESET)"

# ============================================================================
# UTILITIES
# ============================================================================

status:
	@echo "$(COLOR_INFO)Service Status:$(COLOR_RESET)"
	@docker-compose -f infra/docker-compose.yml ps

shell-db:
	@echo "$(COLOR_INFO)Opening PostgreSQL shell...$(COLOR_RESET)"
	docker exec -it voice-agent-postgres psql -U agent -d voice_agent

shell-redis:
	@echo "$(COLOR_INFO)Opening Redis CLI...$(COLOR_RESET)"
	docker exec -it voice-agent-redis redis-cli

fmt:
	@echo "$(COLOR_INFO)Formatting Python code...$(COLOR_RESET)"
	@if command -v black >/dev/null 2>&1; then \
		black services/ shared/ tests/ --line-length 100; \
		echo "$(COLOR_SUCCESS)✓ Python code formatted$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_WARNING)black not installed. Install with: pip install black$(COLOR_RESET)"; \
	fi

lint:
	@echo "$(COLOR_INFO)Linting Python code...$(COLOR_RESET)"
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check services/ shared/ tests/; \
		echo "$(COLOR_SUCCESS)✓ Linting complete$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_WARNING)ruff not installed. Install with: pip install ruff$(COLOR_RESET)"; \
	fi
