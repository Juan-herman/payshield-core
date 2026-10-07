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
