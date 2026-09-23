from decimal import Decimal

from django.utils import timezone

from .models import PremiumPayment, ClaimPayout, PAGADO, FALLIDO
from .gateways import get_gateway
from .events import publicar_payment_completed, publicar_payment_failed


def _aplicar_resultado(pago, exito, tipo, referencia_id):
    pk = str(pago.pk)
    if exito:
        pago.status = PAGADO
        pago.paid_at = timezone.now()
        pago.save()
        publicar_payment_completed.delay(pk, tipo, str(referencia_id))
    else:
        pago.status = FALLIDO
        pago.save()
        publicar_payment_failed.delay(pk, tipo, str(referencia_id))
    return pago


def registrar_cobro_prima(data):
    """Crea el cobro de prima y lo procesa en la pasarela."""
    pago = PremiumPayment.objects.create(**data)
    exito, _, _ = get_gateway().cobrar(str(pago.id_pago), pago.amount, pago.method)
    return _aplicar_resultado(pago, exito, "prima", pago.id_poliza)


def ejecutar_indemnizacion(id_siniestro, amount, method="transferencia"):
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
    return _aplicar_resultado(payout, exito, "indemnizacion", payout.id_siniestro), False
