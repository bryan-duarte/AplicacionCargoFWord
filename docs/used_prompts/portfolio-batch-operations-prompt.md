---
use_case: Prompt usado para planificar los ajustes necesarios para la funcionalidad de batch operations. Se iterá con claude desiciones de la implementación, se lee el plan, se itera hasta lña implementación. Luego se revisa y se ajustan elemementos no bien escritos.
used_agent: Claude code con planning mode

---

Crea un nuevo campo en las operaciones de compra y de venta para generar un identificador único de batch de operaciones (batch uuid), este debe de ser generado en el portafolio y asignado a los schemas de compra y venta

Este será opcional, ya que se usará para indicar operaciones en batch.

Todos los stock operations que compartan un mismo hash se entienden como una operación atomica que debe ser resulta en completo o generar un proceso de rollback.
Como en operaciones de finanzas no hay rollbacks de base de dato, lo que corresponde es:

El Broker ahora debe de en los casos donde recibe el batch uuid, registrar esa operación en un dict interno, donde la llave será el uuid del batch y eso tendrá una lista con todas las operaciones de ese batch.

Así, el flujo ahora será:

Si llega una operación con batch uuid, guardo información de las operaciones en el dict interno donde la llave es el uuid del batch y dentor tiene otro diccionario con el uuid de la operción. como llave y ahí dentro ya sí el schema de la operación.

Al ejecutar correctamente una operación con batch uuid, actualizo el estado del schema que está en {batch uuid}.{operation uuid} la paso a sucess.

Así por todas las operaciones, en caso de que haya algun error, tambien actualiza el estado del schema, asignandole error.

Crea en los schemas de compra y de venta un metodo para en base a un schema de operación, obtener el schema rollback”. es decir, un metodo que al ejecutarlo en el schema de compra, genere el schema de venta que revierte la operación.

Así se puede obtener de esos schemas su homologo contrario.

El broker ahora tendrá un método que sea para ejecutar batch_rollback (debe estar en la interfaz), este recibe el uuid str y retorna True o False según si se logró el rollback completo o no.

Este recibe el uuid del batch

El broker revisa el batch en su dict interno, obtiene las operaciones que esten en el state de error

De esas operaciones obtiene el schema de operación de rollback

Y trata de ejecutar esas operaciones a forma de rollback. Debe al menos intentar 3 veces ejecutar el rollback de esas operaciones.

A medida que ejecuta los rollback debe de marcar esas operaciones como “rollback” true

este es un nuevo atributo que por default es false en todas las stocks operations.

Ahora que tendremos este metodo de rollback, este se debe de usar en el portafolio para las acciones de inicialización y de balanceo.

En caso de que el mismo metodo de rollback no se pueda ejecutar, el portfolio debe de quedar en un estado stale.

stale será un nuevo atributo de instancia, que es por default será false.

Este debe de ser validado en las operaciones que hace el portafolio, no se debe de poder comprar acciones a un portafolio si este está stale, añadir ese early return en los metodos de portoflio con su respectivo error de negocio

Implementa el plan de esta funcionalidad, preguntame cualqueir duda que tengas o punto que creas que hay una solución mejor en la implementación y que me puedas recomendar.