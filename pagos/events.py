import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payment_service.settings")

app = Celery(
    "payment_service",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)

# CELERY_EAGER=1 ejecuta las tareas en el mismo proceso (útil sin Redis).
app.conf.task_always_eager = os.getenv("CELERY_EAGER") == "1"


@app.task
def publicar_payment_completed(payment_id, tipo, referencia_id):
    # Evento definido por la guía: payment.completed
    print({
        "event": "payment.completed",
        "payment_id": payment_id,
        "tipo": tipo,  # "prima" | "indemnizacion"
        "referencia_id": referencia_id,  # id_poliza o id_siniestro
    })


@app.task
def publicar_payment_failed(payment_id, tipo, referencia_id):
    # Evento definido por la guía: payment.failed
    print({
        "event": "payment.failed",
        "payment_id": payment_id,
        "tipo": tipo,
        "referencia_id": referencia_id,
    })


@app.task
def consumir_claim_approved(claim_id, amount, method="transferencia"):
    # Evento consumido por Pagos: claim.approved -> ejecutar indemnización
    print({
        "event": "claim.approved",
        "claim_id": claim_id,
        "amount": amount,
    })

    import django
    django.setup()
    from .services import ejecutar_indemnizacion

    payout, _ = ejecutar_indemnizacion(claim_id, amount, method)
    return str(payout.id_payout)
