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


# Test másivo de portfolios
Esto lo ejecuté con el distributed_task command : .claude/commands/distributed_task.md

Tipo: /distributed_task "{Todo este prompt de abajo como argumento}"

Prompt:
Queiro que añadas un nuevo test a mi suite de test, quiero que añadas un test que prueba el funcionamiento de mi implementación a gran escala con muuuuuchos portafolios en un registry.

El registry al hay que hacer que sea por default, pero posible de hacer overwrite, similar a lo que ocurre con el market, que es por default el global, pero inyectable uno isolated

El test no debe usar registry global del main de la aplicaicón, sino uno que se instancia y se inyecta en la clase portafolio de los portafolios que se van a instanciar

Crea un market solo para este test, totalmente isolated con varias stocks ficticias, minimo 50, donde los portafolios se van a crear aleatoriamente con cantidades aleatorias entre 10 a 50 stocks.

Donde tambien debes de simular una distribución aleatoria para cada tipo de portafolio, donde esta distribución aleatoria tambien debe de sumar 100 en cada portafolio.

Es crear multiples tipos de portafolios con distribuciones muy diferentes, todos sumando un total de 100% de allocation inicial

Luego las stocks del fake market isolated deben de ir variando de forma ascendente y descendenete en rangos de -3 a +3 porciento

Debes de generar 10 cambios aleatorios en 10 stocks aleatorias.

Luego generar mediante el registry un update de los portfolios que tienen las stocks que cambiaron de precio.

Aquí hay que hacer un assert para validar que todos los portafolios estan balanceados.

Luego generar otros cambios aleatorios,m20 acambios aleatorios esta vez en 20 stocks aleatorias y generar el rebalance de los portfolios que tienen esas stocks.

Aquí hay que hacer otro assert para validar que todos los portafolios estan balanceados.

Luego ya 100 cambios aleatorios en todas las stocks, rebalancear todos los portfolios instanciados en el test.

Y validar con otro assert que todos los portafolios siguen totalmente balanceados.

Usa el test-writter subagent para escribir el test tests, 
luego valida con el test-validator subagent el test
luego genera un paralel task que debe de:
       Validar que el test sigue el patron AAA
       Validar que el test prueba lo que debe probar y es totalmente isolated con las respectivas depenedency inyection
       Validar que todas la sintaxis es simple, clara, entendible y sin comentarios innecesarios o sobrecomplejdiad

En caso de que no se cumpla alguna de esas cosas, ajustar, hasta que el test pase la validación de esta ejecución de paralel Task
Validar finanlmente con el subagent el test creado.

Sigue todo esto paso a paso según lo indicado
