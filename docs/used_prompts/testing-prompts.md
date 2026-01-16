---
use_case: Iteración para estructura base de tests. Se ejecuta el orquestador con el command y diferentes arguments según los tests a añadir. Es desición del usuario (Hola, yo) los detalles de la solicitud que luego el orquestador genera con el equipo de subagents de testing.
used_agent: Claude code command (en el folder .claude disponible) con orquestación de subagents enfocados en generar y validar tests.

---

# Generación base: prompt de iteración para estructura
Queiro que revises mi implementación de mi clase portfolio y sus clases asociadas

Queiro estructurar mi suite de tests inicial, quiero que identifiques las entidades claves que deberían ser creadas como fixtures para estrucutrar los tests y que elementos claves de la implementación se deben de testear para proteger la implementación en sus casos de negocios core. Yo te indicaré algunos que sí o sí deben estar:
    Test a allocation finales luego de rebalanceo simple
    Test a allocation finales luego de rebalanceo multiple en paralelo con mucha carga
    Test a allocation finales luego de rebalanceo con cambios de precios extremos
    Test a lock de rebalance que evita race conditions
    Test a proceso de ejecución de rollbacks meidante las batch operations que usan el uuid


# Prompt que ayuda a validar si quedan puntos ciegos:
    NOTA: Esto no es editar, sino que voy pidiendo reportes de los asserts, para ver si algo se me escapa en la implementación (este prompt funciona la raja en claude code, recomendadisimo)

    Queiro que ejecutes un analisis rapido en forma de paralel tasks en mi suite de tests, estas ejecuciones paralelas deben de revisar los assert de los tests y
    validar si lo que revisar realmente se condice con lo que debe de validar el test, cada paralel tasks debe de evaluar: 
        los assert de este test siguen la convención AAA? 
        revisan lo que deben revisar en base a la implementación testeada? 
        esta validación realmente evitaría que la pieza de código a testear genere un potencial bug?
        el test genera un side affect que pueda afectar la ejecución de los otros ?
        el test implementa una correcta dependency inyection para testear la pieza de software de la forma en que debe ser testeada?
    
    Ejecuta esto por cada test y dame un reporte unificado 

# Buscar puntos duplicados o depurables
Revisa con varios paralel taks que se podría simplificar en mi suite de tests, quiero evitar complejidad innecesaria sin perder calidad, que podría simplemente simplificar? 

    Aquí muchas cosas en el reporte seran bobadas, pero siempre sale alguna cosita que sí vale la pena.

# Iterar, intervenir, modificar en loop.