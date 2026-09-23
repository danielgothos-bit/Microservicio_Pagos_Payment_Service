import uuid

from django.db import models
from django.db.models import Q


PENDIENTE = "pendiente"
PAGADO = "pagado"
FALLIDO = "fallido"

STATUS_CHOICES = [
    (PENDIENTE, "Pendiente"),
    (PAGADO, "Pagado"),
    (FALLIDO, "Fallido"),
]

TARJETA = "tarjeta"
PSE = "pse"
TRANSFERENCIA = "transferencia"

METHOD_CHOICES = [
    (TARJETA, "Tarjeta"),
    (PSE, "PSE"),
    (TRANSFERENCIA, "Transferencia"),
]


class PremiumPayment(models.Model):
    """Cobro periódico de primas de una póliza."""

    id_pago = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_poliza = models.UUIDField()  # FK-ext -> Policy Service
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    due_date = models.DateField()
    paid_at = models.DateTimeField(blank=True, null=True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDIENTE)

    class Meta:
        db_table = "premium_payments"
        indexes = [
            models.Index(fields=["id_poliza"], name="idx_premium_payments_poliza"),
            models.Index(fields=["due_date"], name="idx_premium_payments_due_date"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="chk_premium_amount_positivo"),
            models.CheckConstraint(
                condition=Q(method__in=[TARJETA, PSE, TRANSFERENCIA]),
                name="chk_premium_method",
            ),
            models.CheckConstraint(
                condition=Q(status__in=[PENDIENTE, PAGADO, FALLIDO]),
                name="chk_premium_status",
            ),
        ]

    def __str__(self):
        return f"Prima {self.id_pago} - Póliza {self.id_poliza}"


class ClaimPayout(models.Model):
    """Pago de indemnización de un siniestro aprobado."""

    id_payout = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_siniestro = models.UUIDField()  # FK-ext -> Claims Service
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    paid_at = models.DateTimeField(blank=True, null=True)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default=TRANSFERENCIA)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDIENTE)

    class Meta:
        db_table = "claim_payouts"
        indexes = [
            models.Index(fields=["id_siniestro"], name="idx_claim_payouts_siniestro"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(amount__gt=0), name="chk_payout_amount_positivo"),
            models.CheckConstraint(
                condition=Q(status__in=[PENDIENTE, PAGADO, FALLIDO]),
                name="chk_payout_status",
            ),
        ]

    def __str__(self):
        return f"Indemnización {self.id_payout} - Siniestro {self.id_siniestro}"
