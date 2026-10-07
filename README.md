# PayShield Core - Secure Payment Infrastructure Lab

# PayShield Core - Fintech Security & Infrastructure Hardening

PayShield Core es un entorno de microservicios transaccionales desarrollado para modelar, auditar y mitigar vectores de ataque críticos en aplicaciones fintech. 

El proyecto implementa una arquitectura defensiva bajo el principio de **Defensa en Profundidad** y segmentación de red **Zero Trust**, complementada con telemetría forense, mitigaciones de Capa 7 y herramientas automatizadas de correlación de eventos mapeadas contra el marco **MITRE ATT&CK**.

---

## 🏗 Arquitectura de Red y Segmentación

El sistema desacopla los servicios en múltiples redes lógicas dentro de Docker, asegurando que la persistencia permanezca completamente aislada del exterior:

```text
[ Tráfico Externo / Clientes ]
              │ (Puerto 80)
              ▼
   ┌──────────────────────┐
   │ Nginx Reverse Proxy  │ ──> Red: dmz_net (Front-facing)
   └──────────────────────┘
              │ (Proxy Pass / Rate Limiting)
              ▼
   ┌──────────────────────┐
   │ FastAPI Backend App  │ ──> Conectado a dmz_net y internal_net
   └──────────────────────┘
              │ (Query SQL / SQLAlchemy / Conexión directa)
              ▼
   ┌──────────────────────┐
   │ PostgreSQL Database  │ ──> Red: internal_net (internal: true, sin puertos expuestos)
   └──────────────────────┘
