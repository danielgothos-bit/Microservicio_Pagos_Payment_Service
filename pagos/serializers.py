from rest_framework import serializers
from .models import PremiumPayment, ClaimPayout


class PremiumPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PremiumPayment
        fields = [
            "id_pago",
            "id_poliza",
            "amount",
            "due_date",
            "paid_at",
            "method",
            "status",
        ]
        read_only_fields = ["id_pago", "paid_at", "status"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor que 0.")
        return value


class ClaimPayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimPayout
        fields = [
            "id_payout",
            "id_siniestro",
            "amount",
            "paid_at",
            "method",
            "status",
        ]
        read_only_fields = ["id_payout", "paid_at", "status"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor que 0.")
        return value
