from decimal import Decimal

from django.utils import timezone

from comun.eventos import publicar

from .models import PremiumPayment, ClaimPayout, PAGADO, FALLIDO
from .gateways import get_gateway


def _aplicar_resultado(pago, exito, tipo, referencia, extra=None):
    pago.status = PAGADO if exito else FALLIDO
    if exito:
        pago.paid_at = timezone.now()
    pago.save()

    publicar("payment.completed" if exito else "payment.failed", {
        "payment_id": pago.pk,
        "tipo": tipo,  # "prima" | "indemnizacion"
        "referencia_id": referencia[1],  # id_poliza o id_siniestro
        referencia[0]: referencia[1],
        "amount": pago.amount,
        "method": pago.method,
        "paid_at": pago.paid_at,
        **(extra or {}),
    })
    return pago


def registrar_cobro_prima(data):
    """Crea el cobro de prima y lo procesa en la pasarela."""
    pago = PremiumPayment.objects.create(**data)
    exito, _, _ = get_gateway().cobrar(str(pago.id_pago), pago.amount, pago.method)
    return _aplicar_resultado(pago, exito, "prima", ("id_poliza", pago.id_poliza))


def ejecutar_indemnizacion(id_siniestro, amount, method="transferencia", id_asegurado=None):
    """
    Ejecuta el pago de indemnización de un siniestro aprobado.
    Es idempotente: si el siniestro ya tiene un pago exitoso, no se paga dos veces.
    Retorna (payout, ya_pagado).
    """
    existente = ClaimPayout.objects.filter(id_siniestro=id_siniestro, status=PAGADO).first()
    if existente:
        return existente, True

    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValueError("El monto de la indemnización debe ser mayor que 0.")

    payout = ClaimPayout.objects.create(id_siniestro=id_siniestro, amount=amount, method=method)
    exito, _, _ = get_gateway().transferir(str(payout.id_payout), payout.amount, payout.method)
    extra = {"id_asegurado": id_asegurado} if id_asegurado else None
    return _aplicar_resultado(payout, exito, "indemnizacion", ("id_siniestro", payout.id_siniestro), extra), False
