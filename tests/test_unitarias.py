"""Pruebas unitarias: una unidad de lógica de negocio aislada; las dependencias externas se simulan con mocks."""
import uuid
from decimal import Decimal
from unittest import mock

from django.test import TestCase

from pagos.services import ejecutar_indemnizacion


class PagosUnitTests(TestCase):
    @mock.patch("pagos.services.publicar")
    @mock.patch("pagos.services.get_gateway")
    def test_pasarela_rechaza_y_se_publica_payment_failed(self, get_gateway, publicar):
        get_gateway.return_value.transferir.return_value = (False, None, "Fondos insuficientes")
        payout, ya_pagado = ejecutar_indemnizacion(uuid.uuid4(), Decimal("1500000"))
        self.assertEqual(payout.status, "fallido")
        self.assertFalse(ya_pagado)
        self.assertEqual(publicar.call_args[0][0], "payment.failed")

    @mock.patch("pagos.services.publicar")
    @mock.patch("pagos.services.get_gateway")
    def test_rechaza_monto_invalido_sin_llamar_a_la_pasarela(self, get_gateway, publicar):
        with self.assertRaises(ValueError):
            ejecutar_indemnizacion(uuid.uuid4(), Decimal("0"))
        get_gateway.assert_not_called()
        publicar.assert_not_called()
