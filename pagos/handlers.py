"""Eventos que consume el microservicio de Pagos (sección 4.5)."""
from .services import ejecutar_indemnizacion


def on_claim_approved(data):
    # Siniestros aprobó la indemnización: se ejecuta el pago (paso 12 del diagrama de secuencia).
    ejecutar_indemnizacion(
        data["id_siniestro"],
        data.get("amount") or data.get("estimated_amount"),
        data.get("method", "transferencia"),
        id_asegurado=data.get("id_asegurado"),
    )


HANDLERS = {
    "claim.approved": on_claim_approved,
}
