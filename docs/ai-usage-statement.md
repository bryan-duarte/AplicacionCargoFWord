El desarrollo de la aplicación se dividió en 4 etapas:


I - Época de Piedra:
    descripción: setup de estructura general del proyecto (Streaming de 5 horitas), esto incluye:
        -Se implementa estructura general del desafió a nivel de componentes principales.
        -Se diseña algoritmo de rebalanceo.
        -Se implementa flujo con eventos de cambio de precio.
    
    USO DE IA EN ESTA ETAPA:
        -Bajo, solo este prompt 
            /prompts/event-handler-prompt.md para 
        debbug de elemento bloqueante en implementación.

II - Él renacimiento:
    descripción: despues de reflexionar lo mala que era la implementación previa (el niño 5 horas) respecto a la lógica de negocio clave, se mejoran algunos elementos subyacentes previos a cubrir los componentes clave.

        -Se implementa configuración global de profundidad de decimales según hallazgos en documentación de Alpaca (ver link: https://alpaca.markets/learn/fractional-shares-api )
        -Se incorporan funciones helper en utils para evitar problemas en operaciones con valores de tipo Decimal.
        -Se mueve el FAKE MARKET a utils al ser un elemento utilitario con neto foco en el demo del rebalanceo.
        -Se implementa config general de la aplicación (settings), con configs agrupadas por contexto de uso.
        -Se añaden errores de lógica principal en todos los modulos asociados.
        -Se añade uuid para tracing de operaciones de compra y venta realizadas con el broker.
        -Se incorpora schema PortFolioConfig para validar en capa de DTOs todas las reglas de negocios asocidas a la instanciación del portafolio y no saturar en su constructor.
        -Se añaden validación de instanciación de clase Stock con errores en le módulo respectivo.
        -Se crea CLAUDE.MD y AGENTS.md para mejor contexto al agente en solicitudes.
    
    USO DE IA EN ESTA ETAPA:
        -

III-Modernismo:
    descripción: Aquí to bajo el detalle completo de la implementación a realizar con todos los detalles tecnicos de ejecución que debería realizar el agente, describo flujos, modificaciones puntuales a realizar puntuales y uso el planning mode de Claude code para ver puntos ciegos, reviso el plan, solicito ajustes al plan si corresponde y le pido ejecutar el plan.
    Luego sobre lo que hizo, soy generando modificaciones de limpieza de comentarios, cosas que no se entienden, etc.

    Así fué como bajé las dos funcionalidades clave de negocio en el broker y portafolio.

    USO DE IA EN ESTA ETAPA:
        -Principalmente dos promps:
            docs/used_prompts/portfolio-batch-operations-prompt.md
            docs/used_prompts/portfolio-rebalance-lock-prompt.md


IV: Post modernismo:
    descripción: Usé varios prompts para recibir sugerencias de estructuras base del pool de tests, pero con preindicaciones mias sobre que casos de negocios se les debe de dar foco en la suit de test. sobre esto se reciben test, se ajustan, se limpian, se van iterando hasta tener una implementación de test que realmente testee la lógica de negocio y que sean isolated para no generar sideeffects
    
    USO DE IA EN ESTA ETAPA:
         -Principalmente los prompts en: docs/used_prompts/testing-prompts.md


