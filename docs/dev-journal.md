# Diario Técnico de Aprendizaje y Desarrollo (PayShield Core)

### Hito 1: Despliegue de Infraestructura, Segmentación y Trazabilidad
* **Fecha:** Octubre 2026
* **Objetivo:** Implementar la infraestructura base de un microservicio transaccional con segmentación estricta de red y hardening en contenedores.

#### Controles de Seguridad Implementados:
1. **Defensa en Profundidad y Aislamiento de Red:**
   - La base de datos reside en `internal_net` con `internal: true`, sin pasarela de salida a internet ni exposición de puertos al host.
   - El proxy perimetral Nginx no comparte red con la base de datos; las pruebas de resolución y conectividad directa (`ping db`) fallan por diseño.
2. **Hardening de la Capa de Aplicación:**
   - Contenedor de la API ejecutado bajo un usuario sin privilegios (`appuser`, UID 8888) en Python 3.11-slim.
   - Ocultamiento de cabeceras de versión en Nginx (`server_tokens off`).
3. **Atomicidad y Telemetría Contable:**
   - Transacciones implementadas con bloqueo pesimista (`SELECT ... FOR UPDATE`) para mitigar condiciones de carrera (Race Conditions / Double Spending).
   - Telemetría estructurada capturando la IP de origen propagada por el proxy (`X-Real-IP`).

#### Análisis de Incidencia / Troubleshooting Documentado:
- **Síntoma:** Error `psql: error: /docker-entrypoint-initdb.d/init.sql: Permission denied` durante la inicialización de PostgreSQL, provocando `relation "accounts" does not exist`.
- **Causa Raíz:** Permisos de archivo restrictivos en el host que impedían la lectura al UID de PostgreSQL dentro del contenedor.
- **Remediación:** Asignación de permisos `chmod 644 db/init.sql` y purga del volumen (`docker compose down -v`) para forzar la reejecución limpia del script DDL.

### Hito 2: Simulación de Ataques y Extracción de Telemetría
* **Fecha:** Octubre 2026
* **Objetivo:** Ejecutar vectores de ataque controlados para auditar la resistencia de la API y comprobar la calidad de los logs para investigaciones forenses.

#### Conclusiones Técnicas:
1. **Robustez de Entrada:** La validación estricta de datos (Pydantic) evitó que cargas útiles con montos negativos alcanzaran la capa transaccional.
2. **Vulnerabilidad Identificada:** Se detectó la viabilidad de enumeración de cuentas por falta de control de acceso en la consulta de saldo y ausencia de limitación de tasa (Rate Limiting).
3. **Documentación:** Se generó el reporte formal de incidente `docs/incident-reports/IR-2026-001.md` estructurado bajo la taxonomía MITRE ATT&CK.

### Hito 3: Endurecimiento Perimetral con Rate Limiting en Nginx
* **Fecha:** Octubre 2026
* **Objetivo:** Mitigar ataques de fuerza bruta y barridos automatizados limitando la tasa de peticiones en el reverse proxy.

#### Implementación y Validación Técnica:
1. **Configuración de Rate Limiting:**
   - Se configuró la directiva `limit_req_zone $binary_remote_addr zone=api_limit:10m rate=5r/s`.
   - Se estableció un buffer de ráfaga con `burst=5 nodelay` y código de estado explícito `limit_req_status 429`.
2. **Validación de Telemetría Defensiva:**
   - La suite de pruebas activó el descarte de tráfico a partir de la ráfaga del Vector 4.
   - Nginx registró `limiting requests, excess: 5.030 by zone "api_limit"` y respondió con código HTTP `429 Too Many Requests`.
   - Se comprobó que el tráfico abusivo no impacta en el microservicio interno (`payshield-api`), reduciendo la superficie de ataque y el consumo de recursos.

### Hito 4: Mitigación Definitiva de Enumeración mediante Autenticación
* **Fecha:** Octubre 2026
* **Objetivo:** Remediar la fuga de información (IR-2026-001) exigiendo credenciales en los endpoints sensibles.

#### Implementación y Verificación:
1. **Control Criptográfico/Acceso:**
   - Se integró el esquema `APIKeyHeader` (`X-API-Key`) protegiendo `/api/v1/balance/{username}` y `/api/v1/transfer`.
   - Consultas no autenticadas son rechazadas inmediatamente con código HTTP `401 Unauthorized`.
2. **Defensa en Profundidad Completa:**
   - Capa 1: Nginx limita el caudal de peticiones y oculta metadatos de versión.
   - Capa 2: FastAPI exige autenticación por cabecera y valida esquemas estrictos con Pydantic.
   - Capa 3: PostgreSQL permanece aislado en red interna (`internal: true`) sin puertos expuestos.
