El punto está en considerar lo NO evidente que envuelve el caso de uso real como lo sería en FWord como tal, literal lo primero fué un bueeeeeeeeen tiempo en investigar sobre particularidades del negocio y FWord, hagamos una simulación.


CASO 
Primer día: Hola Bryan, bienvenido a FWord te sumaras al equipo que está en la funcionalidad de “FWord malabarista” que balancea portafolios, vaya y aporte pues.

Todo esto sería en lo que me aportaría a la conversación y en algunos casos detallo mi aproach frente a los puntos.

Razonamiento
<…deep human thinking mode>

Primeras dudas:
1- Comisiones del broker. ¿Qué broker usa FWord?
2-¿Puedo comprar fracciones de acciones?
	FWord usa Alpaca Securities (Buen nombre), que sí permite compra fraccionada, y dice que no cobra comisiones, al parecer tiene una api en condiciones.
3- Impuestos a la renta de utilidades de capital del país Chile, México afectan al caso de uso?
Claro pues muchacho, SII y SAT todo lo ven
Opinión mía ante el equipo: Quien activa el feature debe saber el impacto tributario, pero hay que hacerle la vida sencilla respecto a la recopilación de los ingresos y pérdidas obtenidas de estas ventas auto ejecutadas de sus assets.

Adicionales: 
-El mínimo de un asset en FWord acciones es de 1 dolar.
-El tipo de cuenta en el broker probablemente sea de tipo margen, no cash.
La cuenta de margen permite el "rebalanceo atómico": vender Meta y comprar Apple instantáneamente, usando el dinero de la venta antes de que se liquide oficialmente.

Este tipo de cuenta nos lleva a “La Big Mamma Regla”: 
Si una cuenta tiene menos de $25,000 USD (Cuenta Retail), no puede realizar más de 3 "Day Trades" (comprar y vender la misma acción el mismo día) en un periodo de 5 días hábiles.

Opinión mía ante el equipo:  Gente, para no rebalancear constantemente hay que tener un trigger de rebalanceo y manejar los límites de cuentas retail en el broker. podríamos usar:
-% de variación en participación del portafolio que ‘triggeree’ el rebalanceo del portafolio.
Tipo, rebalancear diferencias de solo 1% o más

<…/deep human thinking mode>




Decisiones de equipo:

El rebalanceo del portafolio es algo que ocurriría en segundo plano?, “Tu portafolio se rebalancea mientras ves Netflix” o sería un feature de “Ejecutar balanceo” y que el usuario ejecuta.
Opinión mía ante el equipo: Full con el auto rebalanceo mientras ves netflix.

A nivel sistema, al haber un cambio en el atributo precio de una acción, debe de lanzar el evento de evaluar (o no) los portafolios que contienen esa acción para rebalancearlos si corresponde.

Que opciones tiene alpaca para no tener que hacer una petición a su endpoint a cada rato ? tiene un webhook que me notifique de algún cambio significativo en el precio de alguna acción?

Alguien tiene la data histórica de cambios de precio que tienen las acciones que tenemos disponibles en el feature? así podríamos definir tiempos de chequeo del balanceo basado en el historico. [-Bryan procede a conseguirse la data en la deepweeb si es que FWord no la tiene-]

Vi que alpaca tiene un websocket para suscribirme a eventos cada 1 minuto
Pero, según la propuesta de valor del feature vale la pena? sí es que sí, consideremos el costo de escalar eso a nivel servidores segun la cantidad de variedad de assets y de portafolios manejados.

EDGE CASE: Si a la gente del reddit WallStreet Bets le da por hacer un pump and dump en una acción, nuestro sistema debería reaccionar a esto o debe de omitirlo de alguna manera mágica?
	Opinión mía ante el equipo: Pos sí, sí debería afectar. claramente no es grato, pero es parte de investir y el módulo de trading.


Requerimientos de la implementación:

La arquitectura debe (IMO) de ser basada en eventos, cambios en el precio significativos que veamos en las acciones ejecutará evaluar rebalanceos.Debe de haber un webshocket que esté escuchando cada 1 segundo las variaciones en el precio de las acciones en el portafolio, debemos escuchar solo los symbols en cartera, no todas las acciones del brokers.

Luego de que haya un cambio significativo en la acción, se debe de disparar la evaluación de cambios de portafolio, si al evaluar da como algo a considerar, si se debe ejecutar el balanceo para mantener los porcentajes de distribución de acciones en la colección de acciones.

Manejar thresholds para no sobre evaluar balanceos.
	Cada cuánto porcentaje de variación del precio de una acción evaluamos si hay que rebalancear? obtener de config, usar 1%





