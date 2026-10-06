import uuid
from unittest import mock

from rest_framework.test import APITestCase

from comun.eventos import INTERNAL_TOKEN

from .models import ClaimPayout, PAGADO, FALLIDO


@mock.patch("pagos.services.publicar")
class PagosTests(APITestCase):
    def test_registrar_prima_y_consultar_historial(self, publicar):
        poliza = uuid.uuid4()
        resp = self.client.post("/api/v1/pagos/primas", {
            "id_poliza": str(poliza),
            "amount": "150000.00",
            "due_date": "2026-10-01",
            "method": "pse",
        }, format="json")

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["status"], PAGADO)
        evento, data = publicar.call_args[0]
        self.assertEqual(evento, "payment.completed")
        self.assertEqual(data["tipo"], "prima")
        self.assertEqual(data["id_poliza"], poliza)

        resp = self.client.get(f"/api/v1/pagos/primas/poliza/{poliza}")
        self.assertEqual(len(resp.data), 1)

    def test_prima_con_metodo_invalido(self, publicar):
        resp = self.client.post("/api/v1/pagos/primas", {
            "id_poliza": str(uuid.uuid4()),
            "amount": "100",
            "due_date": "2026-10-01",
            "method": "efectivo",
        }, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data["code"], "VALIDATION_ERROR")

    def test_prima_con_monto_cero(self, publicar):
        resp = self.client.post("/api/v1/pagos/primas", {
            "id_poliza": str(uuid.uuid4()),
            "amount": "0",
            "due_date": "2026-10-01",
            "method": "tarjeta",
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_indemnizacion_no_se_paga_dos_veces(self, publicar):
        siniestro = str(uuid.uuid4())
        body = {"id_siniestro": siniestro, "amount": "5000000"}

        resp = self.client.post("/api/v1/pagos/indemnizaciones", body, format="json")
        self.assertEqual(resp.status_code, 201)

        resp = self.client.post("/api/v1/pagos/indemnizaciones", body, format="json")
        self.assertEqual(resp.status_code, 409)

        resp = self.client.get(f"/api/v1/pagos/indemnizaciones/siniestro/{siniestro}")
        self.assertEqual(len(resp.data), 1)

    @mock.patch.dict("os.environ", {"PAYMENT_GATEWAY_FAIL": "1"})
    def test_indemnizacion_fallida_publica_payment_failed(self, publicar):
        resp = self.client.post("/api/v1/pagos/indemnizaciones", {
            "id_siniestro": str(uuid.uuid4()),
            "amount": "1000",
        }, format="json")

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["status"], FALLIDO)
        self.assertEqual(publicar.call_args[0][0], "payment.failed")

    def test_consumir_claim_approved(self, publicar):
        siniestro = str(uuid.uuid4())
        asegurado = str(uuid.uuid4())
        resp = self.client.post("/api/v1/eventos", {
            "event": "claim.approved",
            "data": {"id_siniestro": siniestro, "amount": "2500000", "id_asegurado": asegurado},
        }, format="json", HTTP_X_INTERNAL_TOKEN=INTERNAL_TOKEN)

        self.assertEqual(resp.data["status"], "processed")
        self.assertEqual(ClaimPayout.objects.filter(id_siniestro=siniestro, status=PAGADO).count(), 1)
        self.assertEqual(publicar.call_args[0][1]["id_asegurado"], asegurado)

    def test_health(self, publicar):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
