<div align="center">

# Fintech Portfolio Auto-Balancer

**Portfolio Management System with Automatic Rebalancing and Atomic Operations**

[Python] [![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

</div>

---

## About This Project

This is a **fintech challenge demonstration** originally created as a solution to a traditional technical interview challenge common in many fintech companies. It has been made public to showcase production-grade software engineering practices applied to financial portfolio management.

The project demonstrates a portfolio management system that automatically rebalances investment portfolios based on stock price changes, with enterprise-grade features including:

- **Automatic rebalancing** with configurable thresholds
- **Atomic batch operations** with automatic rollback
- **Lock-based concurrency control** to prevent race conditions
- **Financial precision** using Python's `Decimal` type
- **Comprehensive test suite** covering edge cases and failure scenarios

> **Note**: This is a demonstration project showcasing software engineering practices for fintech applications. It is not financial advice or a real production trading system.

---

## AI Usage Documentation

The development process of this project involved the use of Large Language Models (LLMs) as coding assistants. Detailed documentation of how AI tools were used throughout development can be found in [`docs/ai-usage-statement.md`](docs/ai-usage-statement.md).

---

## Key Features (Business-Critical Functionality)

### Locking Mechanism for Concurrent Rebalancing Prevention

The system implements **portfolio-level locking** to prevent race conditions during critical operations:

- **TTL-based Locks**: Configurable time-to-live (default: 6 hours) prevents deadlocks
- **Automatic Cleanup**: Locks expire automatically if the process fails
- **Concurrent Operation Prevention**: Ensures only one rebalance occurs at a time
- **Expired Lock Detection**: Allows portfolio recovery after failures

**Why this matters**: In production where multiple events can trigger concurrent rebalances, this mechanism protects user portfolio data integrity.

### Automatic Rollback for Batch Operations

All broker operations are grouped into **atomic transactions** with automatic rollback:

- **Atomic Operations**: All buy/sell operations in a rebalance execute as a unit
- **State Tracking**: Each operation has tracked states
- **Automatic Compensation**: If any operation fails, successful ones automatically reverse
- **Configurable Retries**: Up to 3 retries with configurable delay for rollback operations
- **Complete Logging**: Full operation trace for audit purposes

**Why this matters**: In production trading systems, this means users are **never** left in an inconsistent state. If some operations in a batch fail, successful ones are automatically reversed.

If rollback fails, the `set_stale` method can send alerts (e.g., via Slack) for rapid resolution. Telemetry can be incorporated to measure failure rates.

### Intelligent Automatic Rebalancing

The system detects and corrects deviations automatically:

- **Configurable Threshold**: Only rebalances when deviation exceeds the configured threshold
- **Precise Calculation**: Uses decimal arithmetic to avoid financial rounding errors
- **Asynchronous Execution**: Buy/sell operations execute in parallel to optimize network latency
- **Rule Validation**: Verifies allocation sums equal exactly 100%

**Why this matters**: User portfolios remain aligned with their investment strategy automatically.

### Financial Precision with Decimal

Systematic use of `Decimal` to avoid floating-point errors:

- **Money**: 2 decimals ($10.00)
- **Quantity**: 9 decimals (fractional shares: 1.234567890) - Based on [Alpaca's documentation](https://docs.alpaca.markets/docs/fractional-trading)
- **Percentages**: 4 decimals (20.0000%)

**Why this matters**: A $0.01 error multiplied by millions of users becomes a significant loss.

---

## Architecture

### Core Modules

```
src/
├── broker/              # Financial intermediary with atomic operations
│   ├── broker_interface.py    # Abstract broker protocol
│   ├── broker.py               # BanChileBroker with automatic rollback
│   ├── broker_dtos.py          # Operation data models
│   └── errors.py               # Broker-specific exceptions
│
├── portfolio/           # Portfolio management with rebalancing
│   ├── portfolio.py            # Portfolio with locking and rebalancing
│   ├── portfolio_dtos.py       # Configuration and validations
│   ├── portfolio_register.py   # Portfolio registry by symbol
│   └── errors.py               # Portfolio-specific exceptions
│
├── stock/               # Stock entities
│   ├── stock.py                # Stock with symbol/price validation
│   └── errors.py               # Stock-specific exceptions
│
├── config/              # Centralized configuration
│   └── config.py               # Immutable system settings
│
└── utils/               # Shared utilities
    ├── decimal_utils.py        # Decimal quantization
    └── fake_market.py          # NASDAQ market simulator
```

### Rebalancing Flow

```
┌─────────────────┐
│ Price changes   │
│ (META: $400)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ Registry detects portfolios │
│ affected by symbol          │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Calculate deviation vs target   │
│ Exceeds threshold (5%)?         │
└────────┬────────────────────────┘
         │ NO
         ├─────────────────────► (End - no rebalance)
         │ YES
         ▼
┌─────────────────────────────┐
│ Acquire rebalance lock      │
│ Available?                  │
└────────┬────────────────────┘
         │ NO
         ├─────────────────────► (End - rebalance in progress)
         │ YES
         ▼
┌──────────────────────────────────────┐
│ Calculate required operations        │
│ - Buy stocks with deficit            │
│ - Sell stocks with surplus           │
└────────┬─────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Execute batch operations            │
│ (asyncio.gather in parallel)        │
└────────┬─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ All successful?             │
└────────┬────────────────────┘
         │ YES
         ├─────────────────────► Update quantities ✓
         │
         │ NO
         ▼
┌─────────────────────────────────┐
│ 🔴 Automatic Rollback           │
│ - Execute reverse operations    │
│ - Mark portfolio as STALE       │
│ - Requires manual intervention  │
└─────────────────────────────────┘
```

---

## Installation

### Option 1: With uv

[uv](https://github.com/astral-sh/uv) is an ultra-fast Python package manager.

```bash
# Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <repo-url>
cd fintech-portfolio-rebalancing

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows
```

### Option 2: Without uv (Using pip)

```bash
# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -e .
pip install mypy pydantic ruff pytest pytest-asyncio pytest-cov pytest-freezegun pytest-mock
```

---

## Usage

### Running the Main Application

```bash
# With uv
uv run main.py

# Without uv (virtual environment activated)
python main.py
```

### Development Commands

```bash
# Type checking
# With uv
uv run mypy .
# Without uv
mypy .

# Linting
# With uv
uv run ruff check .
uv run ruff check --fix .
# Without uv
ruff check .
ruff check --fix .

# Formatting
# With uv
uv run ruff format src
# Without uv
ruff format src
```

---

## Testing

### Implemented Tests

The project includes a comprehensive integration test suite validating critical system behavior:

#### TestSimplePortfolioRebalancing
- **`test_simple_rebalancing_maintains_correct_distribution`**: Verifies rebalancing maintains target distribution when prices change significantly (the core requirement)
- **`test_no_rebalancing_when_prices_stable`**: Confirms no unnecessary operations when prices are stable within threshold

#### TestHighVolumeRebalancing
- **`test_rebalancing_with_hundreds_of_random_price_changes`**: Load test validating system against 200 random price changes with validation checkpoints
- **`test_rebalancing_with_extreme_price_levels`**: Tests rebalancing under extreme volatility scenarios

#### TestRebalanceLockMechanism
- **`test_concurrent_rebalances_are_prevented_by_lock`**: Verifies locking prevents race conditions during concurrent rebalances
- **`test_lock_is_released_after_rebalance_completes`**: Confirms lock releases after successful rebalance
- **`test_lock_is_released_after_rebalance_fails`**: Ensures lock releases even when rebalance fails
- **`test_expired_lock_is_acquired_automatically`**: Tests automatic recovery when a lock has expired

#### TestRollbackMechanism
- **`test_rollback_on_partial_rebalance_failure`**: Validates successful operations reverse when any operation fails
- **`test_portfolio_state_consistent_after_rollback`**: Verifies complete portfolio state consistency after successful rollback
- **`test_stale_state_when_rollback_fails`**: Tests portfolio enters stale state when rollback fails, blocking subsequent operations

#### TestLargeScaleRegistryRebalancing
- **`test_large_scale_rebalancing_with_many_portfolios`**: Massive load test validating system with 100 portfolios and 50 stocks across multiple waves of price changes (10, 20, and 100 changes)

### Running Tests with INFO Logging

To see logs in real-time while running tests:

```bash
# With uv
uv run pytest tests/ -v --log-cli-level=INFO --log-cli-format='%(asctime)s [%(levelname)8s] %(message)s' --log-cli-date-format='%Y-%m-%d %H:%M:%S'

# Without uv (virtual environment activated)
pytest tests/ -v --log-cli-level=INFO --log-cli-format='%(asctime)s [%(levelname)8s] %(message)s' --log-cli-date-format='%Y-%m-%d %H:%M:%S'
```

### Testing Options

```bash
# Run with DEBUG level for more detail
# With uv
uv run pytest tests/ -v --log-cli-level=DEBUG --log-cli-format='%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d - %(message)s' --log-cli-date-format='%Y-%m-%d %H:%M:%S'
# Without uv
pytest tests/ -v --log-cli-level=DEBUG --log-cli-format='%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d - %(message)s' --log-cli-date-format='%Y-%m-%d %H:%M:%S'

# Specific rebalancing tests
# With uv
uv run pytest tests/integration/test_portfolio_rebalancing.py -v --log-cli-level=INFO
# Without uv
pytest tests/integration/test_portfolio_rebalancing.py -v --log-cli-level=INFO

# Specific test class
# With uv
uv run pytest tests/integration/test_portfolio_rebalancing.py::TestSimplePortfolioRebalancing -v --log-cli-level=INFO
# Without uv
pytest tests/integration/test_portfolio_rebalancing.py::TestSimplePortfolioRebalancing -v --log-cli-level=INFO

# With coverage report
# With uv
uv run pytest tests/integration/test_portfolio_rebalancing.py --cov=src/portfolio --cov=src/broker --cov-report=term-missing -v --log-cli-level=INFO
# Without uv
pytest tests/integration/test_portfolio_rebalancing.py --cov=src/portfolio --cov=src/broker --cov-report=term-missing -v --log-cli-level=INFO

# Fast execution (no logs)
# With uv
uv run pytest tests/ -v
# Without uv
pytest tests/ -v

# Exclude slow tests (marked as @pytest.mark.slow)
# With uv
uv run pytest tests/ -v -m "not slow"
# Without uv
pytest tests/ -v -m "not slow"

# Only slow tests
# With uv
uv run pytest tests/ -v -m "slow"
# Without uv
pytest tests/ -v -m "slow"
```

---

## Technical Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Main language |
| **Pydantic** | >= 2.12.5 | Data validation and models |
| **pytest** | >= 9.0.2 | Testing framework |
| **mypy** | >= 1.19.1 | Static type checking |
| **ruff** | >= 0.14.11 | Ultra-fast linter (replaces flake8, pylint, isort) and formatter (replaces black) |
| **asyncio** | (stdlib) | Asynchronous programming in Python |

---

## Project Structure

```
fintech-portfolio-rebalancing/
├── src/
│   ├── broker/                  # Broker with batch operations and rollback
│   ├── config/                  # Centralized, immutable configuration
│   ├── portfolio/               # Portfolio management with rebalancing
│   ├── stock/                   # Stock entities
│   └── utils/                   # Shared utilities
│
├── tests/
│   └── integration/             # Integration tests
│       ├── test_portfolio_rebalancing.py
│       └── test_large_scale_registry_rebalancing.py
│
├── main.py                      # Application demo
├── README.md                    # This file
├── CLAUDE.md                    # Instructions for Claude Code
├── pyproject.toml               # Project configuration
└── pytest.ini                   # Test configuration
```

---

<div align="center">

**A demonstration of production-grade software engineering for fintech applications**

[Challenge Overview] • [Testing](#-testing) • [Architecture](#-architecture)

</div>
