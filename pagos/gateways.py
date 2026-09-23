"""
Adaptadores de pasarela de pago.

Todos implementan la misma interfaz (PaymentGateway), de modo que se puede
sustituir la pasarela simulada por una real (PayU, Wompi, banco, etc.) sin
modificar el resto del microservicio (principio de sustitución de Liskov).
"""
import os
import uuid


class PaymentGateway:
    def cobrar(self, referencia, amount, method):
        """Retorna (exito: bool, transaccion_id: str | None, mensaje: str)."""
        raise NotImplementedError

    def transferir(self, referencia, amount, method):
        """Retorna (exito: bool, transaccion_id: str | None, mensaje: str)."""
        raise NotImplementedError


class SimulatedGateway(PaymentGateway):
    """Pasarela simulada para desarrollo. PAYMENT_GATEWAY_FAIL=1 fuerza fallos."""

    def _procesar(self):
        if os.getenv("PAYMENT_GATEWAY_FAIL") == "1":
            return False, None, "Pago rechazado por la pasarela simulada."
        return True, str(uuid.uuid4()), "Pago aprobado."

    def cobrar(self, referencia, amount, method):
        return self._procesar()

    def transferir(self, referencia, amount, method):
        return self._procesar()


def get_gateway():
    return SimulatedGateway()
