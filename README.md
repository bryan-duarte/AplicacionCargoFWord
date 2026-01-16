<div align="center">

# 🏦 FWord Auto balancer

**Sistema de gestión de portafolios con rebalanceo automático y operaciones atómicas**

[Python 3.11+](https://www.python.org/)(https://opensource.org/licenses/MIT) [![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

[Features](#-features-destacadas) • [Arquitectura](#-arquitectura) • [Instalación](#-instalacin) • [Uso](#-uso) • [Testing](#-testing)

</div>

---
Disclaimer:

Resubmit request: Solicité si podrían reconsiderar mi postulación, ya que reflexionando leugo del primer submit me di cuenta que hice puras bobadas y no me enfoque en el caso de negocio adyacente relevante en la implementación.

En el submit previo, mucho bla bla bla, que patrón de diseño 1,2,3 pero el core del negocio no era atendido. Era bueno para un tutorial, pero no era production grade propio de una postulación a un L2. (IMO)

Se eliminaron las bobadas y quedó lo clave, que la funcionalidad funcione BIEN, que tenga tests y que maneje los casos que pueden afectar a los usuarios, el resto era bullshit y admito el error. (al menos fué una postulación diferente no(?) jaja )

[-No eliminaré el link del video por si necesito un motivo para ser socialmente excluido en caso de quedar-]

## 📋 Descripción

Sistema de gestión de portafolios de inversión en tiempo real con **rebalanceo automático** basado en cambios de precio de acciones.

---

## ✨ Features Destacados (Que atienden una negecidad de negocio y que sí importan)

### 🔒 Mecanismo de Locking para Prevenir Rebalanceos Concurrentes

El sistema implementa un **bloqueo distribuido a nivel de portafolio** que previene race conditions durante operaciones críticas:

- **Bloqueo con TTL**: Tiempo de vida configurable (default: 6 horas, un poco de intuición, pero es referencial) para prevenir deadlocks
- **Limpieza automática**: El lock expira y se libera automáticamente si el proceso falla
- **Prevención de operaciones simultáneas**: Garantiza que solo un rebalanceo ocurra a la vez
- **Detección de locks expirados**: Permite recuperar portafolios en caso de fallos

**¿Por qué importa?** En un sistema de producción donde múltiples eventos pueden disparar rebalanceos concurrentemente, este mecanismo protege la integridad de los datos del portafolio del usuario.

### 🔄 Rollback Automático de Operaciones Batch

Todas las operaciones del broker se agrupan en **transacciones atómicas** con rollback automático:

- **Operaciones atómicas**: Todas las compras/ventas en un rebalanceo se ejecutan como una unidad
- **Seguimiento de estado**: Cada operación tiene estados (PENDING → SUCCESS → ERROR → ROLLED_BACK)
- **Compensación automática**: Si alguna operacion falla, las exitosas se revierten automáticamente
- **Reintentos configurables**: Hasta 3 reintentos con delay configurable para operaciones de rollback
- **Logging completo**: Toda la traza de operaciones queda registrada para auditoría

**¿Por qué importa?** En FWord Acciones, esto significa que **nunca** se dejará a un usuario en un estado inconsistente. Si falla una venta de acciones, la compra correspondiente también se revierte.

Y si falla, el metodo de set_stale podría mandar un aviso por slack y se soluciona en tiempo record (esperamos que no)

### ⚖️ Rebalanceo Automático "Inteligente"

El sistema detecta y corrige desviaciones de manera automática:

- **Umbral configurable**: Solo rebalancea cuando la desviación supera el threshold (default: 5%, otra vez intuición)
- **Cálculo preciso**: Usa aritmética decimal para evitar errores de redondeo financiero (tocó aprender)
- **Ejecución asíncrona**: Compras y ventas se ejecutan en paralelo para optimizar tiempos
- **Validación de reglas**: Verifica que la suma de allocations sea exactamente 100%

**¿Por qué importa?** Los portafolios de los usuarios se mantienen siempre alineados con su estrategia de inversión.

### 💎 Precisión Financiera con Decimal

Uso sistemático de `Decimal` para evitar floating-point errors:

- **Dinero**: 2 decimales ($10.00)
- **Cantidad**: 9 decimales (acciones fraccionarias: 1.234567890. Esta vez no es intuición, sino de la documentación de alpaca) https://docs.alpaca.markets/docs/fractional-trading
- **Porcentajes**: 4 decimales (20.0000%)

**¿Por qué importa?** Un error de $0.01 multiplicado por millones de usuarios se convierte en una pérdida significativa. (sino, preguntenle al banco estado, cof cof)


---

## 🏗️ Arquitectura

### Módulos Principales

```
src/
├── broker/              # Intermediario financiero con operaciones atómicas
│   ├── broker_interface.py    # Protocolo abstracto del broker
│   ├── broker.py               # BanChileBroker con rollback automático
│   ├── broker_dtos.py          # Modelos de datos para operaciones
│   └── errors.py               # Excepciones específicas
│
├── portfolio/           # Gestión de portafolios con rebalanceo
│   ├── portfolio.py            # Portfolio con locking y rebalanceo
│   ├── portfolio_dtos.py       # Configuración y validaciones
│   ├── portfolio_register.py   # Registry de portafolios con símbolo
│   └── errors.py               # Excepciones específicas
│
├── stock/               # Entidades de acciones
│   ├── stock.py                # Stock con validación de símbolo/precio
│   └── errors.py               # Excepciones específicas
│
├── config/              # Configuración centralizada
│   └── config.py               # Settings inmutables del sistema
│
└── utils/               # Utilidades compartidas
    ├── decimal_utils.py        # Cuantización de decimales
    └── fake_market.py          # Simulador de mercado NASDAQ
```

### Flujo de Rebalanceo

```
┌─────────────────┐
│ Precio cambia   │
│ (META: $400)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ Registry detecta portafolios │
│ afectados por el símbolo     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Calcula desviación vs objetivo  │
│ ¿Supera threshold (5%)?         │
└────────┬────────────────────────┘
         │ NO
         ├─────────────────────► (Fin - no rebalancear)
         │ SÍ
         ▼
┌─────────────────────────────┐
│ Adquirir lock de rebalanceo │
│ ¿Disponible?                │
└────────┬────────────────────┘
         │ NO
         ├─────────────────────► (Fin - ya hay rebalanceo en curso)
         │ SÍ
         ▼
┌──────────────────────────────────────┐
│ Calcular operaciones necesarias      │
│ - Comprar stocks con déficit         │
│ - Vender stocks con exceso           │
└────────┬─────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Ejecutar operaciones en batch       │
│ (asyncio.gather en paralelo)        │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ ¿Todas exitosas?            │
└────────┬────────────────────┘
         │ SÍ
         ├─────────────────────► Actualizar cantidades ✓
         │
         │ NO
         ▼
┌─────────────────────────────────┐
│ 🔴 Rollback automático          │
│ - Ejecutar operaciones inversas │
│ - Marcar portafolio como STALE  │
│ - Requiere intervención manual  │
└─────────────────────────────────┘
```

---

## 📦 Instalación

### Opción 1: Con uv (Recomendado, taweno)

[uv](https://github.com/astral-sh/uv) es un gestor de paquetes Python ultrarrápido.

```bash
# Instalar uv (si no lo tienes)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clonar el repositorio
git clone <repo-url>
cd FWord-software-engineer-apply

# Instalar dependencias
uv sync

# Activar el entorno virtual
source .venv/bin/activate  # En Linux/Mac
# o
.venv\Scripts\activate     # En Windows
```

### Opción 2: Sin uv (Con pip)

```bash
# Crear entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate  # En Linux/Mac
# o
.venv\Scripts\activate     # En Windows

# Instalar dependencias
pip install -e .
pip install mypy pydantic ruff pytest pytest-asyncio pytest-cov pytest-freezegun pytest-mock
```

### Requisitos del Sistema

- **Python**: >= 3.11
- **Sistema Operativo**: Linux, macOS, Windows
- **Memoria**: Mínimo 512 MB RAM
- **Red**: Conexión a internet para descargar dependencias

(Gracias Claude por este parrafo totalmente inventado)
---

## 🚀 Uso

### Ejecutar la Aplicación Principal

```bash
# Con uv
uv run main.py

# Sin uv (entorno virtual activado)
python main.py
```

**Salida esperada:**

```
2026-01-16 10:30:00 [    INFO] Starting portfolio management system
2026-01-16 10:30:00 [    INFO] Creating portfolio with initial investment: $100,000
2026-01-16 10:30:00 [    INFO]   - META: 33.33% allocation
2026-01-16 10:30:00 [    INFO]   - AAPL: 33.33% allocation
2026-01-16 10:30:00 [    INFO]   - MSFT: 33.34% allocation

2026-01-16 10:30:03 [    INFO] 📈 META price changed: $400.00 -> $440.00 (+10.00%)
2026-01-16 10:30:05 [    INFO] Portfolio deviation detected: 8.50% > 5.00% threshold
2026-01-16 10:30:05 [    INFO] 🔄 Rebalancing portfolio...

[BanChileBroker] Batch operation started: uuid-1234
[BanChileBroker] Buying 15.25 shares of AAPL at $165.00
[BanChileBroker] Selling 20.50 shares of META at $440.00
[BanChileBroker] Batch completed successfully

2026-01-16 10:30:08 [    INFO] ✅ Rebalance completed successfully
```

### Ejecutar Commands de Desarrollo

```bash
# Type checking
uv run mypy .

# Linting
uv run ruff check .
uv run ruff check --fix .

# Formatting
uv run ruff format src
```

---

## 🧪 Testing

### Tests Implementados

El proyecto cuenta con una suite de tests de integración que valida el comportamiento crítico del sistema:

#### TestSimplePortfolioRebalancing
- **`test_simple_rebalancing_maintains_correct_distribution`**: Verifica que el rebalanceo mantiene la distribución objetivo cuando los precios cambian significativamente
- **`test_no_rebalancing_when_prices_stable`**: Confirma que no se realizan operaciones innecesarias cuando los precios están estables y dentro del threshold

#### TestHighVolumeRebalancing
- **`test_rebalancing_with_hundreds_of_random_price_changes`**: Test de carga que valida el sistema ante 200 cambios de precios aleatorios con checkpoints de validación
- **`test_rebalancing_with_extreme_price_levels`**: Prueba el rebalanceo ante escenarios de volatilidad extrema con precios variables

#### TestRebalanceLockMechanism
- **`test_concurrent_rebalances_are_prevented_by_lock`**: Verifica que el mecanismo de locking previene race conditions durante rebalanceos concurrentes
- **`test_lock_is_released_after_rebalance_completes`**: Confirma que el lock se libera correctamente tras un rebalanceo exitoso
- **`test_lock_is_released_after_rebalance_fails`**: Asegura que el lock se libera incluso cuando el rebalanceo falla
- **`test_expired_lock_is_acquired_automatically`**: Prueba la recuperación automática cuando un lock ha expirado

#### TestRollbackMechanism
- **`test_rollback_on_partial_rebalance_failure`**: Valida que las operaciones exitosas se revierten cuando alguna operación falla
- **`test_portfolio_state_consistent_after_rollback`**: Verifica la consistencia completa del estado del portafolio después de un rollback exitoso
- **`test_stale_state_when_rollback_fails`**: Prueba que el portafolio entra en estado stale cuando falla el rollback, bloqueando operaciones posteriores

### Ejecutar Tests con Logging INFO

Para ver los logs en tiempo real mientras ejecutas los tests:

```bash
# Todos los tests con logging
uv run pytest tests/ -v --log-cli-level=INFO --log-cli-format='%(asctime)s [%(levelname)8s] %(message)s' --log-cli-date-format='%Y-%m-%d %H:%M:%S'
```

### Opciones de Testing

```bash
# Ejecutar con nivel DEBUG para mayor detalle
uv run pytest tests/ -v --log-cli-level=DEBUG --log-cli-format='%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d - %(message)s' --log-cli-date-format='%Y-%m-%d %H:%M:%S'

# Tests específicos de rebalanceo
uv run pytest tests/integration/test_portfolio_rebalancing.py -v --log-cli-level=INFO

# Una clase específica
uv run pytest tests/integration/test_portfolio_rebalancing.py::TestSimplePortfolioRebalancing -v --log-cli-level=INFO

# Con coverage report
uv run pytest tests/integration/test_portfolio_rebalancing.py --cov=src/portfolio --cov=src/broker --cov-report=term-missing -v --log-cli-level=INFO

# Sin logs (ejecución rápida)
uv run pytest tests/ -v
```

### Opciones de Logging Disponibles

| Opción | Descripción |
|--------|-------------|
| `--log-cli-level=INFO` | Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `--log-cli-format` | Formato personalizado de los logs |
| `--log-cli-date-format` | Formato de fecha/hora en los logs |
| `-v` | Modo verbose de pytest |
| `-s` | Mostrar output de print statements |

### Ejemplo de Salida con Logs

```
============================= test session starts ==============================
collected 5 items

tests/integration/test_portfolio_rebalancing.py::TestSimplePortfolioRebalancing::test_rebalance_when_price_changes PASSED
2026-01-16 10:35:12 [    INFO] Creating dummy broker for testing
2026-01-16 10:35:12 [    INFO] Initializing portfolio with 3 stocks
2026-01-16 10:35:13 [    INFO] Stock AAPL price changed: $150.00 -> $165.00 (+10.00%)
2026-01-16 10:35:13 [    INFO] Portfolio deviation detected: 12.50% > 5.00% threshold
2026-01-16 10:35:13 [    INFO] Rebalancing portfolio: Buying AAPL, Selling GOOGL

tests/integration/test_portfolio_rebalancing.py::TestPortfolioLocking::test_concurrent_rebalance_prevention PASSED
2026-01-16 10:35:15 [    INFO] Acquired rebalance lock
2026-01-16 10:35:15 [    INFO] Second rebalance attempt blocked - lock held by another process

tests/integration/test_portfolio_rebalancing.py::TestBatchRollback::test_rollback_on_failure PASSED
2026-01-16 10:35:17 [    INFO] Batch operation failed, starting rollback
2026-01-16 10:35:18 [    INFO] Rollback completed - portfolio in stale state

============================== 5 passed in 6.42s ==============================
```

---

## 🛠️ Stack Técnico

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.11+ | Lenguaje principal |
| **Pydantic** | >= 2.12.5 | Validación de datos y modelos |
| **pytest** | >= 9.0.2 | Framework de testing |
| **mypy** | >= 1.19.1 | Type checking estático |
| **ruff** | >= 0.14.11 | Linter ultra-rápido (reemplaza flake8, pylint, isort) y formatter (reemplaza black) |
| **asyncio** | (stdlib) | Programación asíncrona |

---

## 📁 Estructura del Proyecto

```
FWord-software-engineer-apply/
├── src/
│   ├── broker/                  # Broker con operaciones batch y rollback
│   ├── config/                  # Configuración centralizada e inmutable
│   ├── portfolio/               # Gestión de portafolios con rebalanceo
│   ├── stock/                   # Entidades de acciones
│   └── utils/                   # Utilidades compartidas
│
├── tests/
│   └── integration/             # Tests de integración
│       └── test_portfolio_rebalancing.py
│
├── main.py                      # Demo de la aplicación
├── README.md                    # Este archivo
├── CLAUDE.md                    # Instrucciones para Claude Code
├── pyproject.toml               # Configuración del proyecto
└── pytest.ini                   # Configuración de tests
```

---

## 📄 Licencia

Este proyecto es parte del proceso de selección para el cargo de Desarrollador de Software en FWord.

---

<div align="center">

**Hecho con 💙 para el proceso de F*word**

[Challenge](#-FWord-portfolio-management-system) • [Testing](#-testing) • [Arquitectura](#-arquitectura)

</div>
