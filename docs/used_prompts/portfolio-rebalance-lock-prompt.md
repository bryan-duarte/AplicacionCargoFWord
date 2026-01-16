---

use_case: Prompt usado para planificar los ajustes necesarios para la funcionalidad de portfolio rebalance lock. Se iterá con claude desiciones de la implementación, se lee el plan, se itera hasta lña implementación. Luego se revisa y se ajustan elemementos no bien escritos.
used_agent: Claude code con planning mode

---

Estructura la implementaión de un sistema de estados para mi portfolio para evitar race conditions mientras se está ejecutando una rebalance de las stocks del portfolio.

Se debe de crear un lock, mediante algun tipo de estado interno de la clase o contextmanager de pyhton para que siempre se suelte este estado provisorio

Mientras el portfolio esté en rebalanceo no se puede ejecutar otro rebalanceo sobre la misma instancia de portafolio.

Si en el momento en que se está ejecutando un rebalance, otro rebalance quiere ejecutarse debe encontrarse con el lock y omitir el balanceo por ya estar uno en ejecución. Esto solo será omitido si es que hay un rebalance, pero este fué iniciado hace más de 6 horas (añadir este como atributo de instancia).

Eso indicará que el rebalanceo se quedó “pegado” o no se acutalizó el atributo en la clase en rebalanceos previos y como esta validación tiene este factor de tiempo, deberá limpiar lo relativo a estados de rebalance preivos y crear un nuevo estado de rebalanceo con la hora de incio de la que se está generando el proceso.

Así evitamos race conditions de multiples balanceos en paralelo y si un balanceo se queda pegado, se ignora por un ttl de expiración de tiempo para el lock desde que se comienza el balanceo.

Implementa esto, preguntame todas las desiciones que se deban de realizar a nivel de arquitectura de la implementación