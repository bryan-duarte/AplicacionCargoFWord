## 🎥 Resolviendo desafio en vivo (Dar click y manda al video)

[![Ver el video en YouTube](https://img.youtube.com/vi/bdwrvlV7wQ8/maxresdefault.jpg)](https://youtu.be/bdwrvlV7wQ8)

https://youtu.be/bdwrvlV7wQ8

## Challenge cargo de Dev

```bash
uv run main.py
```
Al ejecutar cambio de precio en las acciones, se puede observar como el portfolio se rebalancea automáticamente.

Portafolio inicial:

Inversión inicial: 10000
Distribución de cada una 

| Stock | Porcentaje | Precio |
| :--- | :--- | :--- |
| **AAPL** | 40% | 250 |
| **META** | 20% | 150 |
| **MSFT** | 40% | 600 |

<img width="485" height="437" alt="antes-de-alertas" src="https://github.com/user-attachments/assets/f88626db-97ad-41d9-9bf6-e65307963292" />

Cambios en precios:

| Stock | % Cartera | Precio Inicial | Cambio en Precio |
| :--- | :--- | :--- | :--- |
| **AAPL** | 40% | 250 | 200 |
| **META** | 20% | 150 | 300 |
| **MSFT** | 40% | 600 | 900 |

Portfolio final:

Ante cada cambio de precio el sistema reaccionó y ejecutó compras y ventas para mantener la distribución

<img width="434" height="218" alt="image" src="https://github.com/user-attachments/assets/6b70efc4-8bf5-4e6b-8477-127a6cf4960f" />

El portafolio tiene un valor superior (13248) , pero mantiene su distribución

<img width="758" height="444" alt="despues-de-cambios" src="https://github.com/user-attachments/assets/49b5e247-2ec7-4d42-87f2-ee1745e1e7e4" />


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
