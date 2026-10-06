# Microservicio de Pagos — Payment Service

Microservicio de InsureFlow definido en la sección 4.5 del documento de arquitectura.

## Responsabilidad

Procesar el cobro de primas y el pago de indemnizaciones aprobadas, integrándose con pasarelas de pago (adaptador en `pagos/gateways.py`).

## Tecnología

Python · Django REST Framework · PostgreSQL (`payment_db`) · Celery + Redis · Docker

## Modelo de datos (3FN, IDs UUID)

`premium_payments` y `claim_payouts` (amount > 0, method y status restringidos).

## Endpoints

```
POST /api/v1/pagos/primas — registrar cobro de prima
GET  /api/v1/pagos/primas/poliza/{id} — historial de pagos de una póliza
POST /api/v1/pagos/indemnizaciones — ejecutar pago de indemnización (409 si ya se pagó)
GET  /api/v1/pagos/indemnizaciones/siniestro/{id} — pagos de un siniestro
GET  /health — estado del servicio y de su base de datos
POST /api/v1/eventos — endpoint interno donde otros microservicios entregan eventos
```

## Eventos

Publica:
- payment.completed
- payment.failed

Consume:
- claim.approved

Los eventos se encolan con Celery/Redis y se entregan por HTTP al endpoint `/api/v1/eventos` de cada
suscriptor, con reintentos y backoff exponencial (módulo `comun/eventos.py`). Cada evento se procesa una
sola vez (idempotencia por `event_id`).

## Variables de entorno

- `DATABASE_URL`, `REDIS_URL`: base de datos y Redis propios
- `INTERNAL_TOKEN`: token compartido por todos los microservicios para los eventos
- `RUN_WORKER_IN_WEB=1`: corre el worker de Celery dentro del mismo contenedor (Render gratis)
- `SYNC_TIMEOUT`: timeout de las llamadas REST síncronas (3 s por defecto)
- `CLAIMS_SERVICE_URL`: microservicio de Siniestros
- `DOCUMENT_SERVICE_URL`: microservicio de Documentación
- `NOTIFICATION_SERVICE_URL`: microservicio de Notificaciones
- `ANALYTICS_SERVICE_URL`: microservicio de Analítica

Si una URL no está configurada, el servicio funciona en modo aislado (omite esa validación o ese evento).

## Ejecución local

```bash
docker compose up --build
```

El servicio queda en http://localhost:8001 y las migraciones se aplican solas al arrancar.

Pruebas:

```bash
docker compose exec payment_service python manage.py test pagos
```

## Despliegue en Render

En Render: **New → Blueprint** → conectar este repositorio → **Deploy Blueprint**.
El `render.yaml` crea el servicio web, su PostgreSQL y su Redis (plan gratis).
