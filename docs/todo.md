You’re building a portfolio management module, part of a personal investments and trading app
Construct a simple Portfolio class that has a collection of Stocks. Assume each Stock has a “Current Price” method that receives the last available price. Also, the Portfolio class has a collection of “allocated” Stocks that represents the distribution of the Stocks the Portfolio is aiming (i.e. 40% META, 60% APPL)
Provide a portfolio rebalance method to know which Stocks should be sold and which ones should be bought to have a balanced Portfolio based on the portfolio’s allocation.
Add documentation/comments to understand your thinking process and solution
Important: If you use LLMs that’s ok, but you must share the conversations.



# Dominio

## Clase Stock
    - [X] Asignar un symbol (AAPL, META) y un precio default.
    - [ ] Implementar método `current_price` para actualizar precio desde el último valor.
    - [ ] Evaluar variación porcentual > 1% para emitir evento de revisión del portafolio.
    - [ ] Emitir evento para side effects cuando la variación absoluta supere ±1%. (Dejar en Config)

## Clase Portfolio
    - [X] Validar que el valor total sea ≥ 1 USD.
    - [X] Asignar distribución de stocks en porcentajes al crear el portafolio.
    - [X] Asignar monto inicial y comprar acciones iniciales en `__init__` según distribución.
    - [X] Implementar métodos:
      - [X] Comprar acciones (floats con al menos 3 decimales, permitir fracciones).
      - [X] Vender acciones (floats con al menos 3 decimales, permitir fracciones).
      - [X] Simular precios de mercado con un diccionario de precios.

    - [X] Crear `allocated_stock` (symbols + porcentajes) y reflejar allí los stocks que tiene el portafolio.
    - [ ] Implementar método `rebalance` para ajustar compras/ventas y recuperar distribución inicial.
    - [ ] Calcular valor total y clasificar cliente (retail si < 25,000 USD).
    - [ ] Respetar restricción retail:
      - [ ] Limitar a máximo 3 day trades en 5 días hábiles.
      - [ ] Registrar compras/ventas para auditar day trades.
- [ ] Elemento clave del rebalance
  - [ ] Ejecutar rebalance solo si una acción varió > 1% y eso generó dispersión > 2% en la distribución.
  - [ ] Manejar caso de portafolio 40/60 (AAPL, META) donde un activo crece y excedente debe venderse para volver a `allocated_stock`.

- [X] Acción de comprar o vender acciones
  - [X] Definir DTO con:
    - [X] Tipo (compra/venta).
    - [X] Cantidad (float ≥ 3 decimales).
    - [X] Symbol.
    - [X] Precio al momento de la operación.

# Config
  - [X] Crear archivo de settings para constantes configurables.
  - [ ] Definir umbral 1% para eventos de revisión.
  - [ ] Definir umbral 2% para eventos de rebalanceo.

# Errores de negocio
  - [X] Evitar que el valor total de una acción sea < 1 USD.
  - [X] Error al comprar acciones
  - [X] Error al vender acciones