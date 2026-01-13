



# Challenge cargo de Dev

```bash
uv run main.py
```
Al ejecutar cambio de precio en las acciones, se puede observar como el portfolio se rebalancea automáticamente.

Portafolio inicial:

Portfolio final:

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
