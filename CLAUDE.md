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

This is a Python-based financial portfolio management system demonstrating automatic rebalancing of portfolios based on stock price changes. The system implements an event-driven architecture similar to what might be used in a fintech platform like FWord.

## Architecture

### Event-Driven Core

The system uses an in-memory async event bus for decoupled communication:

- **Event Bus** (`src/event_bus/event_bus.py`): Async pub/sub system
- **Event Types**: `STOCK_PRICE_CHANGE` and `PORTFOLIO_REBALANCE`
- **Event Handlers** (`src/event_bus/event_handlers.py`): Handle price changes and trigger rebalancing
- **Event DTOs** (`src/event_bus/event_dtos.py`): Pydantic models for type-safe event data

Flow: Stock price changes → event emitted → portfolio receives via registry → rebalancing triggered

### Key Modules

#### `/src/broker/`
- `broker_interface.py`: Protocol defining broker operations (buy/sell by amount or quantity)
- `broker.py`: `BanChileBroker` implementation with simulated 1-2s network latency
- `broker_dtos.py`: Request/response models with UUID tracking
- `errors.py`: Broker-specific exceptions

#### `/src/portfolio/`
- `portfolio.py`: Portfolio class with auto-rebalancing logic
- `portfolio_register.py`: Registry for managing portfolios and looking up by stock symbol
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

1. **Observer Pattern**: Stocks emit price events, portfolios listen
2. **Registry Pattern**: `PortfolioRegistry` manages portfolios by stock symbol
3. **Strategy Pattern**: Broker protocol allows multiple implementations
4. **Repository Pattern**: NASDAQ fake market as stock repository

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

- `pydantic>=2.12.5`: Data validation and models
- `mypy>=1.19.1`: Static type checking
- `ruff>=0.14.11`: Linting and formatting

## Python Version

Requires Python >=3.11
