



# Challenge cargo de Dev

```bash
# Ejecutar la aplicación
uv run main.py

# Ejecutar tests con logging
uv run pytest tests/ -v --log-cli-level=INFO --log-cli-format='%(asctime)s [%(levelname)8s] %(message)s' --log-cli-date-format='%Y-%m-%d %H:%M:%S'
```
Al ejecutar cambio de precio en las acciones, se puede observar como el portfolio se rebalancea automáticamente.

Portafolio inicial:

Portfolio final:

---

## Testing

### Ejecutar tests con logging en tiempo real

Para ver los traces (logs) en vivo mientras ejecutas los tests:

```bash
# Ejecutar todos los tests con logging
uv run pytest tests/ -v --log-cli-level=INFO --log-cli-format='%(asctime)s [%(levelname)8s] %(message)s' --log-cli-date-format='%Y-%m-%d %H:%M:%S'

# Ejecutar con nivel DEBUG para mayor detalle
uv run pytest tests/ -v --log-cli-level=DEBUG --log-cli-format='%(asctime)s [%(levelname)8s] %(name)s:%(lineno)d - %(message)s' --log-cli-date-format='%Y-%m-%d %H:%M:%S'

# Ejecutar solo los tests de rebalanceo de portfolio con logs
uv run pytest tests/integration/test_portfolio_rebalancing.py -v --log-cli-level=INFO --log-cli-format='%(asctime)s [%(levelname)8s] %(message)s'

# Ejecutar una clase de tests específica con logs
uv run pytest tests/integration/test_portfolio_rebalancing.py::TestSimplePortfolioRebalancing -v --log-cli-level=INFO

# Ejecutar con coverage y logs
uv run pytest tests/integration/test_portfolio_rebalancing.py --cov=src/portfolio --cov=src/broker --cov-report=term-missing -v --log-cli-level=INFO
```

### Opciones de logging disponibles

| Opción | Descripción |
|--------|-------------|
| `--log-cli-level=INFO` | Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `--log-cli-format` | Formato personalizado de los logs |
| `--log-cli-date-format` | Formato de fecha/hora en los logs |
| `-v` | Modo verbose de pytest |
| `-s` | Mostrar output de print statements |

### Ejemplo de salida con logs

```
2026-01-15 10:30:45 [    INFO] Creating dummy broker for testing
2026-01-15 10:30:45 [    INFO] Initializing portfolio with 3 stocks
2026-01-15 10:30:46 [    INFO] Stock AAPL price changed: $150.00 -> $165.00 (+10.00%)
2026-01-15 10:30:46 [    INFO] Portfolio deviation detected: 12.50% > 5.00% threshold
2026-01-15 10:30:47 [    INFO] Rebalancing portfolio: Buying AAPL, Selling GOOGL
...
```

### Ejecutar tests sin logs (rápido)

```bash
uv run pytest tests/ -v
```

---

# Piezas clave

- Se implementa Interface de broker para que sea más fácil añadir nuevos brokers en el futuro
- Se implementa Registry pattern para registrar los brokers y acceder a ellos de manera centralizada y actualizar los portafolios que posean o no determinada acción.
- Se implementa Pattern Observer para que el portfolio se rebalancee automáticamente cuando cambia el precio de las acciones
- Se implementa un event bus en memory para que las stocks puedan emitir eventos cuando cambian de precio y los portafolios puedan actualizarse en consecuencia mediante el registry.

## Reflexiones de Bryan Aurelio

- Ordené un poco las carpetas y archivos para que quede más ordenado
- Se usó mucho más tiempo de lo esperado, pero la implementación es sólida (hombre feliz)
- No me dió la vida para añadir la validación de operación si el cliente es retail
- Fué un error no investigar el manejo de decimales, pero al menos aprendí la lección.
- Para la otra tocará tener algo de comer a la mano jajaja
