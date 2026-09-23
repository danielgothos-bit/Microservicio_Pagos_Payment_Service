from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import PremiumPayment, ClaimPayout
from .serializers import PremiumPaymentSerializer, ClaimPayoutSerializer
from .services import registrar_cobro_prima, ejecutar_indemnizacion


@api_view(["GET"])
def health(request):
    try:
        connection.ensure_connection()
        db = "ok"
    except Exception:
        db = "error"

    codigo = status.HTTP_200_OK if db == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response({"service": "payment_service", "status": db, "database": db}, status=codigo)


@api_view(["POST"])
def primas(request):
    serializer = PremiumPaymentSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    pago = registrar_cobro_prima(serializer.validated_data)

    return Response(
        PremiumPaymentSerializer(pago).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def primas_por_poliza(request, id):
    pagos = PremiumPayment.objects.filter(id_poliza=id).order_by("-due_date")
    return Response(PremiumPaymentSerializer(pagos, many=True).data)


@api_view(["POST"])
def indemnizaciones(request):
    serializer = ClaimPayoutSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    payout, ya_pagado = ejecutar_indemnizacion(
        data["id_siniestro"],
        data["amount"],
        data.get("method", "transferencia"),
    )

    if ya_pagado:
        return Response(
            {"code": "ALREADY_PAID", "message": "El siniestro ya tiene una indemnización pagada."},
            status=status.HTTP_409_CONFLICT,
        )

    return Response(
        ClaimPayoutSerializer(payout).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def indemnizaciones_por_siniestro(request, id):
    payouts = ClaimPayout.objects.filter(id_siniestro=id).order_by("-paid_at")
    return Response(ClaimPayoutSerializer(payouts, many=True).data)
