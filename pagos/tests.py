import uuid
from unittest import mock

from rest_framework.test import APITestCase

from .models import ClaimPayout, PAGADO, FALLIDO


@mock.patch("pagos.services.publicar_payment_failed.delay")
@mock.patch("pagos.services.publicar_payment_completed.delay")
class PagosTests(APITestCase):
    def test_registrar_prima_y_consultar_historial(self, completed, failed):
        poliza = uuid.uuid4()
        resp = self.client.post("/api/v1/pagos/primas", {
            "id_poliza": str(poliza),
            "amount": "150000.00",
            "due_date": "2026-10-01",
            "method": "pse",
        }, format="json")

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["status"], PAGADO)
        completed.assert_called_once()

        resp = self.client.get(f"/api/v1/pagos/primas/poliza/{poliza}")
        self.assertEqual(len(resp.data), 1)

    def test_prima_con_metodo_invalido(self, completed, failed):
        resp = self.client.post("/api/v1/pagos/primas", {
            "id_poliza": str(uuid.uuid4()),
            "amount": "100",
            "due_date": "2026-10-01",
            "method": "efectivo",
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_prima_con_monto_cero(self, completed, failed):
        resp = self.client.post("/api/v1/pagos/primas", {
            "id_poliza": str(uuid.uuid4()),
            "amount": "0",
            "due_date": "2026-10-01",
            "method": "tarjeta",
        }, format="json")
        self.assertEqual(resp.status_code, 400)

    def test_indemnizacion_no_se_paga_dos_veces(self, completed, failed):
        siniestro = str(uuid.uuid4())
        body = {"id_siniestro": siniestro, "amount": "5000000"}

        resp = self.client.post("/api/v1/pagos/indemnizaciones", body, format="json")
        self.assertEqual(resp.status_code, 201)

        resp = self.client.post("/api/v1/pagos/indemnizaciones", body, format="json")
        self.assertEqual(resp.status_code, 409)

        resp = self.client.get(f"/api/v1/pagos/indemnizaciones/siniestro/{siniestro}")
        self.assertEqual(len(resp.data), 1)

    @mock.patch.dict("os.environ", {"PAYMENT_GATEWAY_FAIL": "1"})
    def test_indemnizacion_fallida_publica_payment_failed(self, completed, failed):
        resp = self.client.post("/api/v1/pagos/indemnizaciones", {
            "id_siniestro": str(uuid.uuid4()),
            "amount": "1000",
        }, format="json")

        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data["status"], FALLIDO)
        failed.assert_called_once()
        completed.assert_not_called()

    def test_consumir_claim_approved(self, completed, failed):
        from .events import consumir_claim_approved

        siniestro = str(uuid.uuid4())
        consumir_claim_approved(siniestro, "2500000")

        self.assertEqual(ClaimPayout.objects.filter(id_siniestro=siniestro, status=PAGADO).count(), 1)

    def test_health(self, completed, failed):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
