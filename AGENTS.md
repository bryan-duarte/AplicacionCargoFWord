# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Project

```bash
# Run the main application
uv run main.py

# Type checking
mypy .

# Linting
ruff check .
ruff check --fix .
ruff format src
```

## Project Overview

This is a Python-based financial portfolio management system demonstrating automatic rebalancing of portfolios based on stock price changes. The system implements a registry-based architecture with direct communication patterns similar to what might be used in a fintech platform.

## Architecture

### Communication Flow

The system uses direct synchronous communication through a registry pattern:

- Stock price changes occur in the market
- `main.py` calls `portfolio_registry.get_by_stock_symbol(symbol)` to find affected portfolios
- Each portfolio's `rebalance()` method is called directly
- Portfolio executes buy/sell operations through the broker interface

Flow: Stock price changes → registry lookup via `get_by_stock_symbol()` → direct `rebalance()` call → broker operations

### Key Modules

#### `/src/broker/`
- `broker_interface.py`: Protocol defining broker operations (buy/sell by amount or quantity)
- `broker.py`: `BanChileBroker` implementation with simulated 1-2s network latency
- `broker_dtos.py`: Request/response models with UUID tracking
- `errors.py`: Broker-specific exceptions

#### `/src/portfolio/`
- `portfolio.py`: Portfolio class with auto-rebalancing logic, lock management, and stale state handling
- `portfolio_register.py`: Registry using `weakref.WeakSet` for automatic memory management
- `portfolio_dtos.py`: Configuration models (allocation must sum to 100%)
- `errors.py`: Portfolio-specific exceptions

#### `/src/stock/`
- `stock.py`: Stock entity with price validation and alerts
- `errors.py`: Stock-specific exceptions

#### `/src/utils/`
- `decimal_utils.py`: Decimal precision utilities (money: 2 decimals, quantity: 9, percentage: 4)
- `fake_market.py`: NASDAQ stock data simulation

#### `/src/config/`
- `config.py`: Centralized settings for all modules (thresholds, limits, precision)

### Design Patterns Used

1. **Registry Pattern**: `PortfolioRegistry` uses `weakref.WeakSet` to manage portfolios by stock symbol with automatic memory management
2. **Strategy Pattern**: `Broker` interface allows multiple implementations (`BanChileBroker`)
3. **Repository Pattern**: `FakeMarket` acts as a stock data repository
4. **Command Pattern**: Broker DTOs (`BuyStockByAmountRequest`, `SellStockByQuantityRequest`, etc.) encapsulate operations with UUID tracking
5. **Batch Processing Pattern**: UUID-based operation grouping with automatic rollback on failure

## Important Constraints

### Financial Precision
- All monetary values use Python's `Decimal` type
- Money: 2 decimal places
- Quantity: 9 decimal places (fractional shares supported)
- Percentage: 4 decimal places

### Key Limits
- Stock symbol: Exactly 4 uppercase letters
- Stock price range: $0.01 - $1,000,000
- Minimum investment: $1 USD
- Retail threshold: $25,000 USD
- Maximum portfolio value: $10M USD
- Maximum quantity: 1,000,000 shares

## Dependencies

### Core Dependencies
- `pydantic>=2.12.5`: Data validation and models
- `mypy>=1.19.1`: Static type checking
- `ruff>=0.14.11`: Linting and formatting

### Development Dependencies
- `pytest>=9.0.2`: Testing framework
- `pytest-asyncio>=1.3.0`: Async test support
- `pytest-cov>=7.0.0`: Coverage reporting
- `pytest-freezegun>=0.4.2`: Time manipulation in tests
- `pytest-mock>=3.15.1`: Mocking utilities

## Python Version

Requires Python >=3.11

## Testing

### Test Configuration
- **Configuration file**: `pytest.ini`
- **Async mode**: `asyncio_mode = auto` for automatic async test support
- **Test discovery**: `tests/integration/test_*.py`

### Test Structure
- **Main test file**: `tests/integration/test_portfolio_rebalancing.py`
- **Fixtures**: `tests/conftest.py` with comprehensive setup for stocks, brokers, and portfolios
- **Registry cleanup**: Automatic cleanup between tests

### Test Categories
1. **TestSimplePortfolioRebalancing**: Basic rebalancing functionality
2. **TestHighVolumeRebalancing**: Performance and edge cases (marked as `@pytest.mark.slow`)
3. **TestRebalanceLockMechanism**: Concurrency control and lock management
4. **TestRollbackMechanism**: Transaction rollback and error handling

### Test Doubles
- **DummyBroker**: Mock broker for controlled testing scenarios
- **FailingRollbackBroker**: Broker that simulates rollback failures

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run only fast tests (exclude slow)
pytest -m "not slow"

# Run specific test class
pytest tests/integration/test_portfolio_rebalancing.py::TestSimplePortfolioRebalancing
```

## Error Handling Architecture

### Exception Hierarchy
```
BaseException
├── BrokerError (with UUID tracking)
│   ├── BuyStockError
│   │   └── StockNotFoundError
│   └── SellStockError
│       └── BrokerConnectionError
├── PortfolioError
│   ├── PortfolioInitializationError (with failed_operations list)
│   ├── PortfolioRetryError (with attempt tracking)
│   └── PortfolioStaleError
└── StockError
    ├── InvalidSymbolError
    └── InvalidPriceError
```

### State Management Patterns
- **Stale State**: Portfolios enter stale state after failed rollback
- **Lock Mechanism**: Rebalancing locks prevent concurrent operations with TTL-based expiration
- **Rollback Pattern**: Batch operations use UUID tracking for atomic semantics (all succeed or all rollback)
- **Idempotency**: UUID-based operations allow safe retries
