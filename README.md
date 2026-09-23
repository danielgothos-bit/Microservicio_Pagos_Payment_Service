# Microservicio de Pagos — Payment Service

Implementación del microservicio de Pagos definido en la guía de InsureFlow.

## Responsabilidad

Gestionar:
- el cobro periódico de primas de las pólizas;
- el pago de indemnizaciones de siniestros ya aprobados;
- la integración con pasarelas de pago y transferencia bancaria (adaptador en `pagos/gateways.py`).

## Tecnología

- Python
- Django REST Framework
- PostgreSQL (`payment_db`)
- Celery
- Redis
- Docker

## Modelo de datos (3FN)

`premium_payments`: id_pago (PK, UUID), id_poliza (FK-ext, UUID), amount, due_date, paid_at, method, status

`claim_payouts`: id_payout (PK, UUID), id_siniestro (FK-ext, UUID), amount, paid_at, method, status

Restricciones: `amount > 0`, `method IN ('tarjeta','pse','transferencia')`,
`status IN ('pendiente','pagado','fallido')`.

Índices: `idx_premium_payments_poliza`, `idx_premium_payments_due_date`, `idx_claim_payouts_siniestro`.

## Endpoints definidos

POST /api/v1/pagos/primas
GET  /api/v1/pagos/primas/poliza/{id}
POST /api/v1/pagos/indemnizaciones
GET  /api/v1/pagos/indemnizaciones/siniestro/{id}
GET  /health

Ejemplo — registrar cobro de prima:

```json
POST /api/v1/pagos/primas
{
  "id_poliza": "8f1c2e4a-1b2c-4d5e-9f00-123456789abc",
  "amount": "150000.00",
  "due_date": "2026-10-01",
  "method": "pse"
}
```

Ejemplo — ejecutar pago de indemnización:

```json
POST /api/v1/pagos/indemnizaciones
{
  "id_siniestro": "3a7d9b10-2c4e-4f6a-8b1c-abcdef012345",
  "amount": "5000000.00",
  "method": "transferencia"
}
```

Si el siniestro ya tiene una indemnización pagada responde `409 ALREADY_PAID` (no se paga dos veces).

## Eventos

Consume:
- claim.approved (tarea `pagos.events.consumir_claim_approved`, argumentos: `claim_id`, `amount`)

Publica:
- payment.completed
- payment.failed

## Ejecución

```bash
docker compose up --build
```

En otro terminal:

```bash
docker compose exec payment_service python manage.py migrate
```

El servicio queda disponible en el puerto **8001** (para no chocar con Peritaje, que usa el 8000).

## Ejecución sin Docker (desarrollo local)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
set USE_SQLITE=1
set CELERY_EAGER=1
python manage.py migrate
python manage.py runserver 8001
```

Pruebas:

```bash
python manage.py test pagos
```

Variable `PAYMENT_GATEWAY_FAIL=1`: fuerza a la pasarela simulada a rechazar los pagos (para probar `payment.failed`).
