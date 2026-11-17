"""Prueba de integración: endpoint + lógica de negocio + base de datos funcionando juntos."""
import uuid
from unittest import mock

from rest_framework.test import APITestCase

from pagos.models import PremiumPayment


@mock.patch("pagos.services.publicar")
class PagosIntegracionTests(APITestCase):
    def test_registrar_cobro_de_prima_y_consultar_historial(self, publicar):
        poliza = str(uuid.uuid4())
        resp = self.client.post("/api/v1/pagos/primas", {"id_poliza": poliza, "amount": "210000", "due_date": "2026-11-01",
                                                         "method": "pse"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["status"], "pagado")
        self.assertTrue(PremiumPayment.objects.filter(id_poliza=poliza, status="pagado").exists())
        self.assertEqual(len(self.client.get(f"/api/v1/pagos/primas/poliza/{poliza}").data), 1)
        self.assertEqual(publicar.call_args[0][0], "payment.completed")
