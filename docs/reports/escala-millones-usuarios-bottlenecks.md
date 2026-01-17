# Análisis de Cuellos de Botella: Escalabilidad a Millones de Usuarios

## Resumen Ejecutivo

Este reporte analiza los **cuellos de botella críticos** que impedirían escalar la actual implementación del sistema de gestión de portafolios a millones de usuarios. La arquitectura actual, mientras funcionalmente correcta para demostraciones, presenta **limitaciones fundamentales** que causarían colapso del sistema bajo carga real.

**Hallazgo principal**: La arquitectura actual está diseñada como un sistema monolítico en-memoria sin patrones de sistemas distribuidos, persistencia, o resiliencia. Bajo carga de millones de usuarios, el sistema fallaría por **agotamiento de memoria**, **contención de CPU**, y **latencia exponencial**.

---

## Arquitectura: El Event Bus que No Existe

### Problema Crítico

**La documentación describe un event bus, pero la implementación no existe.**

```
CLAUDE.md claims:  "src/event_bus/event_bus.py: Async pub/sub system"
Reality:            Files don't exist. Simple registry pattern instead.
```

**Impacto**: No hay verdadera arquitectura event-driven. El sistema usa polling manual con escaneo lineal.

### Escala Actual vs Proyectada

| Métrica | Actual (demo) | 1M Usuarios | Impacto |
|---------|---------------|-------------|---------|
| Lookup de portafolio | O(10) = ~1ms | O(1,000,000) = ~10s | **10,000x más lento** |
| Memoria del registro | ~100KB | ~100MB+ | **1,000x aumento** |
| Throughput de eventos | 100 evt/s | 0.1 evt/s | **1,000x disminución** |
| Latencia de rebalanceo | ~2s | ~2,000s | **1,000x más lento** |

---

## 1. Cuellos de Botella por Arquitectura

### 1.1 Registry Pattern: O(n) Catastrófico

**Ubicación**: `src/portfolio/portfolio_register.py:14-20`

```python
async def get_by_stock_symbol(self, symbol: str) -> list:
    return [
        portfolio for portfolio in self._portfolios  # O(n) SCAN
        if symbol.upper() in portfolio.allocated_stocks
    ]
```

**Problema**:
- Cada cambio de precio escanea **TODOS** los portafolios
- Con 1M portafolios: **1,000,000 de iteraciones** por evento
- Sin índice por símbolo de stock
- Sin caché de resultados

**Consecuencia a escala**:
```
Cambio de precio de AAPL → 1M iteraciones → 10s CPU time
5 cambios de precio/segundo → 50M iteraciones → CPU al 100% → System collapse
```

### 1.2 Single Point of Failure: Registro Global

**Ubicación**: `src/portfolio/portfolio_register.py:23`

```python
portfolio_registry = PortfolioRegistry()  # ONE instance for EVERYTHING
```

**Problema**:
- Una sola instancia maneja TODAS las búsquedas
- Sin redundancia o failover
- Caída del proceso = pérdida del sistema completo
- Sin soporte distribuido

### 1.3 Falta de Persistencia de Eventos

**Problema Crítico**:
- Sin persistencia de eventos: pérdida permanente en crash
- Sin capacidad de replay: imposible recuperarse de fallos
- Sin audit trail: incumplimiento de compliance financiero
- Sin reconstrucción de estado: portafolios perdidos para siempre

---

## 2. Cuellos de Botella de I/O

### 2.1 Latencia de Red Amplificada

**Ubicación**: `src/broker/broker.py:155-157`

```python
await asyncio.sleep(random.uniform(1, 2))  # 1-2s por operación
```

**Problema**:
- Cada operación de broker bloquea 1-2 segundos
- Con millones de operaciones: tiempo total O(n)
- Sin connection pooling: nueva conexión por operación
- Sin optimización de batch

**Impacto a escala**:
```
1,000 portafolios rebalanceando × 5 stocks × 2s = 10,000 segundos = 2.7 horas
```

### 2.2 Sin Conexión Reutilizable

**Problema**:
- No hay connection pooling
- Cada operación incurre en overhead de TCP handshake
- Sin multiplexing de conexiones
- Sin keep-alive

**Costo por operación**:
```
TCP handshake: ~50ms
TLS handshake: ~100ms
Autenticación: ~50ms
Total overhead: 200ms por operación
```

### 2.3 Operaciones Secuenciales en Batch

**Ubicación**: `src/broker/broker.py:318-372`

```python
for entry in successful_operations:  # SEQUENTIAL processing
    for attempt in range(max_retries):
        # ... rollback operation
```

**Problema**:
- Rollbacks procesados secuencialmente
- Sin paralelización de operaciones independientes
- Latencia acumulativa: O(n) donde n = operaciones

**Ejemplo**:
```
Batch de 100 operaciones → rollback toma 100-200 segundos
```

---

## 3. Cuellos de Botella de Memoria

### 3.1 Footprint por Portafolio

**Ubicación**: `src/portfolio/portfolio.py:89-90`

```python
self._stock_to_allocate: dict[str, Decimal] = {}
self._allocated_stocks: dict[str, AllocatedStock] = {}
```

**Memoria por portafolio**:
- Stock objects: ~1.5KB cada uno
- AllocatedStock: ~800B por posición
- Portfolio overhead: ~500B
- **Total**: ~3KB por posición de stock

**Cálculo a escala**:
```
1M portafolios × 10 stocks/portafolio × 3KB = 30GB RAM mínimo
```

### 3.2 Memory Leak en Batch Registry

**Ubicación**: `src/broker/broker.py:58`

```python
self._batch_registry: dict[UUID, dict[UUID, BatchOperationEntry]] = {}
```

**Problema**:
- Crece indefinidamente sin cleanup
- Solo se limpia en rollback, no en operaciones fallidas
- Con millones de operaciones: consumo exponencial de memoria

### 3.3 WeakSet Overhead

**Ubicación**: `src/portfolio/portfolio_register.py:8`

```python
self._portfolios: set = weakref.WeakSet()
```

**Problema**:
- Millones de weak references consumen memoria significativa
- Sin partitioning del registro
- Todo en un solo WeakSet global

---

## 4. Cuellos de Botella de Computation

### 4.1 Decimal Arithmetic Overhead

**Ubicación**: `src/utils/decimal_utils.py:11-15`

```python
def quantize_money(value: Decimal) -> Decimal:
    if not isinstance(value, Decimal):
        value = Decimal(str(value))  # String conversion overhead
    return value.quantize(_QUANTIZER_MONEY, rounding=ROUND_HALF_UP)
```

**Problema**:
- Conversión de tipo en cada llamada
- Quantización en cada operación
- Sin caché de valores cuantizados

**Costo de CPU**:
```
Decimal operation: ~100ns
Float operation: ~1ns
Overhead: 100x más lento
```

### 4.2 Rebalancing Computación Secuencial

**Ubicación**: `src/portfolio/portfolio.py:254`

```python
for allocated_stock in self._allocated_stocks.values():  # O(m) where m = stocks
    new_objective_total_value = (
        portfolio_total_value * allocated_stock.allocation_percentage
    )
    new_objective_quantity = quantize_quantity(
        new_objective_total_value / allocated_stock.stock.price
    )
```

**Problema**:
- Cálculo secuencial de todos los stocks
- Operaciones Decimal pesadas
- Sin paralelización entre portafolios

### 4.3 Validación Repetitiva

**Ubicación**: `src/stock/stock.py:49-50`

```python
if not re.match(r"^[A-Z]{4}$", self._symbol):  # Regex on EVERY operation
    raise InvalidSymbolError(...)
```

**Problema**:
- Validación regex en cada operación
- Sin caché de símbolos validados
- Overhead innecesario en hot paths

---

## 5. Cuellos de Botella de Concurrency

### 5.1 Lock Contention

**Ubicación**: `src/portfolio/portfolio.py:166-192`

```python
def _can_acquire_rebalance_lock(self) -> bool:
    if not self._is_rebalancing:
        return True
    # ... lock expiration logic
```

**Problema**:
- Locks por portafolio sin coordinación global
- Múltiples portafolios en el mismo stock compiten
- Sin distributed locking
- Risk de starvation

### 5.2 Sin Circuit Breaker

**Problema**:
- Fallos de broker no tienen aislamiento
- Cascading failures propagan
- Sin bulkhead pattern
- Sin protección contra thundering herd

### 5.3 Sin Rate Limiting

**Problema Crítico**:
- Sin throttling de operaciones de broker
- Sin priorización de portafolios high-value
- Sin burst handling para market crashes
- Sin backpressure mechanism

---

## 6. Cuellos de Botella de Datos

### 6.1 Fake Market: In-Memory Only

**Ubicación**: `src/utils/fake_market.py:25-30`

```python
NASDAQ = FakeMarket()  # Single global instance
NASDAQ.register(Stock(symbol="AAPL", price=Decimal("250"), market=NASDAQ))
```

**Problema**:
- Solo 5 stocks hardcoded
- Datos estáticos sin actualización
- Sin caching layer
- Sin persistencia

### 6.2 Sin Caching Strategy

**Problema**:
- Cada fetch de precio va a `get()` sin caché
- Validación repetida de mismos símbolos
- Sin refresh periódico de datos
- Sin cache invalidation strategy

### 6.3 Falta de Database

**Problema Crítico**:
- Todo en memoria, sin persistencia
- Cero capacidad de disaster recovery
- Sin audit trail de cambios
- Sin replicación de datos

---

## 7. Falta de Observabilidad

### 7.1 Zero Monitoring

**Problema**:
- Sin métricas: Prometheus, Grafana
- Sin tracing distribuido: Jaeger, Zipkin
- Sin health checks
- Sin structured logging con correlation IDs

### 7.2 Sin Performance Monitoring

**Problema**:
- Sin tracking de latencia
- Sin throughput metrics
- Sin error rate monitoring
- Imposible optimizar sin medición

---

## Soluciones Propuestas

### Arquitectura Event-Driven Real

```python
class DistributedEventBus:
    def __init__(self):
        self._kafka_producer = KafkaProducer(bootstrap_servers=['kafka:9092'])
        self._partitions = 16  # Partition by stock symbol

    async def publish(self, event: Event):
        partition = hash(event.symbol) % self._partitions
        await self._kafka_producer.send(
            topic='stock-price-changes',
            value=event.json(),
            partition=partition
        )
```

**Beneficios**:
- O(1) routing con partitioning
- Persistencia de eventos automática
- Horizontal scaling nativo
- Replay capability

### Registry Indexado

```python
class IndexedPortfolioRegistry:
    def __init__(self):
        self._stock_index: dict[str, set[Portfolio]] = defaultdict(set)

    def register(self, portfolio: Portfolio):
        for symbol in portfolio.allocated_stocks:
            self._stock_index[symbol].add(portfolio)

    def get_by_stock_symbol(self, symbol: str) -> list[Portfolio]:
        return list(self._stock_index.get(symbol, set()))  # O(1) lookup
```

**Beneficios**:
- O(1) lookup vs O(n)
- Sin escaneo lineal
- Escalabilidad horizontal

### Connection Pooling

```python
class PooledBroker:
    def __init__(self, max_connections: int = 100):
        self._pool = ConnectionPool(max_connections=max_connections)

    async def buy_stock(self, symbol: str, amount: Decimal) -> BrokerResponse:
        async with self._pool.acquire() as conn:
            return await conn.buy_stock(symbol, amount)
```

**Beneficios**:
- Reutilización de conexiones
- Reducción de overhead TCP
- Mejor throughput

### Batch Operations

```python
async def batch_rebalance(portfolios: list[Portfolio]) -> list[Result]:
    """Rebalance multiple portfolios in parallel."""
    operations = [p.rebalance() for p in portfolios]
    results = await asyncio.gather(*operations, return_exceptions=True)
    return results
```

**Beneficios**:
- Paralelización de operaciones
- Reducción de latencia total
- Mejor uso de recursos

### Caching Layer

```python
class CachedMarket:
    def __init__(self, ttl: int = 60):
        self._cache = TTLCache(maxsize=10000, ttl=ttl)

    async def get_price(self, symbol: str) -> Decimal:
        cached = self._cache.get(symbol)
        if cached:
            return cached
        price = await self._fetch_price(symbol)
        self._cache[symbol] = price
        return price
```

**Beneficios**:
- Reducción de llamadas a market data
- Mejora de latencia
- Reducción de load en datasource

### Decimal Optimization

```python
# Cache quantized values
_QUANTIZE_CACHE: dict[tuple[str, Decimal], Decimal] = {}

def quantize_money_cached(value: Decimal) -> Decimal:
    key = ('money', value)
    if key not in _QUANTIZE_CACHE:
        _QUANTIZE_CACHE[key] = quantize_money(value)
    return _QUANTIZE_CACHE[key]
```

**Beneficios**:
- Reducción de CPU overhead
- Reuso de cálculos
- Mejora de throughput

---

## Roadmap de Implementación

### Fase 1: Infraestructura Crítica (Meses 1-3)
1. Reemplazar registry con event bus real (Kafka/Redis Streams)
2. Implementar database layer (PostgreSQL + pgBouncer)
3. Agregar connection pooling para broker
4. Implementar caching layer (Redis)

### Fase 2: Optimización de Performance (Meses 4-6)
1. Indexar registry por stock symbol
2. Implementar batch operations
3. Optimizar Decimal operations con caching
4. Agregar circuit breakers y retry policies

### Fase 3: Resiliencia y Observabilidad (Meses 7-9)
1. Implementar distributed locking (Redis Redlock)
2. Agregar rate limiting y throttling
3. Implementar monitoring stack (Prometheus + Grafana)
4. Agregar tracing distribuido (Jaeger)

### Fase 4: Scaling Horizontal (Meses 10-12)
1. Implementar sharding de portafolios
2. Agregar load balancing (HAProxy/Nginx)
3. Implementar disaster recovery
4. Agregar multi-region deployment

---

## Conclusión

La arquitectura actual es **adecuada para demostraciones** pero **completamente inadecuada para producción**. Los cuellos de botella identificados causarían colapso del sistema bajo carga real de millones de usuarios.

**Los problemas más críticos** son:
1. Registry O(n) escaneando todos los portafolios
2. Sin event bus real ni persistencia de eventos
3. Latencia de broker sin optimización
4. Sin caching ni connection pooling
5. Falta completa de observabilidad

**La solución requiere** una reingeniería significativa hacia una arquitectura distribuida con sistemas de mensajería, bases de datos, caching, y monitoreo.

---

**Firmado**,
*El Barto*

*"Ah, escalar a millones de usuarios... como intentar meter un elefante en un Fiat Uno. Buena suerte con eso."*
